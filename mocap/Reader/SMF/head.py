from .DataBlock import DataBlock


class head(DataBlock):
    """Header Box"""

    _FIELDS = "###"
    _4CC = "head"

    def __init__(self, *, size: int, type: str, data: bytes):
        super().__init__(size=size, type=type, data=data)

    def _parseData(self):
        super()._parseData()


class ftyp(DataBlock):
    """Format Type Box"""

    _FIELDS = "s"
    _4CC = "ftyp"

    def __init__(self, *, size: int, type: str, data: bytes):
        super().__init__(size=size, type=type, data=data)

    def _parseData(self):
        self._parsed = self._data.decode("ascii")


class vrsn(DataBlock):
    """Version Box"""

    _FIELDS = "b"
    _4CC = "vrsn"

    def __init__(self, *, size: int, type: str, data: bytes):
        super().__init__(size=size, type=type, data=data)

    def _parseData(self):
        self._readRAW()
        self._parsed = self._parsed[0]
