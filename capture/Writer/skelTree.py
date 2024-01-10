from pxr import Gf

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

MAT44_IDENTITY = Gf.Matrix4d(1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1)


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
        self.id = int(id)
        self.rotation = rotation
        self.translation = translation
        self.parent = int(parent)
        self.global_to_self_transform = Gf.Matrix4d(
            1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, self.translation[0], self.translation[1], self.translation[1], 1
        )
        self.restTransform = Gf.Matrix4d()
        self.children = list()
        self.__parentPath = ""

    def __updateTransform(self, globalToParent):
        self.global_to_self_transform += globalToParent - MAT44_IDENTITY
        self.restTransform = self.global_to_self_transform * globalToParent.GetInverse()

    def size(self):
        val = 1
        for c in self.children.values():
            val += c.size()
        return val

    def append(self, target, parentPath=""):
        if self.id == target.parent:
            target.__parentPath = self.fullPath()
            target.__updateTransform(self.global_to_self_transform)
            self.children.append(target)
            return True
        else:
            for c in self.children:
                ret = c.append(target)
                if ret:
                    return True
        return False

    def name(self):
        if self.id in MOCOPI_SKEL_NAMES:
            return MOCOPI_SKEL_NAMES[self.id]
        return f"skel_{self.id}"

    def fullPath(self):
        return self.__parentPath + "/" + self.name()


__all__ = ["SkelNode"]
