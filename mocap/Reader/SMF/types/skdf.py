from .DataBlock import DataBlock


class skdf(DataBlock):
    """Skeleton Definition Box"""

    _FIELDS = "###"
    _4CC = "skdf"

    def __init__(self, *, size: int, type: str, data: bytes):
        super().__init__(size=size, type=type, data=data)

    def _parseData(self):
        super()._parseData()


class bons(DataBlock):
    """Bone Data Array Box"""

    _FIELDS = "###"
    _4CC = "bons"

    def __init__(self, *, size: int, type: str, data: bytes):
        super().__init__(size=size, type=type, data=data)

    def _parseData(self):
        super()._parseData()


class bndt(DataBlock):
    """Bone Data Box"""

    _FIELDS = "###"
    _4CC = "bndt"

    def __init__(self, *, size: int, type: str, data: bytes):
        super().__init__(size=size, type=type, data=data)

    def _parseData(self):
        super()._parseData()


class bnid(DataBlock):
    """Bone ID Box"""

    _FIELDS = "<H"
    _4CC = "bnid"

    def __init__(self, *, size: int, type: str, data: bytes):
        super().__init__(size=size, type=type, data=data)

    def _parseData(self):
        self._readRAW()


class pbid(DataBlock):
    """Parent Bone ID Box"""

    _FIELDS = "<H"
    _4CC = "pbid"

    def __init__(self, *, size: int, type: str, data: bytes):
        super().__init__(size=size, type=type, data=data)

    def _parseData(self):
        self._readRAW()


class tran(DataBlock):
    """Transform Data Box"""

    _FIELDS = "<fffffff"
    _4CC = "tran"

    def __init__(self, *, size: int, type: str, data: bytes):
        super().__init__(size=size, type=type, data=data)

    def _parseData(self):
        self._readRAW()
