from datetime import datetime
import json
import pickle
import threading
import time
import pandas as pd
import struct, array, serial
import paho.mqtt.client as mqtt
import time
import socket

from feature import calculate_features, compute_sma




def wait_for_ack(ser):
    ddata = ""
    ack = struct.pack('B', 0xff) 
    while ddata != ack:
        ddata = ser.read(1)
    return



# SETUP SECTION



def setup_sensors(portNumber):
    
    i = 0
    while i < 5:
        try:
            ser = serial.Serial(portNumber, 115200, timeout=10)
            break
        except Exception as e:
            print(f"Errore di connessione alla porta {portNumber}")
            time.sleep(1)
            i += 1
            if i == 5:
                print(f"Impossibile connettersi alla porta {portNumber}. Verifica la porta e il dispositivo.")
                exit(1)

    print(f"Connesso shimmer sulla porta {portNumber}")

    # send the set sensors command 
    ser.write(struct.pack('BBB', 0x08, 0x80, 0x00))    # accel
    wait_for_ack(ser)

    # send the set sampling rate command

    #ser.write(struct.pack('BB', 0x05, 0x64))           #  10.24Hz
    #ser.write(struct.pack('BB', 0x05, 0x14))           #  51.20Hz
    ser.write(struct.pack('BB', 0x05, 0x0A))           # 102.40Hz
    #ser.write(struct.pack('BB', 0x05, 0x04))           # 256.00Hz
    wait_for_ack(ser)

    return ser


def sync_sensors():

    global ser1, ser2
    

    ser1.write(struct.pack('B', 0x07))
    wait_for_ack(ser1)

    ser2.write(struct.pack('B', 0x07))
    wait_for_ack(ser2)


    readData(ser1, 1)
    readData(ser2, 1)

    ser1.reset_input_buffer()
    ser2.reset_input_buffer()



def finalize_sensor(ser):
    # send stop streaming command
    ser.write(struct.pack('B', 0x20))
    wait_for_ack(ser)
    # close the serial port
    ser.close()
    print(f"Finalized sensor on port {ser.port}")



#READING SECTION



def readData(ser, n_reads):
    # read incoming data   
    ddata = b""
    numbytes = 0
    framesize = 9  #i.e. Packet type (1), TimeStamp (2), 3xAccel (3x2), tra parentesi il numero di byte
    readings = 0
    while readings < n_reads:

        while numbytes < framesize:
            ddata += ser.read(framesize)
            if not ddata:
                print("Timeout seriale raggiunto. Chiusura programma.")
                ser.close()
                exit(1)
            numbytes = len(ddata)
                
        data = ddata[0:framesize]
        ddata = ddata[framesize:] #svuota il buffer
        numbytes = len(ddata)

        readings += 1
        
    #packettype = struct.unpack('B', data[0:1])
    return struct.unpack('HHHH', data[1:framesize]) #timestamp, accelx, accely, accelz


def readers_function(ser):

    global windows,lock,N_iterations, window_size

    global reader1_data,window1,n_samples1
    
    global reader2_data,window2,n_samples2
        
    while True:
        
        (timestamp, accelx, accely, accelz) = readData(ser, 1)
        
        if threading.current_thread().name == "Reader-1":
            reader1_data.append((timestamp, accelx, accely, accelz))
            n_samples1 += 1
            if n_samples1 == window_size:
                
                lock.acquire()

                windows[window1][0] = reader1_data.copy()
                manageWindow()

                lock.release()

                count1 = max(1, len(reader1_data) // 5)
                reader1_data[:] = reader1_data[-count1:]
                n_samples1 = len(reader1_data)

                window1 += 1
                if window1 == N_iterations:
                    break
        

        elif threading.current_thread().name == "Reader-2":
            reader2_data.append((timestamp, accelx, accely, accelz))
            n_samples2 += 1
            if n_samples2 == window_size:
                
                lock.acquire()

                windows[window2][1] = reader2_data.copy()
                manageWindow()
                

                lock.release()

                count2 = max(1, len(reader2_data) // 5)
                reader2_data[:] = reader2_data[-count2:]
                n_samples2 = len(reader2_data)

                window2 += 1
                if window2 == N_iterations:
                    break
       

def manageWindow():

    global windows,semaphore

    global window1
    global window2


    if threading.current_thread().name == "Reader-1":
        if windows[window1][1] == []:
            windows.append([[], []])
        else:
            semaphore.release()
             

    elif threading.current_thread().name == "Reader-2":
        if windows[window2][0] == []:
            windows.append([[], []])
            
        else:
            semaphore.release()



#PROCESSING SECTION


def create_csv_row(stats, window_index, activity_label):
            
    row = [str(window_index)]
    for attr in ["AccelX_T1", "AccelY_T1", "AccelZ_T1"]:
        for stat_value in stats[attr].values():
            row.append(str(stat_value))
    for attr in ["AccelX_T2", "AccelY_T2", "AccelZ_T2"]:
        for stat_value in stats[attr].values():
            row.append(str(stat_value))

    row.append(str(stats["AccelT1_SMA"]))
    row.append(str(stats["AccelT2_SMA"]))

    if activity_label is not None:
        row.append(activity_label)
    
    return row


def write_to_csv(row,stats):
            
    with open(f"./stats_iteration.csv", "a") as file:

    # Scrivi header solo se il file è vuoto
        if file.tell() == 0:
            headers = ["Iterazione"]
            for attr in ["AccelX_T1", "AccelY_T1", "AccelZ_T1"]:
                for stat_name in stats[attr].keys():
                    headers.append(f"{attr}_{stat_name}")
            for attr in ["AccelX_T2", "AccelY_T2", "AccelZ_T2"]:
                for stat_name in stats[attr].keys():
                    headers.append(f"{attr}_{stat_name}")
            
            headers.append("AccelT1_SMA")
            headers.append("AccelT2_SMA")
            headers.append("Label")
            file.write(",".join(headers) + "\n")

        file.write(",".join(row) + "\n")


def format_row(row):

    global scaler

    float_row = [float(i) for i in row[1:]]

    scaled_activity = scaler.transform([float_row])

    return scaled_activity

def predict(formatted_row):

    global loaded_model, label_encoder

    encoded_pred = loaded_model.predict(formatted_row)
    label_pred = label_encoder.inverse_transform(encoded_pred)
    
    return label_pred[0]



def processData():

    global current_window, windows, current_activity,N_iterations,semaphore

    while current_window < N_iterations:
        
        semaphore.acquire()

        print("Processing data...")
        #Questo nel caso in cui è presente un thread di processamento
        # Se il thread di processamento è superfluo, questa riga può essere rimossa

        timestamps, accelxT1, accelyT1, accelzT1 = organizeData(windows[current_window][0])
        timestamps, accelxT2, accelyT2, accelzT2 = organizeData(windows[current_window][1])

        # Dizionari per memorizzare le statistiche per ogni attributo e thread
        stats = {
            "AccelX_T1": {},
            "AccelY_T1": {},
            "AccelZ_T1": {},
            "AccelT1_SMA": {},

            "AccelX_T2": {},
            "AccelY_T2": {},
            "AccelZ_T2": {},
            "AccelT2_SMA": {}
        }
        
        stats["AccelX_T1"] = calculate_features(accelxT1)
        stats["AccelY_T1"] = calculate_features(accelyT1)
        stats["AccelZ_T1"] = calculate_features(accelzT1)

        stats["AccelX_T2"] = calculate_features(accelxT2)
        stats["AccelY_T2"] = calculate_features(accelyT2)
        stats["AccelZ_T2"] = calculate_features(accelzT2)

        stats["AccelT1_SMA"] = compute_sma(accelxT1, accelyT1, accelzT1)
        stats["AccelT2_SMA"] = compute_sma(accelxT2, accelyT2, accelzT2)

        # Scrivi le statistiche nel file CSV
        # da aggiungere label dell'attività durante la costruzione del dataset
        # e.g. walking, standing, running, etc.


        csv_row = create_csv_row(stats, current_window, current_activity if current_activity is not None else None)

        #DataSet Creation Part
        #write_to_csv(csv_row, stats)

        #Prediction Part

        formatted_row = format_row(csv_row)
        predicted_activity = predict(formatted_row)

        activities_performed.append(predicted_activity)

        analytics = getAnalytics(activities_performed)

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((HOST, PORT1))

            timestamp = datetime.now().isoformat()

            payload = json.dumps({
                "timestamp": timestamp,
                "activity": predicted_activity
            }).encode()

            s.sendall(payload)
            


        message = json.dumps(analytics)

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((HOST, PORT2))
            s.sendall(message.encode('utf-8'))

        print(f"Predicted activity for window {current_window}: {predicted_activity}")
        #client.publish("recognized_activity/topic", predicted_activity)
        
        
        current_window += 1
        
        print(f"Finestra {current_window} processata")

    
def organizeData(data):

    timestamps = [item[0] for item in data]

    accelx = [item[1] for item in data]
    accely = [item[2] for item in data]
    accelz = [item[3] for item in data]

    return timestamps, accelx, accely, accelz

def getAnalytics(data):
    
    cWalking=0
    cRunning=0
    cStanding=0
    cSitting=0

    nElements = len(data)

    for el in data:
        if el == "walking": 
            cWalking+=1
        if el == "running": 
            cRunning+=1
        if el == "standing": 
            cStanding+=1
        if el == "sitting": 
            cSitting+=1

    return {
        "Walking": f"{(cWalking / nElements) * 100:.1f}%",
        "Running": f"{(cRunning / nElements) * 100:.1f}%",
        "Standing": f"{(cStanding / nElements) * 100:.1f}%",
        "Sitting": f"{(cSitting / nElements) * 100:.1f}%"
    }




#INITIALIZE SECTION

# Carica il modello KNN


#try:
    #client = mqtt.Client()
    #client.connect("localhost", 1883, 60)
#except:
    #print("MQTT broker non disponibile. Assicurati che il broker sia in esecuzione.")
    #exit(1) 

#print("MQTT broker connesso.")

with open("data_acquisition\model.pickle", "rb") as f:
    loaded_model = pickle.load(f)
with open("data_acquisition\scaler.pickle", "rb") as f:
    scaler = pickle.load(f)
with open("data_acquisition\label_encoder.pickle", "rb") as f:
    label_encoder = pickle.load(f)

lock = threading.Lock()
semaphore = threading.Semaphore(0)

reader1_data = []
window1 = 0 
n_samples1 = 0

reader2_data = []
window2 = 0
n_samples2 = 0

windows = []
windows.append([[], []])


activities_performed = []

activity_labels = ["walking", "running", "standing", "sitting",None]  # Esempi di etichette di attività
current_activity = activity_labels[4] # Indice dell'attività corrente

current_window = 0
window_size = 150  # least 1 second of data at 102.40Hz
N_iterations = 100  # Numero di finestre da processare

# Inizializza i sensori
port1 = "COM6"  # Prima porta COM
port2 = "COM17"  # Seconda porta COM

HOST = 'localhost'  # Localhost
PORT1 = 5000         
PORT2 = 5100        


ser1 = setup_sensors(port1)
ser2 = setup_sensors(port2)



sync_sensors()


# Crea i thread per i sensori
reader1 = threading.Thread(target=readers_function, args=(ser1,), name="Reader-1")
reader2 = threading.Thread(target=readers_function, args=(ser2,), name="Reader-2")
processThread = threading.Thread(target=processData, args=(), name="Process-Thread")


print("Start...")

# Avvia i thread
reader1.start()
reader2.start()
processThread.start()

reader1.join()
reader2.join()
processThread.join()


finalize_sensor(ser1)
finalize_sensor(ser2)

print("Fine lettura sensori")