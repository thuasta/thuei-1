#!/usr/bin/python3
# coding=utf8
import sys
sys.path.append('/root/MasterPi')
import time
import signal
import HiwonderSDK.mecanum as mecanum

if sys.version_info.major == 2:
    print('Please run this program with python3!')
    sys.exit(0)
    
print('''
**********************************************************
*********************功能:小车转向例程**********************
**********************************************************
----------------------------------------------------------
Official website:https://www.hiwonder.com
Online mall:https://hiwonder.tmall.com
----------------------------------------------------------
Tips:
 * 按下Ctrl+C可关闭此次程序运行，若失败请多次尝试！
----------------------------------------------------------
''')

chassis = mecanum.MecanumChassis()

start = True
#关闭前处理
def Stop(signum, frame):
    global start

    start = False
    print('关闭中...')
    chassis.set_velocity(0,0,0)  # 关闭所有电机
    

signal.signal(signal.SIGINT, Stop)

if __name__ == '__main__':
    while start:
        chassis.set_velocity(0,90,0.3)# 顺时针旋转
        time.sleep(3)
        chassis.set_velocity(0,90,-0.3)# 逆时针旋转
        time.sleep(3)
    chassis.set_velocity(0,0,0)  # 关闭所有电机
    print('已关闭')

        
