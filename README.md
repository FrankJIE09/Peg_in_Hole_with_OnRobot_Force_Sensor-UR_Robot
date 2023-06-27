## **一.简介：**
**项目名称：轴孔力控装配**

**操作系统：Ubuntu18.04**

**编程语言： Python3**

**机械臂平台： UR10e**

**概述：本系统使用UR_RTDE接口控制UR10e，实现了力控轴孔装配。可在50mm的轴孔尺寸下，实现0.1mm以内间隙的装配。**

## **二.配置文件：**

    cd Peg_in_Hole

    pip install -r requirements.txt

## **三.文件描述：**
    │  README.md                                    //help
    │  requirements.txt                             //python环境配置
    ├─configs
    │      UR10e.yaml                               //参数配置 包括轴径，孔径,轴孔坐标等
    ├─data                                          //获取的FT数据
    │  ├─force
    │  │  ├─force_assembly_0                        //装配时期的FT数据图
    │  │  │      
    │  │  └─force_touch_0                           //接触时期的FT数据图
    │  │          0touch_dataFx0_success.jpg
    │  │          0touch_dataFy0_success.jpg
    │  │          0touch_dataFz0_success.jpg
    │  │          0touch_dataMx0_success.jpg
    │  │          0touch_dataMy0_success.jpg
    │  │          0touch_dataMz0_success.jpg
    │  │          
    │  └─FT_data                                    //全部的FT数据及计算与实际误差结果
    │          
    └─projects                                      //code
        │  Assembly.py                              //控制轴孔接触与装配，记录FT数据
        │  Control.py                               //初始化机械臂，与机械臂建立连接
        │  Multiply_assembly.py                     //主程序，记录数据
        └─ read_data.py                             //处理数据

## **四.配置UR示教器：**
    如本目录下的图片：Image_guide1,Image_guide2,Image_guide3，
    测量末端到机械臂末端的距离。将该距离填入图中z值并点上标签。

# Peg_in_Hole_with_OnRobot_Force_Sensor-UR_Robot
