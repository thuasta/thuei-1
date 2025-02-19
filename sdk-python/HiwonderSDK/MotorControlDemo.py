#!/usr/bin/python3
# coding=utf8
import sys
sys.path.append('/root/MasterPi')
import time
import signal
import threading
import HiwonderSDK.Board as Board

if sys.version_info.major == 2:
    print('Please run this program with python3!')
    sys.exit(0)
    
print('''
**********************************************************
********功能:幻尔科技树莓派扩展板，电机控制例程**********
**********************************************************
----------------------------------------------------------
Official website:https://www.hiwonder.com
Online mall:https://hiwonder.tmall.com
----------------------------------------------------------
Tips:
 * 按下Ctrl+C可关闭此次程序运行，若失败请多次尝试！
----------------------------------------------------------
''')

# 关闭所有电机
def MotorStop():
    Board.setMotor(1, 0) 
    Board.setMotor(2, 0)
    Board.setMotor(3, 0)
    Board.setMotor(4, 0)

start = True
#关闭前处理
def Stop(signum, frame):
    global start

    start = False
    print('关闭中...')
    MotorStop()  # 关闭所有电机
    

signal.signal(signal.SIGINT, Stop)

if __name__ == '__main__':
    
    while True:
        Board.setMotor(1, 35)  #设置1号电机速度35
        time.sleep(1)
        Board.setMotor(1, 60)  #设置1号电机速度60
        time.sleep(2)
        Board.setMotor(1, 90)  #设置1号电机速度90
        time.sleep(3)    
        
        if not start:
            MotorStop()  # 关闭所有电机
            print('已关闭')
            break
    
    
        