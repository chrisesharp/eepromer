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
from eeprom import EEPROM

programmer = None

def read_rom_from_file(rom_file):
    rom = []
    with open(rom_file, 'rb') as rom_src:
        for record in iter(lambda: rom_src.read(programmer.RECSIZE), b''):
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

def format_record(input, record, formatter):
    output = str(input) + ":"
    for i in range(programmer.RECSIZE):
        output += (" %02x" % formatter(record, i)).upper()
    return output

def rom_byte(record, index):
    i = 5 + (index*2)
    byte = int(record[i:i+2], 16)
    return byte

def file_byte(record, index):
    return record[index]

def check_diff(address, base, eprom_record, rom_src):
    actual = format_record(address, eprom_record, rom_byte)
    file_index = int((address - base) / programmer.RECSIZE)
    file_record = format_record(address, rom_src[file_index], file_byte)
    if actual != file_record:
        print("DIFF:")
        print("\tROM :" + actual)
        print("\tFILE:" + file_record)

def read_eeprom(programmer, rom_file_name, dumpstart, dumpend, verify=False, dump_rom=False):
    rom_src = None
    output_stream = None
    print("Reading EEPROM from {} to {}".format(dumpstart, dumpend))
    if verify:
        print("Verifying EEPROM from file {}".format(rom_file_name))
        rom_src = read_rom_from_file(rom_file_name)
        rom_size = len(rom_src) * programmer.RECSIZE
        print("ROM file is {} records long.".format(rom_size))
        if rom_size < (dumpend - dumpstart):
            print("The ROM file is smaller than the specified address range.")
            exit(1)

    if dump_rom:
        print("Writing contents to ", rom_file_name)
        output_stream = open(rom_file_name, 'wb')

    bytes_written = 0
    address = dumpstart
    while (address < dumpend):
        record = programmer.read(address)
        if verify:
            check_diff(address, dumpstart, record, rom_src)
        elif dump_rom:
            bytes_written += write_record_to_file(record, output_stream)
        else:
            print(record)
        address += programmer.RECSIZE
    
    if dump_rom:
        print("bytes written:", bytes_written)
        output_stream.close()

def write_eeprom(programmer, rom_file, start, end, verify=False, hex_output=False):
    if not rom_file:
        usage("Must provide ROM file to write.")
    print("Writing ROM {} to EEPROM.".format(rom_file))
    address = start
    for record in read_rom_from_file(rom_file):
        programmer.write(address, record)
        address += programmer.RECSIZE
        if address >= end:
            break

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
    func = read_eeprom
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
            func = read_eeprom
        elif o == "-s":
            start = int(a)
        elif o == "-e":
            end = int(a)
        elif o == "-p":
            TTY = a
        elif o == "-r":
            func = read_eeprom
        elif o == "-w":
            func = write_eeprom

    if verify_rom and dump_rom:
        usage("Can't verify AND dump to file...choose one or other.")
    if verify_rom and not rom_file:
        usage("Must provide ROM file to verify against.")
    if dump_rom and not rom_file:
        usage("Must provide ROM file name to dump to.")
    
    return (func, rom_file, start, end, verify_rom, dump_rom, TTY)


if __name__ == "__main__":
    (op, rom_file, dumpstart, dumpend, verify_rom, dump_rom, TTY) = parse_args(sys.argv[1:])
    programmer = EEPROM(TTY)
    op(programmer, rom_file, dumpstart, dumpend, verify_rom, dump_rom)
    programmer.close()
