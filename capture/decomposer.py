import struct

FIELDS_RECURSIVE = [
    #
    "head",
    #
    "sndf",
    #
    "skdf",
    "bons",
    "bndt",
    #
    "fram",
    "btrs",
    "btdt",
]

FIELDS_PROMOTE = [
    #
    "ftyp",
    "vrsn",
    "fnum",
    "time",
    "uttm",
    "ipad",
    "rcvp",
    "bnid",
    "pbid",
    "tran",
]

FIELDS_DATATYPES = {
    # "head",
    # "ftyp": "s",
    "vrsn": "b",
    # "sndf",
    "ipad": "II",
    "rcvp": "<H",
    # "sdkf",
    # "bons",
    # "bndt",
    "bnid": "<H",
    "pbid": "<H",
    ##"tran": "<fffffff",
    # "fram",
    "fnum": "<I",
    "time": "<f",
    "uttm": "<d",
    # "btrs",
    # "btdt",
    ##"bnid": "<H",
    ##"pbid": "<H",
}


def parse_field_(data: bytes):
    offset = 0
    ret = list()
    while offset < len(data):
        f = dict()
        f["length"] = struct.unpack("<L", data[offset : offset + 4])[0]
        offset += 4

        f["name"] = data[offset : offset + 4].decode("ascii")
        offset += 4

        f["raw"] = data[offset : offset + f["length"]]
        if f["name"] in FIELDS_RECURSIVE:
            children, _ = parse_field_(f["raw"])
            to_be_added_children = list()
            for child in children:
                if child["name"] in FIELDS_PROMOTE:
                    f[child["name"]] = child["data"]
                else:
                    to_be_added_children.append(child)

            if len(to_be_added_children) > 0:
                f["children"] = to_be_added_children

        if f["name"] in FIELDS_DATATYPES:
            f["data"] = struct.unpack(FIELDS_DATATYPES[f["name"]], f["raw"])[0]
        elif f["name"] == "ftyp":
            f["data"] = f["raw"].decode("ascii")
        elif f["name"] == "tran":
            floats = struct.unpack("<fffffff", f["raw"])
            f["data"] = {
                "rotation": floats[0:4],
                "translation": floats[4:],
            }
        elif f["name"] in ["fram", "skdf"] and len(f["children"]) == 1:
            c = f["children"][0]
            if c["name"] in ["btrs", "bons"]:
                f["btrs"] = c["children"]
                del f["children"]

        offset += f["length"]
        ret.append(f)

    for f in ret:
        if "children" in f and len(f["children"]) == 0:
            del f["children"]
        del f["length"], f["raw"]

    return ret, offset


class MocopiPacket:
    def __init__(self, data: bytes):
        self.fields_ = dict()
        self.data_ = data
        self.__parse()

    def __parse(self):
        read_counter = 0
        while read_counter < len(self.data_):
            l, c = parse_field_(self.data_[read_counter:])
            read_counter += c
            for f in l:
                self.fields_[f["name"]] = f

    def getData(self):
        return self.fields_

    def isMotion(self):
        return "fram" in self.fields_

    def isSkel(self):
        return "sdkf" in self.fields_


def decomposePacket(data: bytes) -> dict:
    mocoPacket = MocopiPacket(data)
    return mocoPacket.getData()
