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
                "rotation": list(floats[0:4]),
                "translation": list(floats[4:]),
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


class MalformedDataError(Exception):
    pass


def decomposeHeaderSection(data: bytes):
    decomposed = dict()
    # init marker
    marker = b"#\x00\x00\x00"
    if data.startswith(marker):
        section = data[0 : len(marker)]
        data = data[len(marker) :]
    else:
        raise MalformedDataError()

    # head marker
    marker = b"head\x12\x00\x00\x00ftyp"
    if data.startswith(marker):
        section = data[0 : len(marker)]
        data = data[len(marker) :]
    else:
        raise MalformedDataError()

    # sony motion format version
    marker = b"sony motion format"
    if data.startswith(marker):
        section = data[0 : len(marker) + 4]
        data = data[len(marker) + 4 :]
        decomposed["SMF_version"] = tuple((int(x) for x in section[-4:]))
    else:
        raise MalformedDataError()

    # version
    marker = b"vrsn"
    if data.startswith(marker):
        section = data[0 : len(marker) + 5]
        data = data[len(marker) + 5 :]
        decomposed["version"] = tuple((int(x) for x in section[-5:]))
    else:
        raise MalformedDataError()

    # sndf
    marker = b"sndf"
    if data.startswith(marker):
        section = data[0 : len(marker) + 4]
        data = data[len(marker) + 4 :]
        decomposed["sndf"] = tuple((int(x) for x in section[-4:]))
    else:
        raise MalformedDataError()

    # ipad
    marker = b"ipad"
    if data.startswith(marker):
        section = data[0 : len(marker) + 12]
        data = data[len(marker) + 12 :]
        decomposed["ipad"] = tuple((int(x) for x in section[-12:]))
    else:
        raise MalformedDataError()

    # rcvp?0
    marker = b"rcvp?0"
    if data.startswith(marker):
        section = data[0 : len(marker) + 4]
        data = data[len(marker) + 4 :]
        decomposed["rcvp?0"] = tuple((int(x) for x in section[-4:]))
    else:
        raise MalformedDataError()

    return decomposed, data


def checkSkel(data: bytes):
    return data.startswith(b"skdf")


def decomposeHierarcalData(data: bytes):
    decomposed = dict()

    # skdf
    marker = b"skdf"
    if data.startswith(marker):
        section = data[0 : len(marker) + 4]
        data = data[len(marker) + 4 :]
        decomposed["skdf"] = tuple((int(x) for x in section[-4:]))
    else:
        raise MalformedDataError()

    # bons
    marker = b"bons"
    if data.startswith(marker):
        section = data[0 : len(marker) + 4]
        data = data[len(marker) + 4 :]
        decomposed["bons"] = tuple((int(x) for x in section[-4:]))
    else:
        raise MalformedDataError()

    # skeleton data
    decomposed["skeleton"] = dict()
    bones = filter(lambda x: len(x) > 0, data.split(b"bndt"))

    for dat in bones:
        tmp = dict()
        dat = dat[4:]

        # bnid
        marker = b"bnid"
        if dat.startswith(marker):
            section = dat[0 : len(marker) + 2]
            dat = dat[len(marker) + 2 :]
            tmp["id"] = int.from_bytes(section[-2:], "little")
            # unk0 = dat[0:4]
            dat = dat[4:]
        else:
            raise MalformedDataError()

        # pbid
        marker = b"pbid"
        if dat.startswith(marker):
            section = dat[0 : len(marker) + 2]
            dat = dat[len(marker) + 2 :]
            tmp["parent_id"] = int.from_bytes(section[-2:], "little")
            # unk0 = dat[0:4]
            dat = dat[4:]
        else:
            raise MalformedDataError()

        # tran = dat[0:4]
        dat = dat[4:]

        floats = struct.unpack("<fffffff", dat[0:28])

        tmp["translation"] = tuple(floats[4:])
        tmp["rotation"] = tuple(floats[0:4])

        decomposed["skeleton"][tmp["id"]] = tmp
    return decomposed, data


def decomposePoseData(data: bytes):
    decomposed = dict()

    # pose header
    # fram
    marker = b"fram"
    if data.startswith(marker):
        section = data[0 : len(marker) + 4]
        data = data[len(marker) + 4 :]
        decomposed["fram"] = tuple((int(x) for x in section[-4:]))
    else:
        raise MalformedDataError()

    # fnum
    marker = b"fnum"
    if data.startswith(marker):
        section = data[0 : len(marker) + 8]
        data = data[len(marker) + 8 :]
        decomposed["fnum"] = struct.unpack("<i", section[-8:-4])[0]
    else:
        raise MalformedDataError()

    # time
    marker = b"time"
    if data.startswith(marker):
        section = data[0 : len(marker) + 8]
        data = data[len(marker) + 8 :]
        decomposed["time"] = struct.unpack("<f", section[-8:-4])[0]
    else:
        raise MalformedDataError()

    # uttm
    marker = b"uttm"
    if data.startswith(marker):
        section = data[0 : len(marker) + 12]
        data = data[len(marker) + 12 :]
        decomposed["uttm"] = struct.unpack("<d", section[-12:-4])[0]
    else:
        raise MalformedDataError()

    # btrs
    marker = b"btrs"
    if data.startswith(marker):
        section = data[0 : len(marker) + 4]
        data = data[len(marker) + 4 :]
        decomposed["btrs"] = tuple((int(x) for x in section[-4:]))
    else:
        raise MalformedDataError()

    # btdt
    marker = b"btdt"
    if data.startswith(marker):
        section = data[0 : len(marker) + 4]
        data = data[len(marker) + 4 :]
        decomposed["btdt"] = tuple((int(x) for x in section[-4:]))
    else:
        raise MalformedDataError()

    # pose data
    decomposed["motion"] = dict()
    bones = filter(lambda x: len(x) > 0, data.split(b"bnid"))

    for dat in bones:
        id = int.from_bytes(dat[0:1], "little")
        dat = dat[2:]

        # unk0 = dat[0:4]
        dat = dat[4:]

        # tran = dat[0:4]
        dat = dat[4:]

        floats = struct.unpack("<fffffff", dat[0:28])

        decomposed["motion"][id] = dict()
        decomposed["motion"][id]["rotation"] = tuple(floats[0:4])
        decomposed["motion"][id]["translation"] = tuple(floats[4:])

    return decomposed, data


def decomposePacket(data: bytes) -> dict:
    # from pprint import pprint
    mocoPacket = MocopiPacket(data)
    # pprint(mocoPacket.getData())

    """
    headers, data = decomposeHeaderSection(data)

    if checkSkel(data):
        headers["PACKET_TYPE"] = "SKEL"
        skel, data = decomposeHierarcalData(data)
        return headers | skel
    else:
        headers["PACKET_TYPE"] = "POSE"
        motions, data = decomposePoseData(data)
        return headers | motions
    #"""

    return mocoPacket.getData()
