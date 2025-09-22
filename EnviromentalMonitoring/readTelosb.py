import serial
import re
from datetime import datetime

pattern = re.compile(
    r"Temp:\s*(\d+)\s+Lum:\s*(\d+)"
)

def open_serial(port):
    try:
        ser = serial.Serial(port, 115200, timeout=1)
        print("Seriale connesso. In attesa di dati... per interrompere la connesione premere Ctrl+c")
        return ser
    except Exception as e:
        print(f"Errore apertura seriale: {e}")
        return None    
    

def parse_line(line):
    
    match = pattern.search(line)
    if match:
        try:

            temperature = int(match.group(1))
            luminosity = int(match.group(2))
    
            payloadPyt = {
                        "timestamp": datetime.now(),
                        "temperature": temperature,
                        "luminosity": luminosity
                    }
            
            return payloadPyt

        except Exception as e:
            print(f"Errore nel parsing: {e}")
     


def readFromSensor(serial):
    try:
        line = serial.readline().decode('utf-8', errors='ignore').strip()
        if line:
            parsed_data = parse_line(line)
            if parsed_data:
                return parsed_data
        return line
    except Exception as e:
        print(f"Errore lettura seriale: {e}")

                