from pathlib import Path
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


def motion(baseDir: Path, animPrim, joints: OrderedDict, timesamples: dict):
    animPrim.GetJointsAttr().Set(list(joints.values()))

    pattern = (baseDir / "clip.#.usda").as_posix()
    stride = 60
    manifestFile = (baseDir / "manifest.usda").as_posix()

    valueclip = Usd.ClipsAPI(animPrim)
    valueclip.SetClipPrimPath("/Motion")
    valueclip.SetClipManifestAssetPath(manifestFile)
    valueclip.SetClipTemplateAssetPath(pattern)
    valueclip.SetClipTemplateStartTime(min(timesamples.keys()))
    valueclip.SetClipTemplateEndTime(max(timesamples.keys()))
    valueclip.SetClipTemplateStride(stride)

    generateManifest(manifestFile)
    splitMotion(pattern, joints, timesamples, stride)


def generateManifest(file: str):
    stage = Usd.Stage.CreateInMemory()

    animPrim = UsdSkel.Animation.Define(stage, "/Motion")
    animPrim.CreateRotationsAttr()
    animPrim.CreateTranslationsAttr()

    layer = stage.GetEditTarget().GetLayer()
    layer.TransferContent(stage.GetRootLayer())
    layer.Export(file)


def splitMotion(pattern: str, joints: OrderedDict, timesamples: dict, stride):
    from collections import defaultdict
    from functools import reduce

    def splitter(acc, item):
        acc[(item[0] // stride) * stride][item[0]] = item[1]
        return acc

    clips = reduce(splitter, timesamples.items(), defaultdict(dict))
    for base, ts in clips.items():
        file = Path(pattern.replace("#", str(base))).as_posix()
        saveValueClip(file, joints, ts)


def saveValueClip(file: str, joints: OrderedDict, timesamples: dict):
    timecodes = timesamples.keys()

    stage = Usd.Stage.CreateInMemory()
    stage.SetStartTimeCode(min(timecodes))
    stage.SetEndTimeCode(max(timecodes))

    animPrim = UsdSkel.Animation.Define(stage, "/Motion")
    stage.SetDefaultPrim(animPrim.GetPrim())

    rotationsAttr = animPrim.CreateRotationsAttr()
    translationsAttr = animPrim.CreateTranslationsAttr()

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

        rotationsAttr.Set(rotation_series, time)
        translationsAttr.Set(translation_series, time)

    layer = stage.GetEditTarget().GetLayer()
    layer.TransferContent(stage.GetRootLayer())
    layer.Export(file)


def Write(file, skeleton: list, timesamples: dict, *, secondsPerFrame=0.02, decomposeAxises=SkelNode.ZXY):
    baseDir = Path(file)
    baseDir.mkdir(exist_ok=True)

    stage = Usd.Stage.CreateInMemory()
    layer = stage.GetEditTarget().GetLayer()
    skelRoot = UsdSkel.Root.Define(stage, "/Mocopi")
    stage.SetDefaultPrim(skelRoot.GetPrim())

    timecodes = timesamples.keys()

    stage.SetStartTimeCode(min(timecodes))
    stage.SetEndTimeCode(max(timecodes))

    Skel = UsdSkel.Skeleton.Define(stage, skelRoot.GetPath().AppendChild("skeleton"))
    joints = hierarchy(Skel, skeleton)

    animPrim = UsdSkel.Animation.Define(stage, skelRoot.GetPath().AppendChild("Motion"))
    motion(baseDir, animPrim, joints, timesamples)
    animPrim.GetScalesAttr().Set(
        [
            Gf.Vec3h(1, 1, 1),
        ]
        * len(joints)
    )

    layer.TransferContent(stage.GetRootLayer())
    layer.Export((baseDir / "main.usda").as_posix())
