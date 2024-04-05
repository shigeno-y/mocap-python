import struct


class DataBlock:
    """interface"""

    _FIELDS = "###"
    _4CC = "none"

    def __init__(self, *, size: int, type: str, data: bytes):
        self._size = size
        self._type = type
        self._data = data

        self._parsed = dict()
        self.__types = dict()

    def __import_type(self, type: str):
        import importlib

        for m in [
            ".fram",
            ".head",
            ".skdf",
            ".sndf",
        ]:
            mod = importlib.import_module(m, __package__)
            try:
                self.__types[type] = getattr(mod, type)
                return
            except AttributeError:
                pass

        raise RuntimeError(f"Unknown Type <{type}>found")

    def _parseData(self):
        offset = 0
        while offset < len(self._data):
            param = dict()
            param["size"] = struct.unpack("<L", self._data[offset : offset + 4])[0]
            offset += 4

            param["type"] = self._data[offset : offset + 4].decode("ascii")
            offset += 4

            param["data"] = self._data[offset : offset + param["size"]]

            if param["type"] not in self.__types:
                self.__import_type(param["type"])

            newBlock = self.__types[param["type"]](**param)
            newBlock._parseData()
            self._parsed[newBlock._type] = newBlock
            offset += param["size"]

    def _readRAW(self):
        self._parsed = struct.unpack(type(self)._FIELDS, self._data)[0]

    def _dumpData(self, indent: int = 0):
        i = "  " * indent

        print(i, type(self)._4CC, sep="")
        if isinstance(self._parsed, dict):
            for t, v in self._parsed.items():
                print(i, t, "...", sep="")
                v._dumpData(indent + 1)
        else:
            print(i, self._parsed, sep="")


"""
from .fram import fnum, time, btrs, btdt
from .head import head, ftyp, vrsn
from .skdf import skdf, bons, bndt, bnid, pbid, tran
from .sndf import sndf, ipad, rcvp

_4CC_CLASS_MAP = {
    "fnum": fnum,
    "time": time,
    "btrs": btrs,
    "btdt": btdt,
    "head": head,
    "ftyp": ftyp,
    "vrsn": vrsn,
    "skdf": skdf,
    "bons": bons,
    "bndt": bndt,
    "bnid": bnid,
    "pbid": pbid,
    "tran": tran,
    "sndf": sndf,
    "ipad": ipad,
    "rcvp": rcvp,
}
"""
