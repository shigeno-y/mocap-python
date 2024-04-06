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

    _FIELDS = "Q"
    _4CC = "ipad"

    def __init__(self, *, size: int, type: str, data: bytes):
        super().__init__(size=size, type=type, data=data)

    def _parseData(self):
        import ipaddress

        self._readRAW()
        self._parsed = self._parsed[0]

        v4 = list(
            (
                0,
                0,
                0,
                0,
            )
        )
        v4[3] = self._parsed % 1000
        self._parsed //= 1000
        v4[2] = self._parsed % 1000
        self._parsed //= 1000
        v4[1] = self._parsed % 1000
        self._parsed //= 1000
        v4[0] = self._parsed % 1000

        self._parsed = ipaddress.IPv4Address(".".join([str(v) for v in v4]))


class rcvp(DataBlock):
    """Recieving Port Box"""

    _FIELDS = "<H"
    _4CC = "rcvp"

    def __init__(self, *, size: int, type: str, data: bytes):
        super().__init__(size=size, type=type, data=data)

    def _parseData(self):
        self._readRAW()
        self._parsed = self._parsed[0]
