import struct


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
        tmp = decomposed["skeleton"]
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

        tmp["translation"] = tuple(floats[0:3])
        tmp["rotation"] = tuple(floats[3:])

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
        decomposed["fnum"] = tuple((int(x) for x in section[-8:]))
    else:
        raise MalformedDataError()

    # time
    marker = b"time"
    if data.startswith(marker):
        section = data[0 : len(marker) + 8]
        data = data[len(marker) + 8 :]
        decomposed["time"] = int.from_bytes(section[-8:], "little")
    else:
        raise MalformedDataError()

    # uttm
    marker = b"uttm"
    if data.startswith(marker):
        section = data[0 : len(marker) + 12]
        data = data[len(marker) + 12 :]
        decomposed["uttm"] = tuple((int(x) for x in section[-12:]))
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
        decomposed["motion"][id]["translation"] = tuple(floats[0:3])
        decomposed["motion"][id]["rotation"] = tuple(floats[3:])
    return decomposed, data


def decomposePacket(data: bytes):
    headers, data = decomposeHeaderSection(data)

    if checkSkel(data):
        headers["PACKET_TYPE"] = "SKEL"
        skel, data = decomposeHierarcalData(data)
        return headers | skel
    else:
        headers["PACKET_TYPE"] = "POSE"
        motions, data = decomposePoseData(data)
        return headers | motions
