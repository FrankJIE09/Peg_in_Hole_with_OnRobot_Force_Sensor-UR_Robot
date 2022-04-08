import yaml
import rtde_control
import rtde_io
import rtde_receive
import FTReading


def from_yaml_get_data(label):
	file = open('../configs/UR10e.yaml', 'r', encoding='utf-8')
	read = file.read()
	cfg = yaml.load(read, Loader=yaml.FullLoader)
	
	return cfg[label]
	pass


class URControl:
	def __init__(self):
		IP = from_yaml_get_data('ip')
		FT_IP = from_yaml_get_data('FT_ip')
		self.control_c = rtde_control.RTDEControlInterface(IP)
		self.receive_r = rtde_receive.RTDEReceiveInterface(IP)
		self.io_control = rtde_io.RTDEIOInterface(IP)
		self.read_FT = FTReading.FTReading(FT_IP)
		return
	
	def get_robot(self):
		return self
