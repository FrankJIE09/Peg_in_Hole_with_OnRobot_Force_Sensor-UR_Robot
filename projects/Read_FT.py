# 主要实现的功能是读取某个IP地址对应的传感器的数据，并将其实时显示在一个包含6个子图的大图里面，每个子图展示对应轴向上的力或力矩变化。
# 通过调用FTReading模块中的类，实现传感器的初始化和数据的读取。同时，该程序使用了matplotlib库来绘制实时的力矩变化曲线。
# Created by Jie Yu
import time
import FTReading
import matplotlib.pyplot as plt


def get_ft_chart():
	a = FTReading.FTReading('192.168.1.11')
	a.InitFT()
	FM_num = 6
	t_array = [[0], [0], [0], [0], [0], [0]]
	t = [0, 0]
	t_append = 0
	color = ['b', 'g', 'r', 'c', 'm', 'y']
	text = ["Fx", "Fy", "Fz", "Mx", "My", "Mz"]
	fig, axs = plt.subplots(2, 3, constrained_layout=False, figsize=(20, 20))
	while True:
		tcp_force = a.GetReading(1)
		for i in range(FM_num):
			t_array[i].append(tcp_force[i])
			axs.flat[i].plot(t, t_array[i], color[i], linewidth=1)
			axs.flat[i].set_title(text[i], fontsize=12)
		t_append += 1
		t.append(t_append)
		plt.pause(0.001)
	plt.close()


if __name__ == '__main__':
	get_ft_chart()
