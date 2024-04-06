from .DataBlock import DataBlock


class sndt(DataBlock):
    """Sensor Data"""

    _FIELDS = "###"
    _4CC = "sndt"

    def __init__(self, *, size: int, type: str, data: bytes):
        super().__init__(size=size, type=type, data=data)

    def _parseData(self):
        super()._parseData()


class snad(DataBlock):
    """Sensor Address"""

    _FIELDS = "s"
    _4CC = "snad"

    def __init__(self, *, size: int, type: str, data: bytes):
        super().__init__(size=size, type=type, data=data)

    def _parseData(self):
        self._parsed = self._data.decode("ascii")


class snnm(DataBlock):
    """Sensor Name"""

    _FIELDS = "s"
    _4CC = "snnm"

    def __init__(self, *, size: int, type: str, data: bytes):
        super().__init__(size=size, type=type, data=data)

    def _parseData(self):
        self._parsed = self._data.decode("ascii")


class snji(DataBlock):
    """Sensor Joint ID"""

    _FIELDS = "<I"
    _4CC = "snji"

    def __init__(self, *, size: int, type: str, data: bytes):
        super().__init__(size=size, type=type, data=data)

    def _parseData(self):
        self._readRAW()
        self._parsed = self._parsed[0]


class snvl(DataBlock):
    """Sensor Value"""

    _FIELDS = "<fffffff"
    _4CC = "snvl"

    def __init__(self, *, size: int, type: str, data: bytes):
        super().__init__(size=size, type=type, data=data)

    def _parseData(self):
        self._readRAW()
        # self._parsed = self._parsed[0]
        self._parsed = {
            "quatX": self._parsed[0],
            "quatY": self._parsed[1],
            "quatZ": self._parsed[2],
            "quatW": self._parsed[3],
            "tranX": self._parsed[4],
            "tranY": self._parsed[5],
            "tranZ": self._parsed[6],
        }
