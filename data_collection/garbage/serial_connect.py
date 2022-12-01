import serial

ser = serial.Serial()
from serial.tools import list_ports

device_name = "***"

ports = list_ports.comports()
for info in ports:
    print(info.serial_number)
print(ports)