from datetime import datetime, timedelta
import socket
from readTelosb import open_serial, readFromSensor
import json
import time

from report import create_report

def sendValues(temp, bright, sock_temp, sock_bright):

    timestamp = datetime.now().isoformat()

    payload_temp = json.dumps({"timestamp": timestamp, "temperature": temp}).encode()
    payload_bright = json.dumps({"timestamp": timestamp, "brightness": bright}).encode()

    sock_temp.sendall(payload_temp)
    sock_bright.sendall(payload_bright)

def tempActuator():
    
    global temperature, idealTemperature, deltaT

    if temperature < idealTemperature - deltaT:
        print("Temperature is too low, activating heating system...")
        

    if temperature > idealTemperature + deltaT:
        print("Temperature is too high, activating cooling system...")
        

def turnOffTempActuator():
    print("Temperature actuator deactivated")

def lightActuator():
    
    global brightness, idealBrightness, deltaB

    if brightness < idealBrightness - deltaB:
        print("Brightness is too low, activating light system...")
        
    
    if brightness > idealBrightness + deltaB:
        print("Brightness is too high, activating dimming system...")
        

def turnOffLightActuator():
    print("Brightness actuator deactivated")


def sendTimeActuation(duration, sock):
    timestamp = datetime.now().isoformat()
    
    payload = json.dumps({
        "timestamp": timestamp,
        "duration": duration.total_seconds()
    }).encode()

    sock.sendall(payload)


port = "COM5"
serialPort = open_serial(port)


#Socket connections to Node-RED to send timestamp-temperature and timestamp-brightness values


#Socket for temperature
sock_temp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock_temp.connect(("localhost", 6000))

#Socket for luminosity
sock_bright = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock_bright.connect(("localhost", 6100))

#Socket for fan energy consumption
sock_temp_energy = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock_temp_energy.connect(("localhost", 6200))

#Socket for light energy consumption
sock_light_energy = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock_light_energy.connect(("localhost", 6300))

#Socket for trigger lambda
sock_lambda = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock_lambda.connect(("localhost", 6400))



values = readFromSensor(serialPort)

temperature = values["temperature"]
brightness = values["luminosity"]

#I valori ideali sono questi perchè al momento non dispongo di attuatori in grado di cambiare effettivamente le variabili reali

idealTemperature = temperature
idealBrightness = brightness

print("Ideal values: ")
print("Ideal Temperature: ", idealTemperature)
print("Ideal Luminosity: ", idealBrightness)

percentageT = 0.05
percentageB = 0.50

deltaT = idealTemperature * percentageT
deltaB = idealBrightness * percentageB

print("Border values: ")

print("Higher Temperature: ", deltaT+idealTemperature)
print("Lower Temperature: ", idealTemperature-deltaT)

print("Higher Luminosity: ", deltaB+idealBrightness)
print("Lower Luminosity: ", idealBrightness-deltaB)

temperatureActuator = False
brightnessActuator = False

timerTempActuator = 0
timerBrightActuator = 0

# Whenever we deviate by a certain percentage from the current value, we activate the actuators.
# However, the actuators do not actually perform the work, as they are not powerful enough.
# We simply create an anomaly by covering the sensor with a hand; we see that the actuators activate,
# then we wait for the values to return to normal, which we know will happen.
# At that moment, we turn off the actuators.
# If we set a real ideal temperature and brightness, the actuators would never stop,
# because they are not able to reach the ideal values.

i=0

while True :

    if i%10==0:

        report_lines = create_report(timedelta(minutes=1))
        json_report = json.dumps({"report": report_lines}).encode()
        sock_lambda.sendall(json_report)

    values = readFromSensor(serialPort)

    temperature = values["temperature"]
    brightness = values["luminosity"]

    sendValues(temperature, brightness, sock_temp, sock_bright)

    if(temperature > (idealTemperature + deltaT) or temperature < (idealTemperature - deltaT) ):
        #Non dispongo di un riscaldatore
        
        print("Anomaly detected in temperature sensor")

        if not temperatureActuator:
            temperatureActuator = True
            tempActuator()
            
            timerTempActuator = datetime.now()

    else:
        if temperatureActuator:
            temperatureActuator = False
            turnOffTempActuator()

            timerTemp2 = datetime.now() - timerTempActuator
            timerTempActuator = 0

            sendTimeActuation(timerTemp2, sock_temp_energy)

            print("Time of temperature actuation: ", timerTemp2)
            



    if(brightness > (idealBrightness + deltaB) or brightness < (idealBrightness - deltaB) ):
        
        
        print("Anomaly detected in brightness sensor")

        if not brightnessActuator:
            brightnessActuator = True
            lightActuator()
            
            timerBrightActuator = datetime.now()

    else:
        if brightnessActuator:
            brightnessActuator = False
            turnOffLightActuator()

            timerBright2 = datetime.now() - timerBrightActuator
            timerBrightActuator = 0

            sendTimeActuation(timerBright2, sock_light_energy)

            print("Time of bright actuation: ", timerBright2)

    i += 1
        




