#!/usr/bin/env python3
# encoding: utf-8
import os
import sys
import time
import threading
import sqlite3 as sql
sys.path.append('/root/MasterPi')
import yaml_handle
import HiwonderSDK.Board as Board

runningAction = False
stopRunning = False

def stop_action_group():
    global stopRunning
    
    stopRunning = True

def runAction(actNum):
    '''
    运行动作组，无法发送stop停止信号
    :param actNum: 动作组名字 ， 字符串类型
    :param times:  运行次数
    :return:
    '''
    global runningAction
    global stopRunning
    global online_action_times
    if actNum is None:
        return
    actNum = "/root/MasterPiActionGroups/" + actNum + ".d6a"
    stopRunning = False
    if os.path.exists(actNum) is True:
        if runningAction is False:
            runningAction = True
            ag = sql.connect(actNum)
            cu = ag.cursor()
            cu.execute("select * from ActionGroup")
            deviation_data = yaml_handle.get_yaml_data(yaml_handle.Deviation_file_path)
            while True:
                act = cu.fetchone()
                if stopRunning is True:
                    stopRunning = False                   
                    break
                if act is not None:
                    Board.setPWMServosPulse([ act[1], 5, 1,act[2] + deviation_data['1'],
                                                         3,act[3] + deviation_data['3'],
                                                         4,act[4] + deviation_data['4'],
                                                         5,act[5] + deviation_data['5'],
                                                         6,act[6] + deviation_data['6']])
                    if stopRunning is True:
                        stopRunning = False                   
                        break
                    time.sleep(float(act[1])/1000.0)
                else:   # 运行完才退出
                    break
            runningAction = False
            
            cu.close()
            ag.close()
    else:
        runningAction = False
        print("未能找到动作组文件")
