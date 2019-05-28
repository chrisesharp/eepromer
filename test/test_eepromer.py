from eeprom.writer import EEPROM
from eeprom.programmer import Programmer
from eeprom.main import main
from io import StringIO, BytesIO
import pytest
import os

usage_string = """Usage: eeprom [ -V | -r | -w | -d] [-v] [-s n] [-e n] [-p port] [-S n] rom_file
Where:
    -V - print EEPROM writer firmware version
    -r - read EEPROM contents and print as hex (default option)
    -w - write ROM file to EEPROM
    -d - dump EEPROM contents to rom_file (default is False)
    -v - verify contents of EEPROM with ROM file (default is False)
    -s - start address (default is 0
    -e - end address
    -p - USB port tty (default is /dev/tty.usbserial-1420
    -S - EEPROM size in K (default is 8)
    rom_file - ROM file to write or verify against
"""

class MockEEPROM():
    def __init__(self, rom_size=8192):
        self.rom_size = rom_size
    
    def read(self, addr):
        addr = ("%04x" % addr).upper()
        # Fill with 'A' characters
        return addr + ":41414141414141414141414141414141,00\r\n"
    
    def write(self, addr, data):
        pass
    
    def version(self):
        return "EEPROM VERSION=TEST"
    

class MockSerial():
    def __init__(self, test_data=None):
        self.in_stream = BytesIO()
        self.out_stream = BytesIO(test_data)

    def readline(self):
        return self.out_stream.readline()
    
    def close(self):
        pass
    
    def write(self, bytes):
        self.in_stream.write(bytes)
    
    def flush(self):
        pass

def test_eeprom_writer_version():
    test_port = MockSerial(b"EEPROM VERSION=TEST\n")
    eeprom = EEPROM()
    eeprom.open_port(test_port)
    response = eeprom.version()
    print(response)
    assert response == "EEPROM VERSION=TEST\n"

def test_eeprom_writer_read():
    test_port = MockSerial(b"FFFF\nOK\r\n")
    eeprom = EEPROM()
    eeprom.open_port(test_port)
    response = eeprom.read(0)
    print(response)
    assert response == b"FFFF\n"

def test_eeprom_writer_write_without_parity():
    test_port = MockSerial(b"FFFF\nOK\r\n")
    eeprom = EEPROM()
    eeprom.open_port(test_port)
    response = eeprom.write(0,b'')
    assert response == b'W0000:FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF,00\n'
    assert test_port.in_stream.getvalue() == b'W0000:FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF,00\n'


def test_eeprom_writer_write_with_parity():
    test_port = MockSerial(b"OK\r\n")
    eeprom = EEPROM()
    eeprom.open_port(test_port)
    response = eeprom.write(0,b'A')
    assert response == b'W0000:41FFFFFFFFFFFFFFFFFFFFFFFFFFFFFF,BE\n'
    assert test_port.in_stream.getvalue() == b'W0000:41FFFFFFFFFFFFFFFFFFFFFFFFFFFFFF,BE\n'


def test_eeprom_writer_write_fails_when_no_OK():
    test_port = MockSerial()
    eeprom = EEPROM()
    eeprom.open_port(test_port)
    with pytest.raises(SystemExit):
        response = eeprom.write(0,b'HELLO\n')


def test_programmer_version_returned_for_invalid_start():
    eeprom = MockEEPROM()
    result = StringIO()
    programmer = Programmer(eeprom, result)
    programmer.set_start(-1)
    
    programmer.read_eeprom() 
    assert result.getvalue() == "EEPROM VERSION=TEST\n"

def test_programmer_read_0_15_bytes():
    eeprom = MockEEPROM()
    result = StringIO()
    programmer = Programmer(eeprom, result)
    programmer.set_start(0)
    programmer.set_end(15)

    programmer.read_eeprom() 
    assert result.getvalue() == """Reading EEPROM from 0 to 15
0000:41414141414141414141414141414141,00\r\n
"""

def test_programmer_read_16_31_bytes():
    eeprom = MockEEPROM()
    result = StringIO()
    programmer = Programmer(eeprom, result)
    programmer.set_start(16)
    programmer.set_end(31)

    programmer.read_eeprom()
    assert result.getvalue() == """Reading EEPROM from 16 to 31
0010:41414141414141414141414141414141,00\r\n
"""

def test_programmer_read_0_31_bytes():
    eeprom = MockEEPROM()
    result = StringIO()
    programmer = Programmer(eeprom, result)
    programmer.set_start(0)
    programmer.set_end(31)

    programmer.read_eeprom()
    print(result.getvalue())
    assert result.getvalue() == """Reading EEPROM from 0 to 31
0000:41414141414141414141414141414141,00\r\n
0010:41414141414141414141414141414141,00\r\n
"""

def test_programmer_read_verify_0_64_bytes_fails_with_smaller_file():
    eeprom = MockEEPROM()
    result = StringIO()
    programmer = Programmer(eeprom, result)
    programmer.set_start(0)
    programmer.set_end(63)
    programmer.set_verify(True)
    with pytest.raises(SystemExit):
        programmer.set_input_rom("test/testA.rom")


def test_programmer_read_verify_0_31_bytes():
    test_input = "test/testA.rom"
    eeprom = MockEEPROM()
    result = StringIO()
    programmer = Programmer(eeprom, result)
    programmer.set_start(0)
    programmer.set_end(31)
    programmer.set_input_rom(test_input)
    programmer.set_verify(True)

    programmer.read_eeprom()
    print(result.getvalue())
    assert result.getvalue() == """ROM file is {} bytes long.
Reading EEPROM from 0 to 31
Verifying...
""".format(os.path.getsize(test_input))

def test_programmer_read_verify_0_31_bytes_fail():
    test_input = "test/testB.rom"
    eeprom = MockEEPROM()
    result = StringIO()
    programmer = Programmer(eeprom, result)
    programmer.set_start(0)
    programmer.set_end(31)
    programmer.set_input_rom(test_input)
    programmer.set_verify(True)

    programmer.read_eeprom()
    print(result.getvalue())
    assert result.getvalue() == """ROM file is {} bytes long.
Reading EEPROM from 0 to 31
Verifying...
DIFF:
	ROM :0: 41 41 41 41 41 41 41 41 41 41 41 41 41 41 41 41
	FILE:0: 42 42 42 42 42 42 42 42 42 42 42 42 42 42 42 42

DIFF:
	ROM :16: 41 41 41 41 41 41 41 41 41 41 41 41 41 41 41 41
	FILE:16: 42 42 42 42 42 42 42 42 42 42 42 42 42 42 42 42

""".format(os.path.getsize(test_input))

def test_programmer_write_0_31_bytes():
    test_input = "test/testA.rom"
    eeprom = MockEEPROM()
    result = StringIO()
    programmer = Programmer(eeprom, result)
    programmer.set_start(0)
    programmer.set_end(31)
    programmer.set_input_rom(test_input)

    programmer.write_eeprom()
    print(result.getvalue())
    assert result.getvalue() == """ROM file is {} bytes long.
Writing ROM test/testA.rom to EEPROM.
""".format(os.path.getsize(test_input))

def test_programmer_write_verify_0_31_bytes():
    test_input = "test/testA.rom"
    eeprom = MockEEPROM()
    result = StringIO()
    programmer = Programmer(eeprom, result)
    programmer.set_start(0)
    programmer.set_end(31)
    programmer.set_input_rom(test_input)
    programmer.set_verify(True)

    programmer.write_eeprom()
    print(result.getvalue())
    assert result.getvalue() == """ROM file is {} bytes long.
Writing ROM test/testA.rom to EEPROM.
""".format(os.path.getsize(test_input))


def test_programmer_write_verify_0_31_bytes_fails():
    test_input = "test/testB.rom"
    eeprom = MockEEPROM()
    result = StringIO()
    programmer = Programmer(eeprom, result)
    programmer.set_start(0)
    programmer.set_end(31)
    programmer.set_input_rom(test_input)
    programmer.set_verify(True)

    programmer.write_eeprom()
    print(result.getvalue())
    assert result.getvalue() == """ROM file is {} bytes long.
Writing ROM {} to EEPROM.
DIFF:
	ROM :0: 41 41 41 41 41 41 41 41 41 41 41 41 41 41 41 41
	FILE:0: 42 42 42 42 42 42 42 42 42 42 42 42 42 42 42 42

DIFF:
	ROM :16: 41 41 41 41 41 41 41 41 41 41 41 41 41 41 41 41
	FILE:16: 42 42 42 42 42 42 42 42 42 42 42 42 42 42 42 42

""".format(os.path.getsize(test_input), test_input)

def test_programmer_read_dump_0_31_bytes_file():
    test_input = "test/testA.rom"
    test_output = "test/testA.out"
    read_size = 32
    expected_size = os.path.getsize(test_input)
    eeprom = MockEEPROM()
    result = StringIO()
    programmer = Programmer(eeprom, result)
    programmer.set_start(0)
    programmer.set_end(read_size - 1)
    programmer.set_input_rom(test_input)
    programmer.set_dump_file(test_output)

    programmer.read_eeprom()
    print(result.getvalue())
    assert result.getvalue() == """ROM file is {} bytes long.
Writing contents to  {}
Reading EEPROM from 0 to {}
Dumping to file.
bytes written:{}
""".format(expected_size, test_output, read_size - 1, read_size)
    assert os.path.getsize(test_output) == read_size
    os.remove(test_output)


def test_programmer_rom_size():
    test_input = "test/testC.rom"
    write_size = 2048
    eeprom = MockEEPROM(1024)
    result = StringIO()
    programmer = Programmer(eeprom, result)
    programmer.set_start(0)
    programmer.set_end(write_size - 1)
    programmer.set_input_rom(test_input)
    programmer.set_verify(True)

    with pytest.raises(SystemExit):
        response = programmer.write_eeprom()

def test_main_arg_parsing_valid_args():
    result = StringIO()
    with pytest.raises(SystemExit) as err:
        main(result, ["", "-?"])
    print(result.getvalue())
    assert result.getvalue() == "option -? not recognized\n" + usage_string

def test_main_arg_parsing_romsize():
    result = StringIO()
    with pytest.raises(SystemExit) as err:
        main(result, ["", "-S","33"])
    assert result.getvalue() == "33 is not a valid ROMSIZE\n" + usage_string

def test_main_arg_parsing_options_verify_dump_conflict():
    result = StringIO()
    with pytest.raises(SystemExit) as err:
        main(result, ["", "-d", "-v", "-s","0", "-e", "15", "test/testC.rom"])
    assert result.getvalue() == "Can't verify AND dump to file...choose one or other.\n" + usage_string

def test_main_arg_parsing_options_verify_file_required():
    result = StringIO()
    with pytest.raises(SystemExit) as err:
        main(result, ["", "-v"])
    assert result.getvalue() == "Must provide ROM file to verify against.\n" + usage_string

def test_main_arg_parsing_options_dump_file_required():
    result = StringIO()
    with pytest.raises(SystemExit) as err:
        main(result, ["", "-d"])
    assert result.getvalue() == "Must provide ROM file name to dump to.\n" + usage_string

def test_main_arg_parsing_options_right_sizes():
    result = StringIO()
    with pytest.raises(SystemExit) as err:
        main(result, ["", "-S", "1", "-s", "0", "-e", "2048"])
    assert result.getvalue() == "Address range is bigger than EEPROM size.\n" + usage_string

def test_main_arg_parsing_options():
    result = StringIO()
    with pytest.raises(SystemExit) as err:
        main(result, ["", "-r", "-V"])
    assert result.getvalue() == "No serial device attached.\n"

def test_debug_mode_write():
    result_out = StringIO()
    result_serial = BytesIO()
    test_input = "test/testB.rom"
    main(result_out, ["", "-w", "-x", "-s", "0", "-e", "16", "-p", result_serial , test_input])
    print("OUT:", result_out.getvalue())
    assert result_out.getvalue() == """ROM file is 32 bytes long.
Writing ROM test/testB.rom to EEPROM.
"""
    print("SERIAL:", result_serial.getvalue())
    assert result_serial.getvalue() == b'W0000:42424242424242424242424242424242,00\n'

def test_debug_mode_dump():
    result_out = StringIO()
    result_serial = BytesIO()
    main(result_out, ["", "-x", "-s", "0", "-e", "15", "-d", "-p", result_serial, "/tmp/foo"])
    print("OUT:", result_out.getvalue())
    assert result_out.getvalue() == """Writing contents to  /tmp/foo
Reading EEPROM from 0 to 15
Dumping to file.
bytes written:16
"""
    print("SERIAL:", result_serial.getvalue())
    assert result_serial.getvalue() == b'R0000\n'