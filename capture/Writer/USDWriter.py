from collections import OrderedDict

from pxr import Gf, Usd, UsdSkel
from .skelTree import SkelNode


def hierarchy(skelPrim, skeleton: list):
    skel = None
    for s in sorted(skeleton, key=lambda x: x["bnid"]):
        if skel is None:
            skel = SkelNode(s["bnid"], s["tran"]["rotation"], s["tran"]["translation"], s["pbid"])
            skel.global_to_self_transform = Gf.Matrix4d(
                1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, skel.translation[0], skel.translation[1], skel.translation[1], 1
            )
        else:
            skel.append(SkelNode(s["bnid"], s["tran"]["rotation"], s["tran"]["translation"], s["pbid"]))

    joints = OrderedDict()

    def BuildJoints(s):
        joints[s.id] = s.fullPath()
        for c in s.children:
            BuildJoints(c)

    BuildJoints(skel)
    # skelPrim.GetJointsAttr().Set(list(joints.values()))

    jointNames = OrderedDict()

    def BuildJointNames(s):
        jointNames[s.id] = s.name()
        for c in s.children:
            BuildJointNames(c)

    BuildJointNames(skel)
    # skelPrim.GetJointNamesAttr().Set(list(jointNames.values()))

    restTransForms = OrderedDict()

    def BuildRests(s):
        restTransForms[s.id] = s.restTransform
        for c in s.children:
            BuildRests(c)

    BuildRests(skel)
    # skelPrim.GetRestTransformsAttr().Set(list(restTransForms.values()))
    return joints


def motion(layer, animPrim, joints: OrderedDict, timesamples: dict):
    rotationTimesamplesAttrPath = animPrim.GetPath().AppendProperty(UsdSkel.Tokens.rotations)
    translationTimesamplesAttrPath = animPrim.GetPath().AppendProperty(UsdSkel.Tokens.translations)

    animPrim.GetJointsAttr().Set(list(joints.values()))

    very_first = True
    for time, poses in sorted(timesamples.items()):
        ordered_poses = sorted(poses["btrs"], key=lambda x: x["bnid"])
        rotation_series = list()
        translation_series = list()
        for id in joints:
            pose = ordered_poses[id]
            r = pose["tran"]["rotation"]
            t = pose["tran"]["translation"]

            rotation_series.append(Gf.Quatf(r[3], r[0], r[1], r[2]))
            translation_series.append(Gf.Vec3f(*t) * 100)

        if very_first:
            very_first = False
            animPrim.GetRotationsAttr().Set(rotation_series)
            animPrim.GetTranslationsAttr().Set(translation_series)
        layer.SetTimeSample(rotationTimesamplesAttrPath, time, rotation_series)
        layer.SetTimeSample(translationTimesamplesAttrPath, time, translation_series)


def Write(file, skeleton: list, timesamples: dict, *, secondsPerFrame=0.02, decomposeAxises=SkelNode.ZXY):
    from pathlib import Path

    stage = Usd.Stage.CreateInMemory()
    layer = stage.GetEditTarget().GetLayer()
    skelRoot = UsdSkel.Root.Define(stage, "/Mocopi")
    stage.SetDefaultPrim(skelRoot.GetPrim())

    stage.SetStartTimeCode(min(timesamples.keys()))
    stage.SetEndTimeCode(max(timesamples.keys()))

    Skel = UsdSkel.Skeleton.Define(stage, skelRoot.GetPath().AppendChild("skeleton"))
    joints = hierarchy(Skel, skeleton)

    animPrim = UsdSkel.Animation.Define(stage, skelRoot.GetPath().AppendChild("Motion"))
    motion(layer, animPrim, joints, timesamples)
    animPrim.GetScalesAttr().Set(
        [
            Gf.Vec3h(1, 1, 1),
        ]
        * len(joints)
    )

    layer.TransferContent(stage.GetRootLayer())
    layer.Export(Path(file).with_suffix(".usda").as_posix())
