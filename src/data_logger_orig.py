#!/bin/bash
##### Libraries #####
from datetime import datetime
from sense_hat import SenseHat
from time import sleep
from threading import Thread
from statistics import mean

##### Logging Settings #####
FILENAME = ""
WRITE_FREQUENCY = 100
TEMP_P=True
TEMP_H=False
HUMIDITY=True
PRESSURE=True
ORIENTATION=True
ACCELERATION=True
MAG=True
GYRO=True
DELAY=5

##### Functions #####
def file_setup(filename):
    header =[]
    if TEMP_H:
        header.append("temp_h")
    if TEMP_P:
        header.append("temp_p")
    if HUMIDITY:
        header.append("humidity")
    if PRESSURE:
        header.append("pressure")
    if ORIENTATION:
        header.extend(["pitch","roll","yaw"])
    if MAG:
        header.extend(["mag_x","mag_y","mag_z"])
    if ACCELERATION:
        header.extend(["accel_x","accel_y","accel_z"])
    if GYRO:
        header.extend(["gyro_x","gyro_y","gyro_z"])
    header.append("timestamp")

    with open(filename,"w") as f:
        f.write(",".join(str(value) for value in header)+ "\n")

def log_data():
    output_string = ",".join(str(value) for value in sense_data)
    batch_data.append(output_string)
    #print(output_string)


def get_sense_data():
    sense_data=[]

    if TEMP_H:
        sense_data.append(sense.get_temperature_from_humidity())

    if TEMP_P:
        sense_data.append(sense.get_temperature_from_pressure())

    if HUMIDITY:
        sense_data.append(sense.get_humidity())

    if PRESSURE:
        sense_data.append(sense.get_pressure())

    if ORIENTATION:
        o = sense.get_orientation()
        yaw = o["yaw"]
        pitch = o["pitch"]
        roll = o["roll"]
        sense_data.extend([pitch,roll,yaw])

    if MAG:
        mag = sense.get_compass_raw()
        mag_x = mag["x"]
        mag_y = mag["y"]
        mag_z = mag["z"]
        sense_data.extend([mag_x,mag_y,mag_z])

    if ACCELERATION:
        acc = sense.get_accelerometer_raw()
        x = acc["x"]
        y = acc["y"]
        z = acc["z"]
        sense_data.extend([x,y,z])

    if GYRO:
        gyro = sense.get_gyroscope_raw()
        gyro_x = ["x"]
        gyro_y = ["y"]
        gyro_z = ["z"]
        sense_data.extend([gyro_x,gyro_y,gyro_z])

    sense_data.append(datetime.now())

    return sense_data

def timed_log():
    while True:
        log_data()
        sleep(DELAY)

def blink(r,g,b):
    sense.set_pixel(7,7,r,g,b)
    sleep(0.25)
    sense.set_pixel(7,7,0,0,0)
    sleep(0.25)
    sense.set_pixel(7,7,r,g,b)
    sleep(0.25)
    sense.set_pixel(7,7,0,0,0)
    sleep(0.25)

##### Main Program #####
sense = SenseHat()
sense.clear()
sense.low_light = True
sense.show_message("Loading.........")
blink(255,0,0)

batch_data = []
avg_temp = []

timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")

if FILENAME == "":
    filename = "SenseLog-" + timestamp + ".csv"
else:
    filename = FILENAME + "-" + timestamp + ".csv"

file_setup(filename)

if DELAY > 0:
    sense_data = get_sense_data()
    sense.show_message(str(round(sense.get_temperature_from_humidity(),1)))
    Thread(target= timed_log).start()

while True:
    sense_data = get_sense_data()

    if DELAY == 0:
        log_data()

    if len(batch_data) >= WRITE_FREQUENCY:
        #print("Writing to file..")
        blink(0,255,0)
        temp_data = []
        for i in range(0,len(batch_data)):
            temp_data.append(float(batch_data[i].split(",")[0]))

        #print("Temp_data:")
        #print(temp_data)
        #print("Mean Temp:")
        #print(mean(temp_data))
        sense.show_message(str(round(mean(temp_data),2)))
        if len(avg_temp) > 64:
            avg_temp = []
            sense.clear()
            
        avg_temp.append(mean(temp_data))
        #print("Avg data:")
        #print(avg_temp)
        #print("length avg_data:" + str(len(avg_temp)))

        choices = {
		10: (0, 200, 180),
 		11: (0, 210, 150),
 		12: (0, 220, 120),
 		13: (20, 222, 80),
 		14: (40, 225, 40),
 		15: (75, 222, 20),
 		16: (110, 220, 0),
 		17: (185, 200, 0),
 		18: (255, 180, 0),
 		19: (255, 150, 0),
 		20: (255, 120, 0),
 		21: (255, 100, 0),
 		22: (255, 80, 0),
 		23: (255, 62, 0),
 		24: (255, 45, 0),
 		25: (248, 35, 0),
 		26: (240, 25, 0),
 		27: (225, 17, 0),
 		28: (210, 10, 0),
 		29: (190, 5, 0),
 		30: (170, 0, 0)
	}

        ##Output avg_data on sense hat
        for t in range(0,len(avg_temp)):
            tData = avg_temp[t]
            intVal = int(tData)
            r,g,b = choices.get(intVal, (0,255,183))
            if (t >=0 and t <=7):
                #print(0,t,r,g,b)
                sense.set_pixel(0,t,r,g,b)
            elif (t>7 and t <=15):
                t = t -8
                #print(1,t,r,g,b)
                sense.set_pixel(1,t,r,g,b)
            elif (t>15 and t <=23):
                t = t -16
                #print(2,t,r,g,b)
                sense.set_pixel(2,t,r,g,b)
            elif (t>23 and t <=31):
                t = t -24
                #print(3,t,r,g,b)
                sense.set_pixel(3,t,r,g,b)
            elif (t>31 and t <=39):
                t =t -32
                #print(4,t,r,g,b)
                sense.set_pixel(4,t,r,g,b)
            elif (t>39 and t <=47):
                t =t - 40
                #print(5,t)
                sense.set_pixel(5,t,r,g,b)
            elif (t>47 and t <56):
                t =t -48
                #print(6,t,r,g,b)
                sense.set_pixel(6,t,r,g,b)
            elif (t>56 and t <=64):
                t =t - 57
                #print(7,t,r,g,b)
                sense.set_pixel(7,t,r,g,b)
               
        with open(filename,"a") as f:
            for line in batch_data:
                f.write(line + "\n")
            batch_data = []
