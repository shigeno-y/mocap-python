def Name(skel):
    MOCOPI_SKEL_NAMES = {
        0: "root",
        1: "torso_1",
        2: "torso_2",
        3: "torso_3",
        4: "torso_4",
        5: "torso_5",
        6: "torso_6",
        7: "torso_7",
        8: "neck_1",
        9: "neck_2",
        10: "head",
        11: "l_shoulder",
        12: "l_up_arm",
        13: "l_low_arm",
        14: "l_hand",
        15: "r_shoulder",
        16: "r_up_arm",
        17: "r_low_arm",
        18: "r_hand",
        19: "l_up_leg",
        20: "l_low_leg",
        21: "l_foot",
        22: "l_toes",
        23: "r_up_leg",
        24: "r_low_leg",
        25: "r_foot",
        26: "r_toes",
    }
    if skel._id in MOCOPI_SKEL_NAMES:
        return MOCOPI_SKEL_NAMES[skel._id]
    return f"skel_{skel._id}"


def Specifier(skel):
    return "ROOT" if skel._parent == 65535 else "JOINT"


class SkelNode:
    XYZ = (
        (
            (1, 0, 0),
            (0, 1, 0),
            (0, 0, 1),
        ),
        "Xrotation Yrotation Zrotation",
    )
    ZXY = (
        (
            (0, 0, 1),
            (1, 0, 0),
            (0, 1, 0),
        ),
        "Zrotation Xrotation Yrotation",
    )
    YZX = (
        (
            (0, 1, 0),
            (0, 0, 1),
            (1, 0, 0),
        ),
        "Yrotation Zrotation Xrotation",
    )

    def __init__(self, id, rotation, translation, parent):
        self._id = int(id)
        self._rotation = rotation
        self._translation = translation
        self._parent = int(parent)
        self._children = list()

    def size(self):
        val = 1
        for c in self._children.values():
            val += c.size()
        return val

    def append(self, target):
        if self._id == target._parent:
            self._children.append(target)
            return True
        else:
            for c in self._children:
                ret = c.append(target)
                if ret:
                    return True
        return False

    def dump(self, file, indent=0, decomposeAxises=ZXY):
        indentPrefix = "  " * indent
        if indent == 0:
            print("HIERARCHY", file=file)
        print(indentPrefix, Specifier(self), " ", Name(self), sep="", file=file)
        print(indentPrefix, "{", sep="", file=file)

        print(indentPrefix, "OFFSET {} {} {}".format(*(self._translation)), sep="", file=file)
        print(
            indentPrefix, "CHANNELS 6 Xposition Yposition Zposition {}".format(decomposeAxises[1]), sep="", file=file
        )

        for c in self._children:
            c.dump(file, indent + 1, decomposeAxises)
        print(indentPrefix, "}", sep="", file=file)
