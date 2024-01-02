from collections import OrderedDict

from pxr import Gf, Usd, UsdSkel
from .skelTree import SkelNode


def hierarchy(skelAnim, skeleton: dict):
    # build skeleton
    skel = None
    for idx, s in sorted(skeleton.items(), key=lambda x: x[0]):
        if idx == 0:
            skel = SkelNode(s["id"], s["rotation"], s["translation"], s["parent_id"])
        else:
            skel.append(SkelNode(s["id"], s["rotation"], s["translation"], s["parent_id"]))

    # set joints
    jointNames = OrderedDict()

    def names(s):
        jointNames[s.id] = s.fullPath()
        for c in s.children:
            names(c)

    names(skel)
    skelAnim.GetJointsAttr().Set(list(jointNames.values()))
    return jointNames


def motion(layer, skelAnim, jointNames: OrderedDict, timesamples: dict):
    rotationTimesamplesAttrPath = skelAnim.GetPath().AppendProperty(UsdSkel.Tokens.rotations)
    translationTimesamplesAttrPath = skelAnim.GetPath().AppendProperty(UsdSkel.Tokens.translations)

    very_first = True
    for time, poses in sorted(timesamples.items()):
        rotation_series = list()
        translation_series = list()
        for id in jointNames:
            pose = poses[id]
            r = pose["rotation"]
            t = pose["translation"]

            rotation_series.append(Gf.Quatf(r[3], r[0], r[1], r[2]))
            translation_series.append(Gf.Vec3f(*t))

        if very_first:
            very_first = False
            skelAnim.GetRotationsAttr().Set(rotation_series)
            skelAnim.GetTranslationsAttr().Set(translation_series)
        layer.SetTimeSample(rotationTimesamplesAttrPath, time, rotation_series)
        layer.SetTimeSample(translationTimesamplesAttrPath, time, translation_series)


def Write(file, skeleton: SkelNode, timesamples: dict, *, secondsPerFrame=0.02, decomposeAxises=SkelNode.ZXY):  # 50 Hz
    from pathlib import Path

    stage = Usd.Stage.CreateInMemory()
    layer = stage.GetEditTarget().GetLayer()
    prim = stage.DefinePrim("/Mocopi")
    stage.SetDefaultPrim(prim)

    skelAnim = UsdSkel.Animation.Define(stage, prim.GetPath().AppendChild("SkelAnim"))

    jointNames = hierarchy(skelAnim, skeleton)
    motion(layer, skelAnim, jointNames, timesamples)

    layer.TransferContent(stage.GetRootLayer())
    layer.Export(Path(file).with_suffix(".usda").as_posix())

    #
    # motion(file, timesamples,secondsPerFrame=secondsPerFrame, decomposeAxises=decomposeAxises)
