import math
import random
import time
import threading

import numpy as np
import sympy
from scipy.spatial.transform import Rotation as Rt
import xlsxwriter
import matplotlib.pyplot as plt
import yaml

from projects.Control import URControl as UR


# 姿态数据:由UR使用的rot_vec转换为rpy
def rot_vec2rpy(pose):
	r = Rt.from_rotvec(pose[3:6])
	rpy = r.as_euler('xyz', degrees=False)
	return rpy


# 姿态数据:由rpy转换为UR使用的rot_vec
def rpy2rot_vec(rpy):
	r = Rt.from_euler('xyz', rpy)
	rot_vec = r.as_rotvec()
	return rot_vec


# 建立坐标系转换公式
def calculate_rbw(pose, is_rpy=0):
	if is_rpy is 1:
		[C, B, A] = pose[0:3]
	else:
		[C, B, A] = pose[3:6]  # pose[4]->rotate_x pose[5]->rotate_y pose[6]->rotate_z
	
	RzA = np.array([[math.cos(A), -math.sin(A), 0],
	                [math.sin(A), math.cos(A), 0],
	                [0, 0, 1]])
	
	RyB = np.array([[math.cos(B), 0, math.sin(B)],
	                [0, 1, 0],
	                [-math.sin(B), 0, math.cos(B)]])
	
	RxC = np.array([[1, 0, 0],
	                [0, math.cos(C), -math.sin(C)],
	                [0, math.sin(C), math.cos(C)]])
	
	RBW = np.dot(RzA, RyB).dot(RxC)
	return RBW


def pose2alpha(pose):
	pose = rot_vec2rpy(pose)
	theta = math.atan(math.sqrt(math.tan(pose[0]) * math.tan(pose[0]) + math.tan(pose[1]) * math.tan(pose[1])))
	return theta


def deal_force(Fxe, i, ddxe, dxe, xe):
	M = 1
	B = 10
	K = 30
	dt = 0.01
	ddxe.append((Fxe[i + 1] - B * dxe[i] - K * xe[i]) / M)
	dxe.append(dt * (ddxe[i + 1] + ddxe[i]) / 2 + dxe[i])
	xe.append(dt * (dxe[i + 1] + dxe[i]) / 2 + xe[i])
	return ddxe, dxe, xe


class Assembly:
	def __init__(self):
		self.robot = UR().get_robot()
		self.col = 1
		self.col2 = 0
		self.label = ''
		self.plt = plt
		self.over = 0
		self.over_forceMode = 0
		self.R = from_yaml_get_data('R')
		self._r = from_yaml_get_data('r')
	
	def get_robot(self):
		return self.robot
	
	# double function recover no_zero_data
	def zeroFTSensor(self):
		return self.robot.read_FT.InitFT()
	
	# FT数据实时图像
	def get_ft_chart(self, worksheet=xlsxwriter.Workbook('Ft.xlsx').add_worksheet()):
		init_time = time.time()
		FM_num = 6
		t_array = [[0], [0], [0], [0], [0], [0]]
		t = [0, 0]
		t_append = 0
		color = ['b', 'g', 'r', 'c', 'm', 'y']
		text = ["Fx", "Fy", "Fz", "Mx", "My", "Mz"]
		for i in range(len(text)):
			worksheet.write(0, i * 2, text[i])
		self.col = 1
		fig, axs = self.plt.subplots(2, 3, constrained_layout=False, figsize=(20, 20))
		while self.over == 0:
			tcp_force = self.robot.read_FT.GetReading(1)
			for i in range(FM_num):
				t_array[i].append(tcp_force[i])
				axs.flat[i].plot(t, t_array[i], color[i], linewidth=1)
				axs.flat[i].set_title(text[i], fontsize=12)
				worksheet.write(self.col, i * 2, tcp_force[i])
			worksheet.write(self.col, (FM_num + 1) * 2, time.time() - init_time)
			self.col = self.col + 1
			t_append += 1
			t.append(t_append)
			self.plt.pause(0.001)
		self.plt.close()
	
	# 力控模式配置
	def ur_force_mode(self, force_xyz, x=1, y=1):
		[fx, fy, fz] = force_xyz
		task_frame = [0, 0, 0, 0, 0, 0]
		selection_vector = [x, y, 1, 0, 0, 0]
		wrench_up = [fx, fy, fz, 0, 0, 0]
		force_type = 2
		limits = [2, 2, 1.5, 1, 1, 1]
		self.robot.control_c.forceMode(task_frame, selection_vector, wrench_up, force_type, limits)
		return
	
	# 判断是否3点接触
	def judge_touch(self, force_limit=20, rotate=0, judge_z=0.05, judge_Mz=2):
		Force_z = 0
		start_time = time.time()
		time_ = 0
		while Force_z < force_limit and time_ < 500:
			time_ = time.time() - start_time
			Force = self.robot.read_FT.GetReading(1)
			Force_z = math.sqrt(Force[2] * Force[2])
		# print('Force_z = ',Force_z)
		# time.sleep(0.0)
		self.over_forceMode = 1
		return
	
	# 判断是否装配成功
	def judge_assembly(self, force_limit=20, judge_z=0.05):
		success = 0
		start_time = time.time()
		time_ = 0
		z = self.getTCPPose_reWrite()[2]
		fz = self.robot.read_FT.GetReading(1)[2]
		while time_ < 10 and fz < force_limit:
			if abs(z) < judge_z:
				success = 1
				break
			z = self.getTCPPose_reWrite()[2]
			fz = self.robot.read_FT.GetReading(1)[2]
			time_ = time.time() - start_time
		self.over_forceMode = 1
		return success
	
	# 轴孔接触
	def touch(self, degrees, x, y, z, worksheet):
		"""
		:param degrees: 预设轴相对与垂直方向的角度--默认为35°
		:param x: 轴移动到的x坐标--在'configs/UR10e.yaml'Shaft_Point内配置
		:param y: 预设的轴斜上方x坐标--在'configs/UR10e.yaml'Shaft_Point内配置
		:param z: z方向坐标
		:param worksheet:记录文档
		:return:
		"""
		alpha = math.radians(degrees)
		rpy = np.array([3.14 - alpha, 0, 0])
		trans_R = calculate_rbw(rpy, 1)
		move_point = np.array([x, y, z])  # degrees = 5
		self.moveL_Rewrite(
			[move_point[0], move_point[1], move_point[2] + 0.1, rpy[0], rpy[1], rpy[2]], velocity,
			acceleration, False)
		self.moveL_Rewrite(
			[move_point[0], move_point[1], move_point[2], rpy[0], rpy[1], rpy[2]], velocity, acceleration,
			False)
		# 设定力控模式
		force_z = 50
		k = 0.3
		force_y = math.tan(alpha) * force_z * k
		force_x = 0
		force_offset = self.robot.read_FT.GetReading(10)
		
		# force compensate
		force_x = force_x - force_offset[0]
		force_y = force_y - force_offset[1]
		force_z = force_z - force_offset[2]
		
		force_xyz = [force_x, force_y, force_z]
		self.record(worksheet, 'step1:touch')
		force_frame = [1, 1, 1, 1, 1, 1]
		forceMode = threading.Thread(target=self.force_mode_thread, args=(force_xyz, force_frame, False, 5))
		try:
			forceMode.start()
		except Exception as e:
			print(e)
		time.sleep(2)
		self.judge_touch(30)
		self.record(worksheet, 'step1 over')
	
	def record(self, worksheet, label):
		worksheet.write(self.col, 0, label)
		self.label = label
		self.col = self.col + 2
	
	# 装配
	def assembly_rotate(self, worksheet, worksheet_error):
		time.sleep(0.5)
		pose = self.getTCPPose_reWrite()
		pose[3:6] = rot_vec2rpy(pose)
		judge_z = pose[2] - 0.01
		pose[2] = pose[2] + 0.04
		self.moveL_Rewrite(pose, velocity, acceleration, False)
		rpy = pose[3:6]
		offset = self.cal_offset(abs(math.pi - abs(rpy[0])))
		rpy[0] = math.pi
		pose[3:6] = rpy
		
		pose[0] = pose[0] + offset[0]
		pose[1] = pose[1] + offset[1]
		
		self.moveL_Rewrite(pose, 0.1, 0.5, False)
		pose_ = pose
		pose_[2] = pose_[2] - 0.02
		self.moveL_Rewrite(pose_, 0.1, 0.5, False)
		
		print("cal_pose = ", pose)
		force_z = 20
		force_x = 0
		force_y = 0
		force_offset = self.robot.read_FT.GetReading(1)
		
		# force compensate
		force_x = force_x - force_offset[0]
		force_y = force_y - force_offset[1]
		force_z = force_z - force_offset[2]
		
		force_xyz = [force_x, force_y, force_z]
		self.record(worksheet, 'step2:assembly')
		force_frame = [0, 0, 1, 0, 0, 1]
		forceMode = threading.Thread(target=self.force_mode_thread, args=(force_xyz, force_frame, True, 1))
		try:
			forceMode.start()
		except Exception as e:
			print(e)  # xiege thread
		success = self.judge_assembly(20, judge_z)
		self.record(worksheet, 'step2 over')
		if success == 1:
			self.record(worksheet, 'success')
		else:
			self.record(worksheet, 'fail')
		time.sleep(0.5)
		real_pose = self.getTCPPose_reWrite()
		# print minus between cal_pose and real_pose
		print("real_pose = ", real_pose)
		print("x_minus = ", (pose[0] - real_pose[0]) * 1000)
		print("y_minus = ", (pose[1] - real_pose[1]) * 1000)
		self.record_error(worksheet_error, pose, real_pose)
		return success
	
	def record_error(self, worksheet, cal_pose, real_pose):
		label = ["x_minus", "y_minus", "cal_x", "cal_y", "real_x", "real_y"]
		for i in range(6):
			worksheet.write(self.col2, i * 2, label[i])
			worksheet.write(self.col2 + 1, i * 2, int((cal_pose[i] - real_pose[i]) * 1000 * 100000) / 100000)
		worksheet.write(self.col2 + 1, 4, int(cal_pose[0] * 1000 * 1000) / 1000)
		worksheet.write(self.col2 + 1, 6, int(cal_pose[1] * 1000 * 1000) / 1000)
		worksheet.write(self.col2 + 1, 8, int(real_pose[0] * 1000 * 1000) / 1000)
		worksheet.write(self.col2 + 1, 10, int(real_pose[1] * 1000 * 1000) / 1000)
		self.col2 = self.col2 + 3
	
	# 计算轴末端中心与孔中心的偏移量
	def cal_offset(self, a):
		offset_x = self.R * sympy.cos(a) - self._r
		offset_y = 0
		offset_z = (self.R * sympy.cos(a) * sympy.cos(a) - 2 * self._r * sympy.cos(a) + self.R) / sympy.sin(a)
		offset = np.array([offset_x, offset_y, offset_z])
		rpy = [math.pi, 0, math.pi / 2]  # rotate z 90 degrees ; rotate x 180 degrees
		RBW = calculate_rbw(rpy, 1)
		offset = RBW.dot(offset.transpose())
		pose = self.getTCPPose_reWrite()
		pose[3:6] = rot_vec2rpy(pose)
		RBW = calculate_rbw(pose)
		offset = RBW.transpose().dot(offset.transpose())
		return offset
	
	# 调整机械臂末端旋转角度预防装配时限位
	def zero_joint5(self):
		Joint = self.robot.receive_r.getTargetQ()
		Joint[5] = -0.8674465911087452
		self.robot.control_c.moveJ(Joint, velocity_J, acceleration_J)
	
	def force_mode_thread(self, force_xyz, force_frame, rotate=False, allowForce=0):
		[Fx, Fy, Fz, Mx, My, Mz] = [[0], [0], [0], [0], [0], [0]]
		array_force = [Fx, Fy, Fz, Mx, My, Mz]
		[ddx, ddy, ddz, ddMx, ddMy, ddMz] = [[0], [0], [0], [0], [0], [0]]
		array_dd = [ddx, ddy, ddz, ddMx, ddMy, ddMz]
		[dx, dy, dz, dMx, dMy, dMz] = [[0], [0], [0], [0], [0], [0]]
		array_d = [dx, dy, dz, dMx, dMy, dMz]
		[xe, ye, ze, Mxe, Mye, Mze] = [[0], [0], [0], [0], [0], [0]]
		array_e = [xe, ye, ze, Mxe, Mye, Mze]
		i = -1
		tcp_force_last = force_xyz
		init_targetZ = self.robot.receive_r.getTargetQ()[5]
		velZ = 0.5
		time_0 = time.time()
		first_time = 1
		while self.over_forceMode == 0:
			i = i + 1
			tcp_force = self.robot.read_FT.GetReading(1)
			for row in range(3):
				tcp_force[row] = tcp_force[row] + force_xyz[row]
				if abs(tcp_force[row] + force_xyz[row]) < abs((force_xyz[row])) and abs(tcp_force[row]) < allowForce:
					tcp_force[row] = tcp_force_last[row]
			tcp_force_last = tcp_force
			for row in range(len(array_force)):
				array_force[row].append(tcp_force[row])
				array_dd[row], array_d[row], array_e[row] = deal_force(array_force[row], i, array_dd[row], array_d[row],
				                                                       array_e[row])
			point = []
			array_e[0][-1] = -array_e[0][-1]
			array_e[3][-1] = -array_e[3][-1]
			for piece in array_e:
				if array_e.index(piece) < 3:
					point.append(-piece[-1] / 80)
				else:
					point.append(-piece[-1] / 5)
			array_e[0][-1] = -array_e[0][-1]
			array_e[3][-1] = -array_e[3][-1]
			if rotate is True:
				point[5] = point[5] + velZ
				if abs(self.robot.receive_r.getTargetQ()[5] - init_targetZ) > 1:
					if first_time == 1:
						velZ = -velZ
						time_0 = time.time()
						first_time = 0
					elif time.time() - time_0 > 5:
						velZ = -velZ
						time_0 = time.time()
			for force_num in range(len(force_frame)):
				if force_frame[force_num] == 0:
					point[force_num] = 0
			self.robot.control_c.speedL(point, acceleration=0.25, time=0)
		self.robot.control_c.speedStop(10)
		self.over_forceMode = 0
	
	def getTCPPose_reWrite(self):
		pose = self.robot.receive_r.getActualTCPPose()
		rpy = rot_vec2rpy(pose)
		R = calculate_rbw(rpy, 1)
		bat_ = np.array([0, 0, -bat_length])
		bat_xyz = bat_.transpose().dot(R.transpose())
		for i in range(len(bat_xyz)):
			pose[i] = pose[i] - bat_xyz[i]
		return pose
	
	def moveL_Rewrite(self, pose_re, velocity_re=0.3, acceleration_re=2.0, asynchronous=False):
		rpy = np.array([pose_re[3], pose_re[4], pose_re[5]])
		R = calculate_rbw(rpy, 1)
		rot_vec = rpy2rot_vec(rpy)
		bat_ = np.array([0, 0, -bat_length])
		bat_xyz = bat_.transpose().dot(R.transpose())
		move_point = np.array([pose_re[0], pose_re[1], pose_re[2]])  # degrees = 5
		move_point_fix = np.array([0, 0, 0], dtype=float)
		for i in range(len(bat_xyz)):
			move_point_fix[i] = move_point[i] + bat_xyz[i]
		self.robot.control_c.moveL(
			[move_point_fix[0], move_point_fix[1], move_point_fix[2], rot_vec[0], rot_vec[1], rot_vec[2]], velocity_re,
			acceleration_re, asynchronous)


def from_yaml_get_data(label):
	file = open('../configs/UR10e.yaml', 'r', encoding='utf-8')
	read = file.read()
	cfg = yaml.load(read, Loader=yaml.FullLoader)
	return cfg[label]


velocity = 0.3
acceleration = 2
velocity_J = 1
acceleration_J = 2
bat_length = 0.322

if __name__ == '__main__':
	self = Assembly()
	print(self.getTCPPose_reWrite())
# self.moveL_rewrite([-0.5670, 0.2, 0.5, 2.2, 2.219, 0.00180])
# force_z = 50
# force_x = 0
# force_y = 0
# self.robot.read_FT.InitFT()
#
# force_offset = self.robot.read_FT.GetReading(10)
#
# # force compensate
# force_x = force_x - force_offset[0]
# force_y = force_y - force_offset[1]
# force_z = force_z - force_offset[2]
#
# force_xyz_ = [force_x, force_y, force_z]
# self.force_mode_thread(force_xyz_, rotate=True)
