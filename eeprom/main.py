#!/usr/bin/env python3.7
# Chris Sharp, https://github.com/chrisesharp
# --
# Uses the Arduino firmware on http://danceswithferrets.org/geekblog/?p=496
# --
# Inspired by the original python 2.7 code by: 
# Chris Baird, <cjb@brushtail.apana.org.au>

from getopt import getopt, GetoptError
from enum import IntEnum
import struct
from time import sleep
from .writer import EEPROM, EEPROMException
from .programmer import Programmer
import sys
from .fake_serial import Serial as FakeSerial

MODULE_NAME = "eeprom"

class ROMSIZE(IntEnum):
    ROM1K = 1
    ROM2K = 2
    ROM4K = 4
    ROM8K = 8
    ROM16K = 16
    ROM32K = 32
    ROM64K = 64

def usage(out, err):
    print(err, file=out)
    print("Usage: %s [ -V | -r | -w | -d] [-v] [-s n] [-e n] [-p port] [-S n] rom_file" % (MODULE_NAME), file=out)
    print("Where:", file=out)
    print("    -V - print EEPROM writer firmware version", file=out)
    print("    -r - read EEPROM contents and print as hex (default option)", file=out)
    print("    -w - write ROM file to EEPROM", file=out)
    print("    -d - dump EEPROM contents to rom_file (default is False)", file=out)
    print("    -v - verify contents of EEPROM with ROM file (default is False)", file=out)
    print("    -s - start address (default is 0", file=out)
    print("    -e - end address", file=out)
    print("    -p - USB port tty (default is /dev/tty.usbserial-1420", file=out)
    print("    -S - EEPROM size in K (default is 8)", file=out)
    print("    rom_file - ROM file to write or verify against", file=out)
    exit(-1)

def parse_args(outstream, input):
    options = {
            "rom_file": None,
            "TTY":  "/dev/tty.usbserial-1420",
            "dump_rom": False,
            "verify_rom": False,
            "start": 0,
            "end": 0,
            "reading": True,
            "version": False,
            "debug": False,
            "rom_size": int(ROMSIZE.ROM8K)
        }

    try:
        opts, args = getopt(input, "Vrwdvbxs:e:p:S:")
        if len(args) > 0:
            options["rom_file"] = args.pop(0)
    except GetoptError as err:
        usage(outstream, err)

    for o, a in opts:
        if o == "-d":
            options["dump_rom"] = True
        elif o == "-v":
            options["verify_rom"] = True
        elif o == "-V":
            options["version"] = True
        elif o == "-s":
            options["start"] = int(a)
        elif o == "-e":
            options["end"] = int(a)
        elif o == "-p":
            options["TTY"] = a
        elif o == "-r":
            options["reading"] = True
        elif o == "-w":
            options["reading"] = False
        elif o == "-x":
            options["debug"] = True
        elif o == "-S":
            try:
                options["rom_size"] = ROMSIZE(int(a))
            except ValueError as err:
                usage(outstream, err)

    if options["verify_rom"] and options["dump_rom"]:
        usage(outstream, "Can't verify AND dump to file...choose one or other.")
    if options["verify_rom"] and not options["rom_file"]:
        usage(outstream, "Must provide ROM file to verify against.")
    if options["dump_rom"] and not options["rom_file"]:
        usage(outstream, "Must provide ROM file name to dump to.")
    if ((options["end"] - options["start"]) > options["rom_size"] * 1024):
        usage(outstream, "Address range is bigger than EEPROM size.")
    if options["version"]:
        options["reading"] = True
        options["start"] = -1
        options["end"] = -1
        return options
    
    return options

def main(outstream, args):
    WAIT_FOR_ARDUINO_IN_SECS = 1 # Minimum of 1 sec required
    options = parse_args(outstream, args[1:])

    eeprom = EEPROM(options["rom_size"] * 1024)
    if options["debug"]:
        options["TTY"] = FakeSerial(options["TTY"])
        
    try:
        eeprom.open_port(options["TTY"])
        sleep(WAIT_FOR_ARDUINO_IN_SECS)
    except EEPROMException:
        print("No serial device attached.", file=outstream)
        exit(-2)
    
    programmer = Programmer(eeprom, outstream)
    programmer.set_start(options["start"])
    programmer.set_end(options["end"])
    programmer.set_verify(options["verify_rom"])
    programmer.set_debug(options["debug"])

    if (not options["reading"]) or options["verify_rom"]:
        programmer.set_input_rom(options["rom_file"])
    elif options["dump_rom"]:
        programmer.set_dump_file(options["rom_file"])

    if options["reading"]:
        programmer.read_eeprom()
    else:
        programmer.write_eeprom()