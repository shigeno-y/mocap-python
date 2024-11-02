from .DataBlock import DataBlock


class fram(DataBlock):
    """Frame Data Box"""

    _FIELDS = "###"
    _4CC = "fram"

    def __init__(self, *, size: int, type: str, data: bytes):
        super().__init__(size=size, type=type, data=data)

    def _parseData(self):
        super()._parseData()


class fnum(DataBlock):
    """Frame Number Box"""

    _FIELDS = "<I"
    _4CC = "fnum"

    def __init__(self, *, size: int, type: str, data: bytes):
        super().__init__(size=size, type=type, data=data)

    def __int__(self):
        return int(self._parsed)

    def _parseData(self):
        self._readRAW()
        self._parsed = self._parsed[0]


class time(DataBlock):
    """Timestamp Box"""

    _FIELDS = "<f"
    _4CC = "time"

    def __init__(self, *, size: int, type: str, data: bytes):
        super().__init__(size=size, type=type, data=data)

    def _parseData(self):
        self._readRAW()
        self._parsed = self._parsed[0]


class tmcd(DataBlock):
    """UNKNOWN FIELD"""

    _FIELDS = "<cccccc"
    _4CC = "tmcd"

    def __init__(self, *, size: int, type: str, data: bytes):
        super().__init__(size=size, type=type, data=data)

    def _parseData(self):
        self._readRAW()
        self._parsed = self._parsed[0]

        self._parsed = list(self._parsed)


class uttm(DataBlock):
    """UTC Timestamp Box"""

    _FIELDS = "<d"
    _4CC = "uttm"

    def __init__(self, *, size: int, type: str, data: bytes):
        super().__init__(size=size, type=type, data=data)

    def _parseData(self):
        import datetime

        self._readRAW()
        self._parsed = self._parsed[0]

        self._parsed = datetime.datetime.fromtimestamp(self._parsed, datetime.timezone.utc)


class btrs(DataBlock):
    """Bone Transform Data Array Box"""

    _FIELDS = "###"
    _4CC = "btrs"

    def __init__(self, *, size: int, type: str, data: bytes):
        super().__init__(size=size, type=type, data=data)

    def _parseData(self):
        super()._parseData()


class btdt(DataBlock):
    """Bone Transform Data Box"""

    _FIELDS = "###"
    _4CC = "btdt"

    def __init__(self, *, size: int, type: str, data: bytes):
        super().__init__(size=size, type=type, data=data)

    def _parseData(self):
        super()._parseData()
