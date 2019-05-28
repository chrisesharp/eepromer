from serial import Serial, SerialException
import sys
import struct

OK = b'OK\r\n'

class EEPROM():
    def __init__(self, rom_size=8192):
        self.RECSIZE = 16
        self.port = None
        self.rom_size = rom_size
    
    def open_port(self, tty_port="/dev/tty.usbserial-1420"):
        if isinstance(tty_port, str):
            try:
                self.port = Serial(tty_port, timeout=0.1, dsrdtr=True)
            except SerialException as err:
                raise EEPROMException(err)
        else:
            self.port = tty_port
    
    def __del__(self):
        self.close()
    
    def close(self):
        if self.port:
            self.port.close()
    
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
        return cmd
    
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
    
    def version(self):
        cmd = str.encode("V" + chr(10))
        self.send_cmd(cmd)
        response = self.port.readline().upper()
        return response.decode('UTF-8')
    
    def send_cmd(self, cmd):
        self.port.write(cmd)
        self.port.flush()

def address_field(addr):
    return ("%04x" % addr).upper()

def data_field(data):
    chksum = 0
    payload = ""
    for byte in data:
        payload += ("%02x" % byte)
        chksum = chksum ^ byte
    payload += "ffffffffffffffffffffffffffffffff"
    payload = payload[:32]
    if (len(data) & 1):
        chksum = chksum ^ 255
    chksum = chksum & 255
    payload += "," + ("%02x" % chksum)
    return payload.upper()

class EEPROMException(Exception):
    pass