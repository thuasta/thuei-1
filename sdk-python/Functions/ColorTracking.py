#!/usr/bin/python3
# coding=utf8
import sys
sys.path.append('/root/MasterPi')
import cv2
import time
import signal
import Camera
import argparse
import threading
import yaml_handle
from ArmIK.Transform import *
from ArmIK.ArmMoveIK import *
import HiwonderSDK.PID as PID
import HiwonderSDK.Misc as Misc
import HiwonderSDK.Board as Board

if sys.version_info.major == 2:
    print('Please run this program with python3!')
    sys.exit(0)

AK = ArmIK()

range_rgb = {
    'red': (0, 0, 255),
    'blue': (255, 0, 0),
    'green': (0, 255, 0),
    'black': (0, 0, 0),
    'white': (255, 255, 255),
}

lab_data = None
def load_config():
    global lab_data, servo_data
    
    lab_data = yaml_handle.get_yaml_data(yaml_handle.lab_file_path)

__target_color = ('red',)
# 设置检测颜色
def setTargetColor(target_color):
    global __target_color

    print("COLOR", target_color)
    __target_color = target_color
    return (True, ())

# 找出面积最大的轮廓
# 参数为要比较的轮廓的列表
def getAreaMaxContour(contours):
    contour_area_temp = 0
    contour_area_max = 0
    areaMaxContour = None
    for c in contours:  # 历遍所有轮廓
        contour_area_temp = math.fabs(cv2.contourArea(c))  # 计算轮廓面积
        if contour_area_temp > contour_area_max:
            contour_area_max = contour_area_temp
            if contour_area_temp > 300:  # 只有在面积大于300时，最大面积的轮廓才是有效的，以过滤干扰
                areaMaxContour = c
    return areaMaxContour, contour_area_max  # 返回最大的轮廓

# 夹持器夹取时闭合的角度
servo1 = 1500

x_dis = 1500
y_dis = 860

x_pid = PID.PID(P=0.28, I=0.03, D=0.03)  # pid初始化
y_pid = PID.PID(P=0.28, I=0.03, D=0.03)

go_pid = PID.PID(P=0.28, I=0.1, D=0.05)
about_pid = PID.PID(P=0.35, I=0.08, D=0.005)

y_speed = 0
x_speed = 0

# 初始位置
def initMove():
    Board.setPWMServoPulse(1, servo1, 800)
    AK.setPitchRangeMoving((0, 8, 18), 0,-90, 90, 1500)

# 设置蜂鸣器
def setBuzzer(timer):
    Board.setBuzzer(0)
    Board.setBuzzer(1)
    time.sleep(timer)
    Board.setBuzzer(0)

# 关闭电机
def MotorStop():
    Board.setMotor(1, 0) 
    Board.setMotor(2, 0)
    Board.setMotor(3, 0)
    Board.setMotor(4, 0)

#设置扩展板的RGB灯颜色使其跟要追踪的颜色一致
def set_rgb(color):
    if color == "red":
        Board.RGB.setPixelColor(0, Board.PixelColor(255, 0, 0))
        Board.RGB.setPixelColor(1, Board.PixelColor(255, 0, 0))
        Board.RGB.show()
    elif color == "green":
        Board.RGB.setPixelColor(0, Board.PixelColor(0, 255, 0))
        Board.RGB.setPixelColor(1, Board.PixelColor(0, 255, 0))
        Board.RGB.show()
    elif color == "blue":
        Board.RGB.setPixelColor(0, Board.PixelColor(0, 0, 255))
        Board.RGB.setPixelColor(1, Board.PixelColor(0, 0, 255))
        Board.RGB.show()
    else:
        Board.RGB.setPixelColor(0, Board.PixelColor(0, 0, 0))
        Board.RGB.setPixelColor(1, Board.PixelColor(0, 0, 0))
        Board.RGB.show()

_stop = False
__isRunning = False
detect_color = 'None'
start_pick_up = False
# 变量重置
def reset():
    global _stop
    global __isRunning
    global detect_color
    global start_pick_up
    global __target_color
    global x_dis,y_dis
    global enableWheel
    
    x_dis = 1500
    y_dis = 860
    x_pid.clear()
    y_pid.clear()
    go_pid.clear()
    about_pid.clear()
    _stop = False
    enableWheel = False
    __target_color = ()
    detect_color = 'None'
    start_pick_up = False

# app初始化调用
def init():
    print("ColorTracking Init")
    load_config()
    reset()
    initMove()

# app开始玩法调用
def start():
    global __isRunning
    reset()
    __isRunning = True
    print("ColorTracking Start")

# app停止玩法调用
def stop():
    global _stop 
    global __isRunning
    _stop = True
    reset()
    initMove()
    MotorStop()
    __isRunning = False
    set_rgb('None')
    print("ColorTracking Stop")

# app退出玩法调用
def exit():
    global _stop
    global __isRunning
    _stop = True
    reset()
    initMove()
    MotorStop()
    __isRunning = False
    set_rgb('None')
    print("ColorTracking Exit")

# 设置车身跟随函数
enableWheel = False
def setWheel(Wheel = 0,):
    global enableWheel
    if Wheel :
        enableWheel = True
        Board.setPWMServoPulse(1, 1500, 800)
        AK.setPitchRangeMoving((0, 7, 12), -50, -90, 0, 1500)
    else:
        enableWheel = False
        MotorStop()
        initMove()
    return (True, ())

rect = None
size = (640, 480)

def run(img):
    global rect
    global __isRunning
    global enableWheel
    global detect_color
    global start_pick_up
    global img_h, img_w
    global x_dis, y_dis
    global x_speed,y_speed
    
    
    img_copy = img.copy()
    img_h, img_w = img.shape[:2]
    
    if not __isRunning:   # 检测是否开启玩法，没有开启则返回原图像
        return img
     
    frame_resize = cv2.resize(img_copy, size, interpolation=cv2.INTER_NEAREST)
    frame_gb = cv2.GaussianBlur(frame_resize, (3, 3), 3)   
    frame_lab = cv2.cvtColor(frame_gb, cv2.COLOR_BGR2LAB)  # 将图像转换到LAB空间
    
    Motor_ = True
    area_max = 0
    areaMaxContour = 0
    if not start_pick_up:
        for i in lab_data:
            if i in __target_color:
                detect_color = i
                frame_mask = cv2.inRange(frame_lab,
                                             (lab_data[detect_color]['min'][0],
                                              lab_data[detect_color]['min'][1],
                                              lab_data[detect_color]['min'][2]),
                                             (lab_data[detect_color]['max'][0],
                                              lab_data[detect_color]['max'][1],
                                              lab_data[detect_color]['max'][2]))  #对原图像和掩模进行位运算 
                opened = cv2.morphologyEx(frame_mask, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))  # 开运算
                closed = cv2.morphologyEx(opened, cv2.MORPH_CLOSE, np.ones((3, 3), np.uint8))  # 闭运算
                contours = cv2.findContours(closed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)[-2]  # 找出轮廓
                areaMaxContour, area_max = getAreaMaxContour(contours)  # 找出最大轮廓
        if area_max > 1000:  # 有找到最大面积
            (center_x, center_y), radius = cv2.minEnclosingCircle(areaMaxContour)  # 获取最小外接圆
            center_x = int(Misc.map(center_x, 0, size[0], 0, img_w))
            center_y = int(Misc.map(center_y, 0, size[1], 0, img_h))
            radius = int(Misc.map(radius, 0, size[0], 0, img_w))
            if radius > 100:
                return img
            
            rect = cv2.minAreaRect(areaMaxContour)
            box = np.int0(cv2.boxPoints(rect))
            cv2.circle(img, (int(center_x), int(center_y)), int(radius), range_rgb[detect_color], 2)
            
            if __isRunning:   # 检测是否开启玩法
                
                if enableWheel == True:   #  检测是否开启车身跟随;   enableWheel = True,为开启车身跟随
                    Motor_ = True
                    
                    if abs(center_x - img_w/2.0) < 15: # 移动幅度比较小，则不需要动
                        about_pid.SetPoint = center_x
                    else:
                        about_pid.SetPoint = img_w/2.0 # 设定
                    about_pid.update(center_x) # 当前
                    x_speed = -int(about_pid.output)  # 获取PID输出值
                    x_speed = -100 if x_speed < -100 else x_speed
                    x_speed = 100 if x_speed > 100 else x_speed
                    
                    if abs(center_y - img_h/2.0) < 10: # 移动幅度比较小，则不需要动
                        go_pid.SetPoint = center_y
                    else:
                        go_pid.SetPoint = img_h/2.0  
                    go_pid.update(center_y)
                    y_speed = int(go_pid.output)# 获取PID输出值
                    y_speed = -100 if y_speed < -100 else y_speed
                    y_speed = 100 if y_speed > 100 else y_speed
                    
                    speed_1 = int(y_speed + x_speed) # 速度合成
                    speed_2 = int(y_speed - x_speed)
                    speed_3 = int(y_speed - x_speed) 
                    speed_4 = int(y_speed + x_speed)

                    
                    Board.setMotor(1, speed_1)
                    Board.setMotor(2, speed_2)
                    Board.setMotor(3, speed_3)
                    Board.setMotor(4, speed_4)
                                       
                else:
                    if Motor_:
                        MotorStop()
                        Motor_ = False
                        
                    x_pid.SetPoint = img_w / 2.0  # 设定
                    x_pid.update(center_x)  # 当前
                    dx = x_pid.output
                    x_dis += int(dx)  # 输出
                    x_dis = 500 if x_dis < 500 else x_dis
                    x_dis = 2500 if x_dis > 2500 else x_dis
                    
                    y_pid.SetPoint = img_h / 2.0  # 设定
                    y_pid.update(center_y)  # 当前
                    dy = y_pid.output
                    y_dis += int(dy)  # 输出
                    y_dis = 500 if y_dis < 500 else y_dis
                    y_dis = 2500 if y_dis > 2500 else y_dis
                                     
                    Board.setPWMServosPulse([20, 2, 3,int(y_dis), 6,int(x_dis)])
        else:
            if Motor_:
                MotorStop()
                Motor_ = False
    return img

def parse_opt():
    parser = argparse.ArgumentParser()
    parser.add_argument('--Wheel', type=int, default=0, help='0 or 1')
    opt = parser.parse_args()
    return opt

#关闭前处理
def Stop(signum, frame):
    global __isRunning
    
    __isRunning = False
    print('关闭中...')
    MotorStop()  # 关闭所有电机

if __name__ == '__main__':
    opt = parse_opt()
    init()
    start()
    setWheel(**vars(opt))
    __isRunning = True
    __target_color = ('red')
    signal.signal(signal.SIGINT, Stop)
    cap = cv2.VideoCapture('http://127.0.0.1:8080?action=stream')
    while __isRunning:
        ret,img = cap.read()
        if ret:
            frame = img.copy()
            Frame = run(frame)  
            frame_resize = cv2.resize(Frame, (320, 240))
            cv2.imshow('frame', frame_resize)
            key = cv2.waitKey(1)
            if key == 27:
                break
        else:
            time.sleep(0.01)
    cv2.destroyAllWindows()
