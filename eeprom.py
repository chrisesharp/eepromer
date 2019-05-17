from serial import Serial
from time import sleep

OK = b'OK\r\n'

class EEPROM():
    def __init__(self, tty_port):
        RECSIZE = 16
        serial_port = Serial(tty_port,
                    timeout=0.1,
                    baudrate=9600,
                    dsrdtr=True)
        sleep(0.5)
    
    def read(self, address, data):
        pass
    
    def write(self, address, data):
        pass