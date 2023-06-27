# 读取Excel数据和绘制力传感器数据图像的函数。
# 其中，“read”函数的主要目的是从Excel文件中提取力传感器数据并绘制图像；
# “array”函数的主要目的是将多个Excel文件中的数据合并到单个xlsx文件中；
# “deal_data”函数的目的是处理数据并输出图像和数组。
# Created by Jie Yu
import time

import xlrd
import matplotlib.pyplot as plt
import numpy as np
import os

import xlsxwriter


def read(file, which='', combine=0):
    excel = xlrd.open_workbook(file)
    sheet = excel.sheet_by_index(0)
    step1_start = []
    step1_over = []
    step2_start = []
    step2_over = []
    for row in range(sheet.nrows):
        if sheet.cell_type(row, 0) is 1:
            label = sheet.cell(row, 0).value
            if label == 'step1:touch':
                step1_start.append(row)
            elif label == 'step1 over':
                step1_over.append(row)
            elif label == 'step2:assembly':
                step2_start.append(row)
            elif label == 'step2 over':
                step2_over.append(row)
    success_judge = []
    for row_start in step2_over:
        row = row_start + 1
        while sheet.cell_type(row, 0) is not 1:
            row = row + 1
        success_judge.append(sheet.cell(row, 0).value)

    text = ["Fx", "Fy", "Fz", "Mx", "My", "Mz"]
    color = ['b', 'g', 'r', 'c', 'm', 'y']
    group = -1
    for row_start in step1_start:
        group = group + 1
        row_over = step1_over[step1_start.index(row_start)]
        for col in range(6):
            data = []
            data_index = []
            for i in range(row_start + 2, row_over - 1):
                data.append(sheet.cell(i, col * 2).value)
                data_index.append(sheet.cell(i, 6 * 2).value)
            plt.title(text[col])
            plt.xlabel("time")
            plt.ylabel(text[col])
            plt.plot(data_index, data, color[col], linestyle="-", linewidth=2)
            plt.savefig(
                "./../data/force/force_touch_" + which + "/" + str(group) + "touch_data" + text[col] + which + "_" +
                success_judge[group] + ".jpg")
            if combine != 1:
                plt.close()
    plt.close()
    group = -1
    for row_start in step2_start:
        group = group + 1
        row_over = step2_over[step2_start.index(row_start)]
        for col in range(6):
            data = []
            data_index = []
            for i in range(row_start + 2, row_over - 1):
                data.append(sheet.cell(i, col * 2).value)
                data_index.append(sheet.cell(i, 6 * 2).value)
            plt.title(text[col])
            plt.xlabel("time")
            plt.ylabel(text[col])
            plt.plot(data_index, data, color[col], linestyle="-", linewidth=2)
            plt.savefig(
                "./../data/force/force_assembly_" + which + "/" + str(
                    group) + "assembly_data" + text[col] + which + "_" + success_judge[group] + ".jpg")
            if combine != 1:
                plt.close()


def array():
    data_name = ['x_', 'y_', 'cal_x', 'cal_y', 'rel_x', 'rel_y']
    workbook = xlsxwriter.Workbook('./../data/FT_data/' + 'data_array' + '.xlsx')
    worksheet_ = workbook.add_worksheet()
    for j in range(6):
        array_row = 0
        worksheet_.write(array_row, j, data_name[j])
        array_row = array_row + 1
        for i in range(10):
            file = './../data/FT_data/FT_data_e' + str(i) + '.xlsx'
            excel = xlrd.open_workbook(file)
            sheet = excel.sheet_by_index(1)
            row = 3
            record = sheet.cell(row, j * 2).value
            worksheet_.write(array_row, j, record)
            array_row = array_row + 1
    workbook.close()


def deal_data():
    data = [0]
    for i in data:
        try:
            os.makedirs('./../data/force/force_touch_' + str(i))
        except BaseException or Exception as e:
            time.sleep(0)
        try:
            os.makedirs('./../data/force/force_assembly_' + str(i))
        except BaseException or Exception as e:
            time.sleep(0)
        read('./../data/FT_data/FT_data_e' + str(i) + '.xlsx', str(i), combine=0)


if __name__ == '__main__':
    deal_data()
