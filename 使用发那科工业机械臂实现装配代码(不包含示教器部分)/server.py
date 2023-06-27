
import math
import socket
import time
import yaml
import numpy as np
import re
import threading
from projects import Read_FT


def calculate_rbw(pose):
    [C, B, A] = pose  # pose[0]->rotate_x pose[1]->rotate_y pose[2]->rotate_z

    RzA = np.array([[math.cos(A), -math.sin(A), 0],
                    [math.sin(A), math.cos(A), 0],
                    [0, 0, 1]])

    RyB = np.array([[math.cos(B), 0, math.sin(B)],
                    [0, 1, 0],
                    [-math.sin(B), 0, math.cos(B)]])

    RxC = np.array([[1, 0, 0],
                    [0, math.cos(C), -math.sin(C)],
                    [0, math.sin(C), math.cos(C)]])

    RBW = np.dot(RzA, RyB).dot(RxC)  # important xyz or zyx
    return RBW


class Server:
    # 建立客户端连接
    def __init__(self):
        self.serverSocket = socket.socket()
        self.serverSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        host = '192.168.1.100'
        # host = '127.0.0.1'
        port = 8888
        self.serverSocket.bind((host, port))
        self.serverSocket.listen(1)
        self.label = 0
        self.ShaftWpr = np.array([])
        self.BearingWpr = np.array([-89.839, -0.041, 178.724])
        for i in range(3):
            self.BearingWpr[i] = math.radians(self.BearingWpr[i])

    def solveMsg(self, msg, clientSocket):
        # if msg == 'qt,0':
        if msg == 'qt,0\r':
            [x, y, z] = self.calculateOffset()
            # y = -60.0
            # z = 40.00
            BearingPose = []
            for i in range(3):
                BearingPose.append(math.degrees(self.BearingWpr[i]))
            [w, p, r_] = BearingPose
            poseDate = ['(', x, ',', y, ',', z, ',', w, ',', p, ',', r_, ')\n']
            poseDateString = ''
            for i in poseDate:
                poseDateString = poseDateString + str(i)
            print("offset_value = ", poseDateString)
            clientSocket.send(poseDateString.encode())
            time.sleep(0.1)
            clientSocket.close()
        elif msg == 'tr,0\r':
            clientSocket.send('1\n'.encode())
            clientSocket.close()
        elif msg == 'cd,0\r':
            clientSocket.send('1\n'.encode())
            clientSocket.close()
        elif msg[0] == '#':
            self.ShaftWpr = np.array([])
            pose = np.array([])
            clientSocket.send('1\n'.encode())
            pattern = re.compile(r'(-*\d*\.\d*)')
            msg = pattern.findall(msg)
            for i in msg:
                pose = np.append(pose, float(i))
            print(pose)
            for i in pose[3:6]:
                self.ShaftWpr = np.append(self.ShaftWpr, math.radians(i))
        else:
            clientSocket.send('1\n'.encode())

    def cal_alpha(self):
        wprFlange2Tool = np.array([math.pi / 2, 0, 0])
        wprFlange2Tool_Shaft = np.array([math.pi / 2 - math.radians(3), 0, 0])

        TransBase2Flange_Shaft = calculate_rbw(self.ShaftWpr)
        TransFlange2Tool = calculate_rbw(wprFlange2Tool)
        TransFlange2Tool_Shaft = calculate_rbw(wprFlange2Tool_Shaft)

        bat = np.array([0, 0, -1])
        bearing = np.array([0, 0, -1])
        bat = np.dot(bat.transpose(), TransFlange2Tool_Shaft.transpose()).dot(TransBase2Flange_Shaft.transpose())
        TransBase2Flange_Bearing = calculate_rbw(self.BearingWpr)
        # bearing = np.dot(bearing.transpose(), TransFlange2Tool.transpose()).dot(TransBase2Flange_Bearing.transpose())
        bearing = np.dot(bearing.transpose(), TransBase2Flange_Bearing.transpose())
        a = 1
        b = 1
        c = 0
        for i in range(3):
            c = c + (bat[i] - bearing[i]) ** 2
        c = math.sqrt(c)
        alpha = math.acos((a ** 2 + b ** 2 - c ** 2) / 2 * a * b)
        print("alpha = ", math.degrees(alpha))
        return alpha

    def calculateOffset(self):
        alpha = self.cal_alpha()
        offsetX = (R * math.cos(alpha) - r) * 1000
        offsetY = 0
        offsetZ = ((R * math.cos(alpha) ** 2 - 2 * r * math.cos(alpha) + R) / math.sin(alpha)) * 1000
        offset = [-offsetY, -offsetX, -offsetZ]
        for i in range(3):
            offset[i] = int(offset[i] * 1000) / 1000
        return offset

    def loopReceiver(self):
        try:
            while True:
                clientSocket, address = self.serverSocket.accept()
                msg = clientSocket.recv(1024).decode()
                if msg:
                    print("ReceiverMsg = ", msg)
                    self.solveMsg(msg, clientSocket)
        except Exception as e:
            print(e)


R = 0.0250
r = 0.0249
if __name__ == '__main__':
    self = Server()
    # Read_FT = threading.Thread(target=Read_FT.get_ft_chart, args=())
    # Read_FT.start()
    self.loopReceiver()