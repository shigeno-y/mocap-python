from .DataBlock import DataBlock


class sndf(DataBlock):
    """Sender Definition Box"""

    _FIELDS = "###"
    _4CC = "sndf"

    def __init__(self, *, size: int, type: str, data: bytes):
        super().__init__(size=size, type=type, data=data)

    def _parseData(self):
        super()._parseData()


class ipad(DataBlock):
    """IP Address Box"""

    _FIELDS = "II"
    _4CC = "ipad"

    def __init__(self, *, size: int, type: str, data: bytes):
        super().__init__(size=size, type=type, data=data)

    def _parseData(self):
        import ipaddress

        self._readRAW()

        self._parsed = ipaddress.ip_address(self._parsed)


class rcvp(DataBlock):
    """Recieving Port Box"""

    _FIELDS = "<H"
    _4CC = "rcvp"

    def __init__(self, *, size: int, type: str, data: bytes):
        super().__init__(size=size, type=type, data=data)

    def _parseData(self):
        self._readRAW()
