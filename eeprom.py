from serial import Serial
from time import sleep
import sys

OK = b'OK\r\n'

class EEPROM():
    def __init__(self, tty_port):
        self.RECSIZE = 16
        self.port = Serial(tty_port,
                    timeout=0.1,
                    baudrate=9600,
                    dsrdtr=True)
        sleep(1)
    
    def read(self, addr):
        cmd = str.encode("R" + address_field(addr) + chr(10))
        self.send_cmd(cmd)
        response = self.port.readline().upper()
        self.wait_okay()
        return response
    
    def write(self, addr, data):
        cmd = str.encode("W" + address_field(addr) + ":" + data_field(data) + chr(10))
        self.send_cmd(cmd)
        self.wait_okay()
    
    def wait_okay(self):
        retries = 0
        resp = self.port.readline()
        while resp != OK:
            print("RESP:", resp)
            retries += 1
            if retries > 5:
                self.port.close()
                sys.exit("Didn't receive OK back from programmer.\n")
            resp = self.port.readline()
    
    def send_cmd(self, cmd):
        self.port.write(cmd)
        self.port.flush()

    def close(self):
        self.port.close()

def address_field(addr):
    return ("%04x" % addr).upper()

def data_field(data):
    chksum = 0
    payload = ""
    for byte in data:
        payload += ("%02x" % byte)
        chksum = chksum ^ byte
    payload += "ffffffffffffffffffffffffffffffff"
    payload = payload[:38]
    if (len(data) & 1):
        chksum = chksum ^ 255
    chksum = chksum & 255
    payload += "," + ("%02x" % chksum)
    return payload.upper()
