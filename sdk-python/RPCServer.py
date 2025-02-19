#!/usr/bin/python3
# coding=utf8
import os
import sys
sys.path.append('/root/thuei-1/sdk-python/')
import time
import logging
import threading
from werkzeug.wrappers import Request, Response
from werkzeug.serving import run_simple
from jsonrpc import JSONRPCResponseManager, dispatcher
from ArmIK.ArmMoveIK import *
import HiwonderSDK as hwsdk
import HiwonderSDK.Misc as Misc
import HiwonderSDK.Board as Board
import HiwonderSDK.mecanum as mecanum
import Functions.Running as Running
import Functions.lab_adjust as lab_adjust
import Functions.ColorDetect as ColorDete
import Functions.ColorTracking as ColorTrack
import Functions.ColorSorting as ColorSort
import Functions.VisualPatrol as VisualPat
import Functions.Avoidance as Avoidan



if sys.version_info.major == 2:
    print('Please run this program with python3!')
    sys.exit(0)

__RPC_E01 = "E01 - Invalid number of parameter!"
__RPC_E02 = "E02 - Invalid parameter!"
__RPC_E03 = "E03 - Operation failed!"
__RPC_E04 = "E04 - Operation timeout!"
__RPC_E05 = "E05 - Not callable"

HWSONAR = None
QUEUE = None

ColorDete.initMove()
ColorDete.setBuzzer(0.3)

chassis = mecanum.MecanumChassis()

@dispatcher.add_method
def map(x, in_min, in_max, out_min, out_max):
    return (x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min

data = []
@dispatcher.add_method
def SetPWMServo(*args, **kwargs):
    ret = (True, (), 'SetPWMServo')
    print("SetPWMServo:",args)
    arglen = len(args)
    try:
        servos = args[2:arglen:2]
        pulses = args[3:arglen:2]
        use_times = args[0]
        servos_num =  args[1]
        data.insert(0, use_times)
        data.insert(1, servos_num)
        
        dat = zip(servos, pulses)
        for (s, p) in dat:
            pulses = int(map(p,90,-90,500,2500))
            data.append(s)
            data.append(pulses)
            
        Board.setPWMServosPulse(data)
        data.clear()
        
    except Exception as e:
        print('error3:', e)
        ret = (False, __RPC_E03, 'SetPWMServo')
    return ret

@dispatcher.add_method
def SetMovementAngle(angle):
    print(angle)
    try:
        if angle == -1:
            chassis.set_velocity(0,0,0)
            
        else:
            chassis.set_velocity(70,angle,0)
       
    except:
        ret = (False, __RPC_E03, 'SetMovementAngle')
        return ret

# 电机控制
@dispatcher.add_method
def SetBrushMotor(*args, **kwargs):
    ret = (True, (), 'SetBrushMotor')
    arglen = len(args)
    print(args)
    if 0 != (arglen % 2):
        return (False, __RPC_E01, 'SetBrushMotor')
    try:
        motors = args[0:arglen:2]
        speeds = args[1:arglen:2]
        
        for m in motors:
            if m < 1 or m > 4:
                return (False, __RPC_E02, 'SetBrushMotor')
            
        dat = zip(motors, speeds)
        for m, s in dat:
            Board.setMotor(m, s)
            
    except:
        ret = (False, __RPC_E03, 'SetBrushMotor')
    return ret

# 获取超声波测距
@dispatcher.add_method
def GetSonarDistance():
    global HWSONAR
    ret = (True, 0, 'GetSonarDistance')
    try:
        ret = (True, HWSONAR.getDistance(), 'GetSonarDistance')
    except:
        ret = (False, __RPC_E03, 'GetSonarDistance')
    return ret

# 获取当前电池电压
@dispatcher.add_method
def GetBatteryVoltage():
    ret = (True, 0, 'GetBatteryVoltage')
    try:
        ret = (True, Board.getBattery(), 'GetBatteryVoltage')
    except Exception as e:
        print(e)
        ret = (False, __RPC_E03, 'GetBatteryVoltage')
    return ret

# 设置超声波rgb灯模式
@dispatcher.add_method
def SetSonarRGBMode(mode = 0):
    global HWSONAR
    
    HWSONAR.setRGBMode(mode)
    return (True, (mode,), 'SetSonarRGBMode')

# 设置超声波rgb灯颜色
@dispatcher.add_method
def SetSonarRGB(index, r, g, b):
    global HWSONAR
    print((r,g,b))
    if index == 0:
        HWSONAR.setPixelColor(0, Board.PixelColor(r, g, b))
        HWSONAR.setPixelColor(1, Board.PixelColor(r, g, b))
    else:
        HWSONAR.setPixelColor(index, (r, g, b))
    return (True, (r, g, b), 'SetSonarRGB')

# 设置超声波闪烁的颜色和周期
@dispatcher.add_method
def SetSonarRGBBreathCycle(index, color, cycle):
    global HWSONAR
    
    HWSONAR.setBreathCycle(index, color, cycle)
    return (True, (index, color, cycle), 'SetSonarRGBBreathCycle')

# 设置超声波开始闪烁
@dispatcher.add_method
def SetSonarRGBStartSymphony():
    global HWSONAR
    
    HWSONAR.startSymphony()    
    return (True, (), 'SetSonarRGBStartSymphony')

# 设置避障速度
@dispatcher.add_method
def SetAvoidanceSpeed(speed=50):
    print(speed)
    return runbymainth(Avoidan.setSpeed, (speed,))

# 设置避障阈值
@dispatcher.add_method
def SetSonarDistanceThreshold(new_threshold=30):
    print(new_threshold)
    return runbymainth(Avoidan.setThreshold, (new_threshold,))

# 获取当前避障阈值
@dispatcher.add_method
def GetSonarDistanceThreshold():
    return runbymainth(Avoidan.getThreshold, ())

def runbymainth(req, pas):
    if callable(req):
        event = threading.Event()
        ret = [event, pas, None]
        QUEUE.put((req, ret))
        count = 0
        while ret[2] is None:
            time.sleep(0.01)
            count += 1
            if count > 200:
                break
        if ret[2] is not None:
            if ret[2][0]:
                return ret[2]
            else:
                return (False, __RPC_E03 + " " + ret[2][1])
        else:
            return (False, __RPC_E04)
    else:
        return (False, __RPC_E05)

@dispatcher.add_method
def SetBusServoPulse(*args, **kwargs):
    ret = (True, (), 'SetBusServoPulse')
    arglen = len(args)
    if (args[1] * 2 + 2) != arglen or arglen < 4:
        return (False, __RPC_E01, 'SetBusServoPulse')
    try:
        servos = args[2:arglen:2]
        pulses = args[3:arglen:2]
        use_times = args[0]
        for s in servos:
           if s < 1 or s > 6:
                return (False, __RPC_E02)
        dat = zip(servos, pulses)
        for (s, p) in dat:
            Board.setBusServoPulse(s, p, use_times)
    except Exception as e:
        print(e)
        ret = (False, __RPC_E03, 'SetBusServoPulse')
    return ret

@dispatcher.add_method
def SetBusServoDeviation(*args):
    ret = (True, (), 'SetBusServoDeviation')
    arglen = len(args)
    if arglen != 2:
        return (False, __RPC_E01, 'SetBusServoDeviation')
    try:
        servo = args[0]
        deviation = args[1]
        Board.setBusServoDeviation(servo, deviation)
    except Exception as e:
        print(e)
        ret = (False, __RPC_E03, 'SetBusServoDeviation')

@dispatcher.add_method
def GetBusServosDeviation(args):
    ret = (True, (), 'GetBusServosDeviation')
    data = []
    if args != "readDeviation":
        return (False, __RPC_E01, 'GetBusServosDeviation')
    try:
        for i in range(1, 7):
            dev = Board.getBusServoDeviation(i)
            if dev is None:
                dev = 999
            data.append(dev)
        ret = (True, data, 'GetBusServosDeviation')
    except Exception as e:
        print(e)
        ret = (False, __RPC_E03, 'GetBusServosDeviation')
    return ret 

@dispatcher.add_method
def SaveBusServosDeviation(args):
    ret = (True, (), 'SaveBusServosDeviation')
    if args != "downloadDeviation":
        return (False, __RPC_E01, 'SaveBusServosDeviation')
    try:
        for i in range(1, 7):
            dev = Board.saveBusServoDeviation(i)
    except Exception as e:
        print(e)
        ret = (False, __RPC_E03, 'SaveBusServosDeviation')
    return ret 

@dispatcher.add_method
def UnloadBusServo(args):
    ret = (True, (), 'UnloadBusServo')
    if args != 'servoPowerDown':
        return (False, __RPC_E01, 'UnloadBusServo')
    try:
        for i in range(1, 7):
            Board.unloadBusServo(i)
    except Exception as e:
        print(e)
        ret = (False, __RPC_E03, 'UnloadBusServo')

@dispatcher.add_method
def GetBusServosPulse(args):
    ret = (True, (), 'GetBusServosPulse')
    data = []
    if args != 'angularReadback':
        return (False, __RPC_E01, 'GetBusServosPulse')
    try:
        for i in range(1, 7):
            pulse = Board.getBusServoPulse(i)
            if pulse is None:
                ret = (False, __RPC_E04, 'GetBusServosPulse')
                return ret
            else:
                data.append(pulse)
        ret = (True, data, 'GetBusServosPulse')
    except Exception as e:
        print(e)
        ret = (False, __RPC_E03, 'GetBusServosPulse')
    return ret 

@dispatcher.add_method
def StopBusServo(args):
    ret = (True, (), 'StopBusServo')
    if args != 'stopAction':
        return (False, __RPC_E01, 'StopBusServo')
    try:     
        AGC.stop_action_group()
    except Exception as e:
        print(e)
        ret = (False, __RPC_E03, 'StopBusServo')

@dispatcher.add_method
def RunAction(args):
    ret = (True, (), 'RunAction')
    if len(args) == 0:
        return (False, __RPC_E01, 'RunAction')
    try:
        threading.Thread(target=AGC.runAction, args=(args, )).start()
    except Exception as e:
        print(e)
        ret = (False, __RPC_E03, 'RunAction')
        
@dispatcher.add_method
def ArmMoveIk(*args):   
    ret = (True, (), 'ArmMoveIk')
    if len(args) != 7:
        return (False, __RPC_E01, 'ArmMoveIk')
    try:
        result = setPitchRangeMoving((args[0], args[1], args[2]), args[3], args[4], args[5], args[6])
        ret = (True, result)
    except Exception as e:
        print(e)
        ret = (False, __RPC_E03, 'ArmMoveIk')
    return ret
        
@dispatcher.add_method
def GetSonarDistance():
    global HWSONAR
    
    ret = (True, 0, 'GetSonarDistance')
    try:
        ret = (True, HWSONAR.getDistance(), 'GetSonarDistance')
    except:
        ret = (False, __RPC_E03, 'GetSonarDistance')
    return ret

@dispatcher.add_method
def GetBatteryVoltage():
    ret = (True, 0, 'GetBatteryVoltage')
    try:
        ret = (True, Board.getBattery(), 'GetBatteryVoltage')
    except Exception as e:
        print(e)
        ret = (False, __RPC_E03, 'GetBatteryVoltage')
    return ret

def runbymainth(req, pas):
    if callable(req):
        event = threading.Event()
        ret = [event, pas, None]
        QUEUE.put((req, ret))
        count = 0
        #ret[2] =  req(pas)
        #print('ret', ret)
        while ret[2] is None:
            time.sleep(0.01)
            count += 1
            if count > 200:
                break
        if ret[2] is not None:
            if ret[2][0]:
                return ret[2]
            else:
                return (False, __RPC_E03 + " " + ret[2][1])
        else:
            return (False, __RPC_E04)
    else:
        return (False, __RPC_E05)


@dispatcher.add_method
def LoadFunc(new_func = 0):
    return runbymainth(Running.loadFunc, (new_func, ))

@dispatcher.add_method
def UnloadFunc():
    return runbymainth(Running.unloadFunc, ())

@dispatcher.add_method
def StartFunc():
    return runbymainth(Running.startFunc, ())

@dispatcher.add_method
def StopFunc():
    return runbymainth(Running.stopFunc, ())

@dispatcher.add_method
def FinishFunc():
    return runbymainth(Running.finishFunc, ())

@dispatcher.add_method
def Heartbeat():
    return runbymainth(Running.doHeartbeat, ())

@dispatcher.add_method
def GetRunningFunc():
    return runbymainth("GetRunningFunc", ())
    return (True, (0,))

@dispatcher.add_method
def ColorTracking(*target_color):
    return runbymainth(ColorTrack.setTargetColor, target_color)

@dispatcher.add_method
def ColorTrackingWheel(new_st = 0):
    print("Wheel",new_st)
    return runbymainth(ColorTrack.setWheel, new_st)

@dispatcher.add_method
def ColorSorting(*target_color):
    print(target_color)
    return runbymainth(ColorSort.setTargetColor, target_color)

@dispatcher.add_method
def VisualPatrol(*target_color):
    print(target_color)
    return runbymainth(VisualPat.setTargetColor, target_color)

@dispatcher.add_method
def ColorDetect(*target_color):
    print(target_color)
    return runbymainth(ColorDete.setTargetColor, target_color)

@dispatcher.add_method
def Avoidance(*target_color):
    print(target_color)
    return runbymainth(Avoidan.setTargetColor, target_color)


# 设置颜色阈值
# 参数：颜色lab
# 例如：[{'red': ((0, 0, 0), (255, 255, 255))}]
@dispatcher.add_method
def SetLABValue(*lab_value):
    #print(lab_value)
    return runbymainth(lab_adjust.setLABValue, lab_value)

# 保存颜色阈值
@dispatcher.add_method
def GetLABValue():
    return (True, lab_adjust.getLABValue()[1], 'GetLABValue')

# 保存颜色阈值
@dispatcher.add_method
def SaveLABValue(color=''):
    return runbymainth(lab_adjust.saveLABValue, (color, ))

@dispatcher.add_method
def HaveLABAdjust():
    return (True, True, 'HaveLABAdjust')

@Request.application
def application(request):
    dispatcher["echo"] = lambda s: s
    dispatcher["add"] = lambda a, b: a + b
#     print(request.data)
    response = JSONRPCResponseManager.handle(request.data, dispatcher)

    return Response(response.json, mimetype='application/json')

def startRPCServer():
    log = logging.getLogger('werkzeug')
    log.setLevel(logging.ERROR)
    run_simple('', 9030, application)

if __name__ == '__main__':
    startRPCServer()
