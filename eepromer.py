#!/usr/bin/env python3.7
# Chris Sharp, https://github.com/chrisesharp
# --
# Uses the Arduino firmware on http://danceswithferrets.org/geekblog/?p=496
# --
# Inspired by the original python 2.7 code by: 
# Chris Baird, <cjb@brushtail.apana.org.au>


import sys
from serial import Serial
from time import sleep
from getopt import getopt, GetoptError
import struct

RECSIZE = 16
OK = b'OK\r\n'

def open_serial_port(port):
    serial_port = Serial(port,
                        timeout=0.1,
                        baudrate=9600,
                        dsrdtr=True)
    sleep(1)
    return serial_port

def calc_writeline(addr, data):
    chksum = 0
    cmd = "W" + ("%04x" % addr) + ":"
    for byte in data:
        cmd += ("%02x" % byte)
        chksum = chksum ^ byte
    cmd += "ffffffffffffffffffffffffffffffff"
    cmd = cmd[:38]
    if (len(data) & 1):
        chksum = chksum ^ 255
    chksum = chksum & 255
    cmd += "," + ("%02x" % chksum)
    return cmd.upper()

def wait_okay(port):
    retries = 0
    resp = port.readline()
    while resp != OK:
        print(resp)
        retries += 1
        if retries > 50:
            port.close()
            sys.exit("Didn't receive OK back from programmer.\n")
        resp = port.readline()

def read_record_from_file(rom):
    record = rom.read(RECSIZE)
    if len(record) == 0:
        return None
    return record

def read_rom_from_file(rom_file):
    rom = []
    with open(rom_file, 'rb') as rom_src:
        for record in iter(lambda: rom_src.read(RECSIZE), b''):
            rom.append(record)
    return rom

def format_record(input, record, func):
    output = input[:] + ":"
    for i in range(RECSIZE):
        output += (" %02x" % func(record, i)).upper()
    return output

def rom_byte(record, index):
    i = 5 + (index*2)
    byte = int(record[i:i+2], 16)
    return byte

def file_byte(record, index):
    return record[index]

def read_eeprom(port, rom_file_name, dumpstart, dumpend, verify=False, dump_rom=False):
    rom_src = None
    output_stream = None
    print("Reading EEPROM from {} to {}".format(dumpstart, dumpend))
    if verify:
        if not rom_file_name:
            usage("Must provide ROM file to verify against.")
        elif dump_rom:
            usage("Can't verify AND dump to file...choose one or other.")
        else:
            rom_src = read_rom_from_file(rom_file_name)
            print("Verifying EEPROM from file {}".format(rom_file_name))
            rom_size = len(rom_src) * RECSIZE
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
        addr = ("%04x" % address).upper()
        cmd = str.encode("R" + addr + chr(10))
        port.write(cmd)
        port.flush()
        line = port.readline().upper()
        if verify:
            rom_record = format_record(addr, line, rom_byte)
            file_record = format_record(addr, rom_src[int(address/RECSIZE)], file_byte)
            if rom_record != file_record:
                print("DIFF:")
                print("\tROM :" + rom_record)
                print("\tFILE:" + file_record)
        elif dump_rom:
            data = line[5:-5]
            for i in range(0, 64, 2):
                byte_string = data[i:i+2]
                if byte_string:
                    byte = struct.pack("B", int(byte_string, 16))
                    bytes_written += output_stream.write(byte)
        else:
            print(line)
        wait_okay(port)
        address += RECSIZE
    if dump_rom:
        print("bytes written:", bytes_written)

def write_eeprom(port, rom_file, start, end, verify=False, hex_output=False):
    if not rom_file:
        usage("Must provide ROM file to write.")
    print("Writing ROM {} to EEPROM.".format(rom_file))
    address = start
    for record in read_rom_from_file(rom_file):
        data = calc_writeline(address, record)
        print("Writing command {} to programmer.".format(data))
        port.write(str.encode(data + chr(10)))
        port.flush()
        wait_okay(port)
        address += RECSIZE
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
            dumpstart = int(a)
        elif o == "-e":
            dumpend = int(a)
        elif o == "-p":
            TTY = a
        elif o == "-r":
            func = read_eeprom
        elif o == "-w":
            func = write_eeprom

    return func, rom_file, start, end, verify_rom, dump_rom, TTY


if __name__ == "__main__":
    op, rom_file, dumpstart, dumpend, verify_rom, dump_rom, TTY = parse_args(sys.argv[1:])
    port = open_serial_port(TTY)
    op(port, rom_file, dumpstart, dumpend, verify_rom, dump_rom)
    port.close()
