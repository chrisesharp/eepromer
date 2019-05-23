from serial import Serial
from time import sleep
import sys
import struct
from .writer import EEPROM

class Programmer():
    def __init__(self, eeprom_programmer, print_stream):
        self.rom_src = None
        self.file_name = None
        self.dump_rom = False
        self.verify_rom = False
        self.start = 0
        self.end = 0
        self.output_stream = None
        self.print_stream = print_stream
        self.programmer = eeprom_programmer
        self.RECSIZE = 16
    
    def set_start(self, start):
        self.start = start
    
    def set_end(self, end):
        self.end = end
    
    def set_verify(self, verify):
        self.verify_rom = verify
    
    def set_input_rom(self, filename):
        self.file_name = filename
        rom_size, self.rom_src = read_rom_from_file(filename, self.RECSIZE)
        print("ROM file is {} bytes long.".format(rom_size), file=self.print_stream)
        if rom_size < (self.end - self.start):
            print("The ROM file is smaller than the specified address range.", file=self.print_stream)
            exit(-1)
    
    def set_dump_file(self, filename):
        self.dump_rom = True
        self.file_name = filename
        print("Writing contents to ", filename, file=self.print_stream)
        self.output_stream = open(filename, 'wb')
    
    def format_record(self, input, record, formatter):
        output = str(input) + ":"
        for i in range(self.RECSIZE):
            output += (" %02x" % formatter(record, i)).upper()
        return output
    
    def check_diff(self, address, eprom_record):
        output = ""
        actual = self.format_record(address, eprom_record, rom_byte)
        file_index = int((address - self.start) / self.RECSIZE)
        file_record = self.format_record(address, self.rom_src[file_index], file_byte)
        if actual != file_record:
            output = "DIFF:\n"
            output += "\tROM :" + actual + "\n"
            output += "\tFILE:" + file_record + "\n"
        return output
    
    def read_eeprom(self):
        if self.start < 0:
            print(self.programmer.version(), file=self.print_stream)
            return 

        print("Reading EEPROM from {} to {}".format(self.start, self.end), file=self.print_stream)
        if self.verify_rom:
            print("Verifying...", file=self.print_stream)
        if self.dump_rom:
            print( "Dumping to file.", file=self.print_stream)
        bytes_written = 0
        address = self.start
        while (address < self.end):
            record = self.programmer.read(address)
            if self.verify_rom:
                diff = self.check_diff(address, record)
                if diff:
                    print(diff, file=self.print_stream)
            elif self.dump_rom:
                bytes_written += write_record_to_file(record, self.output_stream)
            else:
                print(record, file=self.print_stream)
            address += self.RECSIZE
        
        if self.dump_rom:
            print("bytes written:" + str(bytes_written), file=self.print_stream)
            self.output_stream.close()
        return
    
    def write_eeprom(self):
        print("Writing ROM {} to EEPROM.".format(self.file_name), file=self.print_stream)
        address = self.start
        for record in self.rom_src:
            self.programmer.write(address, record)
            if self.verify_rom:
                readback = self.programmer.read(address)
                diff = self.check_diff(address, readback)
                if diff:
                    print(diff, file=self.print_stream)
            address += self.RECSIZE
            if address >= self.end:
                break
        return

def read_rom_from_file(rom_file, recsize):
    rom = []
    num_bytes = 0
    with open(rom_file, 'rb') as rom_src:
        for record in iter(lambda: rom_src.read(recsize), b''):
            rom.append(record)
            num_bytes += len(record)
    return num_bytes, rom

def write_record_to_file(record, output):
    data = record[5:-5]
    bytes_written = 0
    for i in range(0, 64, 2):
        byte_string = data[i:i+2]
        if byte_string:
            byte = struct.pack("B", int(byte_string, 16))
            bytes_written += output.write(byte)
    return bytes_written

def rom_byte(record, index):
    i = 5 + (index*2)
    byte = int(record[i:i+2], 16)
    return byte

def file_byte(record, index):
    return record[index]