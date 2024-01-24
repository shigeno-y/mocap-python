from pathlib import Path
from collections import defaultdict

from pxr import Gf, Usd, UsdSkel
from constants import PMX_COMMON_BONE_NAMES_MOCOPI_MAPPING

PMX_COMMON_BONE_NAMES = PMX_COMMON_BONE_NAMES_MOCOPI_MAPPING.keys()


class TargetCharacter:
    def __init__(self, infile: Path, skelPath: str = None):
        self._stage = Usd.Stage.Open(infile)

        self._skeletonPrim = None
        if skelPath is None:
            for prim in self._stage.Traverse():
                if prim.IsA(UsdSkel.Skeleton):
                    self._skeletonPrim = prim
                    self._skeleton = UsdSkel.Skeleton(prim)
        else:
            prim = self._stage.GetPrimAtPath(skelPath)
            if prim.IsA(UsdSkel.Skeleton):
                self._skeletonPrim = prim
                self._skeleton = UsdSkel.Skeleton(prim)

        if self._skeletonPrim is None:
            raise RuntimeError("No skel")

    def _findMapping(self):
        joints = self._skeleton.GetJointsAttr().Get()
        jpNames = self._skeleton.GetJointNamesAttr().GetCustomDataByKey("usdmmdplugins:originalJP")
        enNames = self._skeleton.GetJointNamesAttr().GetCustomDataByKey("usdmmdplugins:originalEN")
        restTransforms = self._skeleton.GetRestTransformsAttr().Get()

        bones = dict(zip(jpNames, zip(joints, enNames, restTransforms)))

        ret = dict()
        for njp, vv in bones.items():
            j, nen, rt = vv
            if njp in PMX_COMMON_BONE_NAMES_MOCOPI_MAPPING and None not in PMX_COMMON_BONE_NAMES_MOCOPI_MAPPING[njp]:
                ret[j] = PMX_COMMON_BONE_NAMES_MOCOPI_MAPPING[njp]

        return ret


class AnimationReader:
    def __init__(self, infile: Path, animPath: str = None):
        from math import floor, ceil

        self._stage = Usd.Stage.Open(infile)

        self.startTimeCode = floor(self._stage.GetStartTimeCode())
        self.endTimeCode = ceil(self._stage.GetEndTimeCode())

        self._skelanimPrim = None
        if animPath is None:
            for prim in self._stage.Traverse():
                if prim.IsA(UsdSkel.Animation):
                    self._skelanimPrim = prim
                    self._skelanim = UsdSkel.Animation(prim)
        else:
            prim = self._stage.GetPrimAtPath(animPath)
            if prim.IsA(UsdSkel.Skeleton):
                self._skelanimPrim = prim
                self._skelanim = UsdSkel.Skeleton(prim)

        if self._skelanimPrim is None:
            raise RuntimeError("No skelAnim")

    def _collectTransforms(self):
        joints = self._skelanim.GetJointsAttr().Get()

        rattr = self._skelanim.GetRotationsAttr()
        tattr = self._skelanim.GetTranslationsAttr()

        retR = defaultdict(dict)
        retT = defaultdict(dict)

        for t in range(self.startTimeCode, self.endTimeCode + 1):
            rs = rattr.Get(t)
            ts = tattr.Get(t)
            for j, rot, tra in zip(joints, rs, ts):
                j = Path(j).name
                retR[t][j] = rot
                retT[t][j] = tra

        return retR, retT


if __name__ == "__main__":
    animation = AnimationReader("ACTOR_USD")
    rotations, translations = animation._collectTransforms()

    target = TargetCharacter("CHARACTER_USD")
    joints_combinations = target._findMapping()

    news = defaultdict(dict)

    for t in range(animation.startTimeCode, animation.endTimeCode + 1):
        for j, src in joints_combinations.items():
            resultR = Gf.Quatf(1, 0, 0, 0)
            resultT = Gf.Vec3f(0, 0, 0)
            for j in src:
                resultR *= rotations[t][j]
                resultT += translations[t][j]
            news[t][j] = (resultR, resultT)

    #'''
    stage = Usd.Stage.CreateInMemory()
    stage.SetStartTimeCode(animation.startTimeCode)
    stage.SetEndTimeCode(animation.endTimeCode)

    animPrim = UsdSkel.Animation.Define(stage, "/Motion")
    stage.SetDefaultPrim(animPrim.GetPrim())

    animPrim.CreateJointsAttr().Set(list(joints_combinations.keys()))
    rotationsAttr = animPrim.CreateRotationsAttr()
    translationsAttr = animPrim.CreateTranslationsAttr()
    animPrim.CreateScalesAttr().Set(
        [
            Gf.Vec3h(1, 1, 1),
        ]
        * len(joints_combinations.keys())
    )

    for time, poses in sorted(news.items()):
        rotation_series = list()
        translation_series = list()

        for joint, pose in poses.items():
            r, t = pose
            rotation_series.append(r)
            translation_series.append(t)

        rotationsAttr.Set(rotation_series, time)
        translationsAttr.Set(translation_series, time)

    layer = stage.GetEditTarget().GetLayer()
    layer.TransferContent(stage.GetRootLayer())
    layer.Export("test.usda")
