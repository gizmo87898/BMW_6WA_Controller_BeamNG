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


id_counter = 0

counter_8bit = 0
counter_4bit_100ms = 0
counter_4bit_eps = 0
counter_4bit_10ms = 0
abs_counter = 0

rpm = 2000
speed = 33456
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

def crc8_sae_j1850(data, xor, polynomial, init_val):
    crc = init_val

    for byte in data:
        crc ^= byte
        for _ in range(8):
            if crc & 0x80:
                crc = (crc << 1) ^ polynomial
            else:
                crc <<= 1
            crc &= 0xFF

    return crc ^ xor


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
            

            can.Message(arbitration_id=0xc0, data=[ # JBBE alive counter "alive ZGM"
                counter_8bit | 0xF0, 255], is_extended_id=False),
            
            can.Message(arbitration_id=0xd7, data=[ # Airbag "alive counter, safety"
                counter_8bit, 255], is_extended_id=False),
            
            can.Message(arbitration_id=0x12f, data=[ # Ignition "terminals"
                0xfb, counter_8bit, 0x8a, 0x1c, counter_8bit, 0x05, 0x30, 0], is_extended_id=False),
            
            can.Message(arbitration_id=0x1f6, data=[ # Directionals "turn indicators"
                0x01+(left_directional*16)+(right_directional*32),0xf1], is_extended_id=False),
            
            can.Message(arbitration_id=0x21a, data=[ # lights "lamp status"
                (parking_lights*4)+(highbeam*2)+(foglight*32)+(rear_foglight*64), 0, 0xf7], is_extended_id=False),
            
            can.Message(arbitration_id=0x26a, data=[ # self-leveling suspension
                0x02, 0x04, 0x18, 0,0,0,0,0x04], is_extended_id=False),
            
            can.Message(arbitration_id=0x287, data=[ # Road Signs Identification 
                0xff,0xff,0xff,random.randint(0,255),0xff], is_extended_id=False),
            
            can.Message(arbitration_id=0x291, data=[ # MIL, set langage and units
                0x02, 0x04, 0x18, 0,0,0,0,0x04], is_extended_id=False),
            
            can.Message(arbitration_id=0x2a7, data=[ # Power STeering "display, Check Control, driving dynamics" 
                0xa7,counter_4bit_eps+0xf0,0xfe,0xff,0x14], is_extended_id=False),
            
            can.Message(arbitration_id=0x2bb, data=[ # mpg
                0xbb,counter_8bit,counter_8bit,counter_8bit,0], is_extended_id=False),
            
            can.Message(arbitration_id=0x2c4, data=[ # mpg? "status, engine fuel consumption"
                0xc4,counter_4bit_100ms,0,0,0,random.randint(0xa0,0xa9),0,0], is_extended_id=False),
            
            can.Message(arbitration_id=0x30b, data=[ # Auto Start/Stop "status, automatic engine start-stop function"
                0,0,0,4,0,0,0,0], is_extended_id=False),
            
            can.Message(arbitration_id=0x327, data=[ # Lane Departure Assist
                counter_4bit_100ms+0x50, 0x40, 0x46, 0xf1], is_extended_id=False),
            
            can.Message(arbitration_id=0x349, data=[ # Fuel level "raw data, fuel tank level"
                counter_8bit, counter_8bit, counter_8bit, counter_8bit,0], is_extended_id=False),
            
            can.Message(arbitration_id=0x34f, data=[ # Handbrake status "status, handbrake contact"
                0xfd,0xff], is_extended_id=False),
            
            can.Message(arbitration_id=0x368, data=[ # TPMS "tyre status"
                0,0,0,0,0,0,0,0], is_extended_id=False),
            
            can.Message(arbitration_id=0x36a, data=[ # Auto Highbeam "status, high-beam assist"
                0xff,0xff,0xff,0xff,0,0,0,0], is_extended_id=False),
            
            can.Message(arbitration_id=0x36e, data=[ # ABS/TC "display check control bypass"
                random.randint(0,255), (counter_8bit>>4)+240, 0xfe, 0xff,0x14], is_extended_id=False),
            
            can.Message(arbitration_id=0x36f, data=[ # Park light "display, Check Control bypass, EMF"
                random.randint(0,255), (counter_8bit>>4)+240, 0xfe, 0xff,0x14], is_extended_id=False),
            
            can.Message(arbitration_id=0x39e, data=[ # Date and time
                date.hour,date.minute,date.second,date.day,date.year>>8,date.year&0xff,0,0xf2], is_extended_id=False),
            
            can.Message(arbitration_id=0x3a7, data=[ # Drive Mode "configuration, driving dynamics switch"
                0, counter_8bit, 0, counter_8bit, 5,0,0,0], is_extended_id=False),
            
            can.Message(arbitration_id=0x3fd, data=[ # Gear 
                0xff, counter_4bit_100ms, 0x20, 0xfc,0xFF], is_extended_id=False),
            
            can.Message(arbitration_id=0x3f9, data=[ # Oil and coolant temp "status, gear selection" "drivetrain data"
                0x02, 148, counter_8bit, 148, 148, 148, 148, counter_8bit], is_extended_id=False),
            
            can.Message(arbitration_id=0x581, data=[ # Seatbelt
                counter_8bit | 0xF0, 255], is_extended_id=False),
        
            can.Message(arbitration_id=id_counter, data=[
                random.randint(0,255),random.randint(0,255),random.randint(0,255),random.randint(0,255),random.randint(0,255),random.randint(0,255),random.randint(0,255),random.randint(0,255)], is_extended_id=False),
        ]
        
        #Update checksums and counters here
        counter_8bit = (counter_8bit + 1) % 256

        counter_4bit_100ms = (counter_4bit_100ms + 1) % 15
        counter_4bit_eps = (counter_4bit_eps + 4) % 15

        messages_100ms[9].data[0] = crc8_sae_j1850(messages_100ms[9].data, 0xde, 0x1d,0) # MPG 2bb checksum
        messages_100ms[10].data[0] = crc8_sae_j1850(messages_100ms[10].data, 0xc6, 0x1d,0) # MPG 2c4 checksum
        messages_100ms[21].data[0] = crc8_sae_j1850(messages_100ms[21].data[1:], 0xD6, 0x1d,0xff) # Gear Checksum (doesnt wokr)
        messages_100ms[8].data[0] = crc8_sae_j1850(messages_100ms[8].data[1:], 0x9e,0x1d,0xff) # Steering/Driving Dynamics Checksum (doesnt wokr)

        if ((((messages_100ms[2].data[2] >> 4) + 3) << 4) & 0xF0) | 0x03:
            messages_100ms[2].data[4] = 0x00
            
            
        # Send Messages
        for message in messages_100ms:
            bus.send(message)
            #print(message)
            if message.arbitration_id == 0x2a7:
                print(message)
            wpt.sleep(0.001)
        start_time_100ms = time.time()


    # Execute code every 10ms
    elapsed_time_10ms = current_time - start_time_10ms
    if elapsed_time_10ms >= 0.01:  # 10ms
        counter_4bit_10ms = (counter_4bit_10ms + 1) % 15
        #print(counter_4bit_10ms)
        
        rpmval = int(rpm/10.3)
        
        messages_10ms = [
            can.Message(arbitration_id=0xf3, data=[ # RPM
                0xf3, (rpmval&0xf)*16 + counter_4bit_10ms, (rpmval >> 4) & 0xFF, 0xc0, 0xF0, 0x44, 0xFF, 0xFF], is_extended_id=False),    
            can.Message(arbitration_id=0x1a1, data=[ # Speed
                0xa1,0xc0, speed&0xff, speed>>8, 0x81], is_extended_id=False),
        ]
        #do checksums here
        messages_10ms[1].data[0] = crc8_sae_j1850(messages_10ms[1].data, 0x2c, 0x1d,0) # Speed Checksum (dont work)

        messages_10ms[0].data[0] = crc8_sae_j1850(messages_10ms[0].data, 0x2c, 0x1d,0) # RPM Checksum
        
        for message in messages_10ms:
            #if message.arbitration_id == 0xf3:
                #print(message)
            bus.send(message)
            wpt.sleep(0.001)
        start_time_10ms = time.time()

    # Execute code every 5s
    elapsed_time_5s = current_time - start_time_5s
    if elapsed_time_5s >= 5:
        id_counter += 1
        print(hex(id_counter))
        
        rpm = random.randint(0,7500)
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
        #left_directional = not left_directional
        #right_directional = not right_directional
        tc = not tc
        abs = not abs
        battery = not battery
        handbrake = not handbrake
        highbeam = not highbeam
        rear_foglight = not rear_foglight

        start_time_5s = time.time()

sock.close()

