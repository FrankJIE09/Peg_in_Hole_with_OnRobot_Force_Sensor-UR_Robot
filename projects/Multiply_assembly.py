from projects.Assembly import Assembly
import yaml
import math
import time
import random
import numpy as np
import projects.Assembly
from multiprocessing import Process
import xlsxwriter
import threading
import os


def from_yaml_get_data(label):
	file = open('../configs/UR10e.yaml', 'r', encoding='utf-8')
	read = file.read()
	cfg = yaml.load(read, Loader=yaml.FullLoader)
	return cfg[label]


def from_yaml_get_point_xy(label):
	file = open('../configs/UR10e.yaml', 'r', encoding='utf-8')
	read = file.read()
	cfg = yaml.load(read, Loader=yaml.FullLoader)
	point = []
	for i in cfg[label]:
		point.append(i)
	return point


# 设定抓取姿态
def define_rpy():
	rpy = np.array([3.14, 0, 1.57])
	return rpy


class Multiply:
	def __init__(self):
		self.assembly = Assembly()
		self.robot = Assembly.get_robot(self.assembly)
	
	# 主程序
	def loop_Grab(self, worksheet, worksheet_error=xlsxwriter.Workbook('Ft.xlsx').add_worksheet("record")):
		Bearing_Point = from_yaml_get_point_xy('Bearing_Point')
		Bearing_Point_for_record = Bearing_Point
		Shaft_Point = from_yaml_get_point_xy('Shaft_Point')
		Shaft_Point_for_record = Shaft_Point
		for point_shaft in Shaft_Point:
			self.assembly.zero_joint5()
			label_s = 0
			fail_z = self.grab_shaft(point_shaft[0], point_shaft[1])
			for point_bearing in Bearing_Point:
				# 记录装配轴和孔编号
				index_bear = Bearing_Point_for_record.index(point_bearing)
				index_shaft = Shaft_Point_for_record.index(point_shaft)
				worksheet_error.write(self.assembly.col2, 0, str(index_shaft) + '-' + str(index_bear))
				self.assembly.col2 = self.assembly.col2 + 2
				#
				self.assembly.zero_joint5()
				success = self.peg_in_hole(worksheet, worksheet_error, point_bearing[0], point_bearing[1])
				if success == 1:
					print('success')
					label_s = 1
					Bearing_Point.remove(point_bearing)
					self.after_success()
					break
				else:
					print('fail')
					self.robot.control_c.stopL(2)
					pose = self.assembly.getTCPPose_reWrite()
					pose[2] = pose[2] + 0.15
					self.assembly.moveL_Rewrite(pose, velocity, acceleration)
			# self.assembly.prepare()
			if label_s is 0:
				self.fail(fail_z)
		self.assembly.over = 1
	
	# 抓取轴
	def grab_shaft(self, x, y, z=from_yaml_get_data('z')):
		z = z - offsetZ
		self.gripper()
		rpy = define_rpy()
		self.assembly.moveL_Rewrite([x, y, z, rpy[0], rpy[1], rpy[2]], velocity, acceleration, 0)
		self.assembly.moveL_Rewrite([x, y, z - 0.1, rpy[0], rpy[1], rpy[2]], velocity, acceleration, 0)
		self.gripper(0)
		self.assembly.moveL_Rewrite([x, y, z, rpy[0], rpy[1], rpy[2]], velocity, acceleration, 0)
		return z - 0.1
	
	# 装配程序
	def peg_in_hole(self, worksheet, worksheet_error, x, y, z=from_yaml_get_data('z')):
		z = z - offsetZ
		self.assembly.touch(35, x, y, z, worksheet)
		return self.assembly.assembly_rotate(worksheet, worksheet_error)
	
	def judge_success(self, z=from_yaml_get_data('z_assembly')):
		z = z - offsetZ
		pose = self.assembly.getTCPPose_reWrite()
		if pose[2] < z:
			return True
		else:
			return False
	
	def gripper(self, open_gripper=1):
		if open_gripper is 1:
			open_gripper = 0
		else:
			open_gripper = 1
		self.robot.io_control.setToolDigitalOut(0, open_gripper)
		time.sleep(0.5)
		return
	
	def after_success(self):
		self.gripper(1)
		pose = self.assembly.getTCPPose_reWrite()
		pose[2] = pose[2] + 0.2
		pose[3:6] = projects.Assembly.rot_vec2rpy(pose)
		self.assembly.moveL_Rewrite(pose, velocity, acceleration)
	
	def fail(self, z):
		file = open('../configs/UR10e.yaml', 'r', encoding='utf-8')
		read = file.read()
		cfg = yaml.load(read, Loader=yaml.FullLoader)
		pose = [cfg['fail_areas'][0], cfg['fail_areas'][1], z + 0.1, 2.2, 2.219, 0.00180]
		self.assembly.moveL_Rewrite(pose, velocity, acceleration, 0)
		pose = [cfg['fail_areas'][0], cfg['fail_areas'][1], z, 2.2, 2.219, 0.00180]
		self.assembly.moveL_Rewrite(pose, velocity, acceleration, 0)
		self.gripper(1)
		pose = [cfg['fail_areas'][0], cfg['fail_areas'][1], z + 0.1, 2.2, 2.219, 0.00180]
		self.assembly.moveL_Rewrite(pose, velocity, acceleration, 0)
		return
	
	# FT数据校正
	def zero_ft(self):
		self.assembly.zero_joint5()
		rpy = define_rpy()
		self.assembly.moveL_Rewrite([-0.52, 0.345, 0.2, rpy[0], rpy[1], rpy[2]], velocity, acceleration, 0)
		time.sleep(1)
		self.assembly.zeroFTSensor()
		print(self.robot.read_FT.GetReading(1))


velocity = projects.Assembly.velocity
acceleration = projects.Assembly.acceleration
offsetZ = projects.Assembly.bat_length - 0.325
if __name__ == '__main__':
	print("Input group number:")
	n = input()
	try:
		os.makedirs('./../data/FT_data')
	except BaseException or Exception as e:
		time.sleep(0)
	experiment = Multiply()
	workbook = xlsxwriter.Workbook('./../data/FT_data/FT_data_' + n + '.xlsx')
	worksheet_ = workbook.add_worksheet()
	worksheet_2 = workbook.add_worksheet("record")
	experiment.zero_ft()
	# get_chart = threading.Thread(target=experiment.assembly.get_ft_chart, args=(worksheet_,), daemon=True)
	grab = threading.Thread(target=experiment.loop_Grab, args=(worksheet_, worksheet_2))
	try:
		# get_chart.start()
		grab.start()
	except Exception as e:
		print(e)
		workbook.close()
	# experiment.assembly.get_ft_chart(worksheet_)
	try:
		while grab.is_alive() == 1:
			time.sleep(1)
			continue
	except Exception as e:
		print(e)
		workbook.close()
	workbook.close()
	# get_chart.join(1)
	grab.join(1)
