#!/usr/bin/env python3.7
# Chris Sharp, https://github.com/chrisesharp
# --
# Uses the Arduino firmware on http://danceswithferrets.org/geekblog/?p=496
# --
# Inspired by the original python 2.7 code by: 
# Chris Baird, <cjb@brushtail.apana.org.au>


import sys
from getopt import getopt, GetoptError
import struct
from eeprom_writer import EEPROM

# programmer = None

class Programmer():
    def __init__(self, TTY="/dev/tty.usbserial-1420"):
        self.rom_src = None
        self.file_name = None
        self.TTY = TTY
        self.dump_rom = False
        self.verify_rom = False
        self.start = 0
        self.end = 0
        self.output_stream = None
        self.programmer = EEPROM(TTY)
        self.RECSIZE = 16
    
    def set_start(self, start):
        self.start = start
    
    def set_end(self, end):
        self.end = end
    
    def set_verify(self, verify):
        self.verify_rom = verify
    
    def set_input_rom(self, filename):
        self.file_name = filename
        self.rom_src = read_rom_from_file(filename, self.RECSIZE)
        rom_size = len(self.rom_src) * self.RECSIZE
        print("ROM file is {} bytes long.".format(rom_size))
        if rom_size < (self.end - self.start):
            print("The ROM file is smaller than the specified address range.")
            exit(-1)
    
    def set_dump_file(self, filename):
        self.file_name = filename
        print("Writing contents to ", filename)
        self.output_stream = open(filename, 'wb')
    
    def format_record(self, input, record, formatter):
        output = str(input) + ":"
        for i in range(self.RECSIZE):
            output += (" %02x" % formatter(record, i)).upper()
        return output
    
    def check_diff(self, address, eprom_record):
        actual = self.format_record(address, eprom_record, rom_byte)
        file_index = int((address - self.start) / self.RECSIZE)
        file_record = self.format_record(address, self.rom_src[file_index], file_byte)
        if actual != file_record:
            print("DIFF:")
            print("\tROM :" + actual)
            print("\tFILE:" + file_record)
    
    def read_eeprom(self):
        print("Reading EEPROM from {} to {}".format(self.start, self.end))
        if self.verify_rom:
            print("Verifying...")
        bytes_written = 0
        address = self.start
        while (address < self.end):
            record = self.programmer.read(address)
            if self.verify_rom:
                self.check_diff(address, record)
            elif self.output_stream:
                bytes_written += write_record_to_file(record, self.output_stream)
            else:
                print(record)
            address += self.RECSIZE
        
        if self.dump_rom:
            print("bytes written:", bytes_written)
            self.output_stream.close()
    
    def write_eeprom(self):
        print("Writing ROM {} to EEPROM.".format(self.file_name))
        address = self.start
        for record in self.rom_src:
            self.programmer.write(address, record)
            if self.verify_rom:
                readback = self.programmer.read(address)
                self.check_diff(address, readback)
            address += self.RECSIZE
            if address >= self.end:
                break


def read_rom_from_file(rom_file, recsize):
    rom = []
    with open(rom_file, 'rb') as rom_src:
        for record in iter(lambda: rom_src.read(recsize), b''):
            rom.append(record)
    return rom

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

def usage(err):
    print(err)
    print("Usage: %s [-r [-v] | -w | -d] [-s n] [-e n] [-p port] rom_file" % (sys.argv[0]))
    print("Where:")
    print("    -r - read EEPROM contents and print as hex (default option)")
    print("    -w - write ROM file to EEPROM")
    print("    -v - verify contents of EEPROM with ROM file (default is False)")
    print("    -d - dump EEPROM contents to rom_file (default is False)")
    print("    -s - start address")
    print("    -e - end address")
    print("    -p - USB port tty (default is /dev/tty.usbserial-1420")
    print("    rom_file - ROM file to write or verify against")
    exit(-1)

def parse_args(input):
    rom_file = None
    TTY = "/dev/tty.usbserial-1420"
    dump_rom = False
    verify_rom = False
    start = 0
    end = 0
    reading = True

    try:
        opts, args = getopt(input, "rwdvbs:e:p:")
        if len(args) > 0:
            rom_file = args.pop(0)
    except GetoptError as err:
        usage(err)

    for o, a in opts:
        if o == "-d":
            dump_rom = True
        elif o == "-v":
            verify_rom = True
            reading = True
        elif o == "-s":
            start = int(a)
        elif o == "-e":
            end = int(a)
        elif o == "-p":
            TTY = a
        elif o == "-r":
            reading = True
        elif o == "-w":
            reading = False

    if verify_rom and dump_rom:
        usage("Can't verify AND dump to file...choose one or other.")
    if verify_rom and not rom_file:
        usage("Must provide ROM file to verify against.")
    if dump_rom and not rom_file:
        usage("Must provide ROM file name to dump to.")
    
    return (reading, rom_file, start, end, verify_rom, dump_rom, TTY)


if __name__ == "__main__":
    (reading, rom_file, dumpstart, dumpend, verify_rom, dump_rom, TTY) = parse_args(sys.argv[1:])

    eeprom = Programmer(TTY)
    eeprom.set_start(dumpstart)
    eeprom.set_end(dumpend)
    eeprom.set_verify(verify_rom)

    if (not reading) or verify_rom:
        eeprom.set_input_rom(rom_file)
    elif dump_rom:
        eeprom.set_dump_file(rom_file)

    if reading:
        eeprom.read_eeprom()
    else:
        eeprom.write_eeprom()

