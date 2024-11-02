import struct
from collections import defaultdict


class DataBlock:
    """interface"""

    _FIELDS = "###"
    _4CC = "none"

    def __init__(self, *, size: int, type: str, data: bytes):
        self._size = size
        self._type = type
        self._data = data

        self._parsed = defaultdict(list)
        self.__types = dict()

    def __contains__(self, item):
        if isinstance(self._parsed, dict) or isinstance(self._parsed, list):
            return item in self._parsed
        else:
            return False

    def __getitem__(self, key):
        if key not in self:
            print(f"<{key}> is not in {self._4CC}")
            raise KeyError

        return self._parsed[key][0]

    def __import_type(self, type: str):
        import importlib

        for m in [
            ".fram",
            ".head",
            ".skdf",
            ".sndf",
            ".sndt",
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
            self._parsed[newBlock._type].append(newBlock)
            offset += param["size"]

    def _readRAW(self):
        self._parsed = struct.unpack(type(self)._FIELDS, self._data)

    def _dumpData(self, indent: int = 0):
        i = "  " * indent

        print(i, type(self)._4CC, " ", self._size, " ", len(self._data), sep="")
        if isinstance(self._parsed, dict):
            for t, v in self._parsed.items():
                print(i, t, "...", sep="")
                if isinstance(v, DataBlock):
                    v._dumpData(indent + 1)
                elif isinstance(v, list):
                    for vv in v:
                        vv._dumpData(indent + 1)
                else:
                    print(i, v)
        else:
            print(i, self._parsed, sep="")


def decomposePacket(rawData: bytes):
    data = DataBlock(size=len(rawData), type="RAW", data=rawData)
    data._parseData()
    return data
