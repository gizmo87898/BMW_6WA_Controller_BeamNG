import time
import can
import random
import socket
import struct
import select 
import win_precise_time as wpt
from datetime import datetime

bus = can.interface.Bus(channel='com11', bustype='seeedstudio', bitrate=500000)
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind(('127.0.0.1', 4444))
    
# Track time for each function separately
start_time_100ms = time.time()
start_time_10ms = time.time()
start_time_5s = time.time()

id_counter = 0x360

alive_counter = 0
abs_counter = 0

rpm = 2000
speed = 20
coolant_temp = 120
fuel = 50

left_directional = False
right_directional = False
tc = False
abs = False
battery = False
handbrake = False
highbeam = False
auto_highbeam = False
park_light = False


tpms = False #tbd
cruise_control = False # tbd
cruise_control_speed = 80 # tbd
foglight = False
rear_foglight = False
parking_lights = False 
check_engine = False
hood = False
trunk = False
front_left = 30
front_right = 30
rear_left = 30
rear_right = 30
airbag = False
seatbelt = False

while True:
    current_time = time.time()
    
    #read from the socket if there is data to be read
    ready_to_read, _, _ = select.select([sock], [], [], 0)
    if sock in ready_to_read:
        data, _ = sock.recvfrom(256)
        packet = struct.unpack('I4sH2c7f2I3f16s16si', data)
        
        rpm = int(max(min(packet[6], 8000), 0))
        speed = max(min(int(packet[5]*2.5), 160), 0) #convert speed to km/h
        
        left_directional = False
        right_directional = False
        highbeam = False
        abs = False
        battery = False
        tc = False
        handbrake = False
        
        if (packet[13]>>1)&1:
            highbeam = True
        if (packet[13]>>2)&1:
            handbrake = True
        if (packet[13]>>4)&1:
            tc = True
        if (packet[13]>>10)&1:
            abs = True
        if (packet[13]>>9)&1:
            battery = True
        if (packet[13]>>5)&1:
            left_directional = True
        if (packet[13]>>6)&1:
            right_directional = True
            
    # Send each message every 100ms
    elapsed_time_100ms = current_time - start_time_100ms
    if elapsed_time_100ms >= 0.05:
        date = datetime.now()
        
        messages_100ms = [
            

            can.Message(arbitration_id=0xc0, data=[ # JBBE alive counter (dont know if this is needed but it was on kcan1 so i put it)
                alive_counter | 0xF0, 255], is_extended_id=False),
            
            can.Message(arbitration_id=0xd7, data=[ # Airbag
                alive_counter | 0xF0, 255], is_extended_id=False),
            
            can.Message(arbitration_id=0x12f, data=[ # Ignition
                0xfb, alive_counter, 0x8a, 0x1c, alive_counter, 0x05, 0x30, 0], is_extended_id=False),
            
            can.Message(arbitration_id=0x1f6, data=[ # Directionals
                0x01+(left_directional*16)+(right_directional*32),0xf1], is_extended_id=False),
            
            can.Message(arbitration_id=0x21a, data=[ # lights
                (parking_lights*4)+(highbeam*2)+(foglight*32)+(rear_foglight*64), 0, 0xf7], is_extended_id=False),
            
            can.Message(arbitration_id=0x291, data=[ # MIL, set langage and units
                0x02, 0x04, 0x18, 0,0,0,0,0x04], is_extended_id=False),
            
            can.Message(arbitration_id=0x2a7, data=[ # Power STeering
                6,54,0,0,25], is_extended_id=False),
            
            can.Message(arbitration_id=0x2c4, data=[ # mpg?
                0,0,0,0,0,0,0,0], is_extended_id=False),
            
            can.Message(arbitration_id=0x30b, data=[ # Auto Start/Stop
                0,0,0,4,0,0,0,0], is_extended_id=False),
            
            can.Message(arbitration_id=0x349, data=[ # Fuel level
                0xcc,0xcc,0xcc,0xcc,0xcc,0xcc], is_extended_id=False),
            
            can.Message(arbitration_id=0x34f, data=[ # Handbrake status
                0xfd,0xff], is_extended_id=False),
            
            can.Message(arbitration_id=0x368, data=[ # TPMS
                0,0,0,0,0,0,0,0], is_extended_id=False),
            
            can.Message(arbitration_id=0x36a, data=[ # Auto Highbeam
                0xff,0xff,0xff,0xff,0,0,0,0], is_extended_id=False),
            
            can.Message(arbitration_id=0x36e, data=[ # ABS/TC
                0x00, 0x98, 0x00, 0x80, 0x00, 0xF4, 0xE8, 0x10], is_extended_id=False),
            
            can.Message(arbitration_id=0x36f, data=[ # Park light
                0xff,0xff,0xff,0xff,0,0,0,0], is_extended_id=False),
            
            can.Message(arbitration_id=0x39e, data=[ # Date and time
                date.hour,date.minute,date.second,date.day,date.year>>8,date.year&0xff,0,0xf2], is_extended_id=False),
            
            can.Message(arbitration_id=0x3a7, data=[ # Drive Mode
                0, alive_counter, 0, alive_counter, 5,0,0,0], is_extended_id=False),
            
            can.Message(arbitration_id=0x3f9, data=[ # Oil and coolant temp
                0x02, 148, alive_counter, 148, 148, 148, 148, alive_counter], is_extended_id=False),
            
            can.Message(arbitration_id=0x581, data=[ # Seatbelt
                alive_counter | 0xF0, 255], is_extended_id=False),
        
            can.Message(arbitration_id=id_counter, data=[
                random.randint(0,255),random.randint(0,255),random.randint(0,255),random.randint(0,255),random.randint(0,255),random.randint(0,255),random.randint(0,255),random.randint(0,255)], is_extended_id=False),
        ]
        
        alive_counter = (alive_counter + 1) % 256
        if ((((messages_100ms[2].data[2] >> 4) + 3) << 4) & 0xF0) | 0x03:
            messages_100ms[2].data[4] = 0x00
        for message in messages_100ms:
            bus.send(message)
            #print(message)
            wpt.sleep(0.05)
        start_time_100ms = time.time()


    # Execute code every 10ms
    elapsed_time_10ms = current_time - start_time_10ms
    if elapsed_time_10ms >= 0.01:  # 10ms
        messages_10ms = [
            can.Message(arbitration_id=0xf3, data=[ # RPM
                0xf3, (int(rpm * 1.557) & 0xff), (int(rpm * 1.557) >> 8), 0xc0, 0xF0, 0x44, 0xFF, 0xFF], is_extended_id=False),    
            can.Message(arbitration_id=0x1a1, data=[ # Speed
                0x01,0xf1], is_extended_id=False),
        ]
        
        for message in messages_10ms:
            bus.send(message)
            wpt.sleep(0.002)
        start_time_10ms = time.time()

    # Execute code every 5s
    elapsed_time_5s = current_time - start_time_5s
    if elapsed_time_5s >= 3:
        id_counter += 1
        print(hex(id_counter))
        
        rpm = random.randint(0,8000)
        speed = random.randint(0,160)
        tpms = not tpms
        cruise_control = not cruise_control
        foglight = not foglight
        parking_lights = not parking_lights
    
        check_engine = not check_engine
       
        hood = not hood
        trunk = not trunk
        airbag = not airbag
        seatbelt = not seatbelt
        left_directional = not left_directional
        right_directional = not right_directional
        tc = not tc
        abs = not abs
        battery = not battery
        handbrake = not handbrake
        highbeam = not highbeam
        rear_foglight = not rear_foglight

        start_time_5s = time.time()

sock.close()

