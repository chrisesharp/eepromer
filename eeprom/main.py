#!/usr/bin/env python3.7
# Chris Sharp, https://github.com/chrisesharp
# --
# Uses the Arduino firmware on http://danceswithferrets.org/geekblog/?p=496
# --
# Inspired by the original python 2.7 code by: 
# Chris Baird, <cjb@brushtail.apana.org.au>

from getopt import getopt, GetoptError
import struct
from time import sleep
from .writer import EEPROM, EEPROMException
from .programmer import Programmer
import sys

def usage(err):
    MODULE = sys.argv[0].split("/")[-2]
    print(err)
    print("Usage: %s [ -V | -r | -w | -d] [-v] [-s n] [-e n] [-p port] rom_file" % (MODULE))
    print("Where:")
    print("    -V - print EEPROM writer firmware version")
    print("    -r - read EEPROM contents and print as hex (default option)")
    print("    -w - write ROM file to EEPROM")
    print("    -d - dump EEPROM contents to rom_file (default is False)")
    print("    -v - verify contents of EEPROM with ROM file (default is False)")
    print("    -s - start address (default is 0")
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
    version = False

    try:
        opts, args = getopt(input, "Vrwdvbs:e:p:")
        if len(args) > 0:
            rom_file = args.pop(0)
    except GetoptError as err:
        usage(err)

    for o, a in opts:
        if o == "-d":
            dump_rom = True
        elif o == "-v":
            verify_rom = True
        elif o == "-V":
            version = True
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
    if version:
        return (True, None, -1, -1, False, False, TTY)
    
    return (reading, rom_file, start, end, verify_rom, dump_rom, TTY)

def main(args):
    WAIT_FOR_ARDUINO_IN_SECS = 1 # Minimum of 1 sec required
    (reading, rom_file, dumpstart, dumpend, verify_rom, dump_rom, TTY) = parse_args(args[1:])

    eeprom = EEPROM()
    try:
        eeprom.open_port(TTY)
        sleep(WAIT_FOR_ARDUINO_IN_SECS)
    except EEPROMException:
        print("No serial device attached.")
        exit(-2)
    
    programmer = Programmer(eeprom, sys.stdout)
    programmer.set_start(dumpstart)
    programmer.set_end(dumpend)
    programmer.set_verify(verify_rom)

    if (not reading) or verify_rom:
        programmer.set_input_rom(rom_file)
    elif dump_rom:
        programmer.set_dump_file(rom_file)

    if reading:
        programmer.read_eeprom()
    else:
        programmer.write_eeprom()