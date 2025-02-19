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
****************功能:小车前后左右移动例程*********************
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
        chassis.set_velocity(50,90,0)
        time.sleep(1)
        chassis.set_velocity(50,0,0)
        time.sleep(1)
        chassis.set_velocity(50,270,0)
        time.sleep(1)
        chassis.set_velocity(50,180,0)
        time.sleep(1)
    chassis.set_velocity(0,0,0)  # 关闭所有电机
    print('已关闭')

        
