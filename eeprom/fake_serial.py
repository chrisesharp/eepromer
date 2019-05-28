class Serial:
    def __init__( self, port=None, baudrate = 19200, timeout=1,
                  bytesize = 8, parity = 'N', stopbits = 1, xonxoff=0,
                  rtscts = 0):
        print("Port is ", port)
        self.halfduplex = True
        self.name     = port
        self.port     = port
        self.timeout  = timeout
        self.parity   = parity
        self.baudrate = baudrate
        self.bytesize = bytesize
        self.stopbits = stopbits
        self.xonxoff  = xonxoff
        self.rtscts   = rtscts
        self._data = b'0000:FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF,00\r\n'
        if isinstance(self.port, str):
            self.port = open(self.port, "wb+")

    def close(self):
        pass
    
    def flush(self):
        self.port.flush()

    def write(self, data):
        written = self.port.write(data)
        return written

    def readline(self):
        self.halfduplex = not self.halfduplex
        if self.halfduplex:
            return b"OK\r\n"
        return self._data