from pathlib import Path
from collections import defaultdict, OrderedDict
import multiprocessing

from pxr import Gf, Usd, UsdSkel
from .skelTree import SkelNode


class USDWriter:
    def __init__(
        self,
        mainFileBasename: str,
        *,
        stride: int = 600,
        framesPerSecond=60,
        clipPattern="clip.#.usd",
        output_base=None,
        **kwargs
    ):
        self.__baseDir = Path(mainFileBasename)
        if output_base is not None:
            self.__baseDir = Path(output_base) / self.__baseDir.name
        self.__baseDir.absolute().mkdir(parents=True, exist_ok=True)
        self.__mainFile = Path(self.__baseDir.as_posix() + ".usda")

        self.__stride = stride
        self.fps_ = framesPerSecond
        self.pattern_ = self.__baseDir / clipPattern

        # self.skeleton_ = None
        self.joints_ = None
        self.jointNames_ = None
        self.restTransforms_ = None

        self.timesamples_ = defaultdict(dict)
        self.initialFrame_ = None
        self.lastFrame_ = -1
        self.__writeAnimationThreads = list()

    def close(self):
        # generate manifest file
        manifestFile = self.__baseDir / "manifest.usda"
        generateManifest(manifestFile.as_posix())

        # generate main file
        stage = Usd.Stage.CreateInMemory()
        layer = stage.GetEditTarget().GetLayer()
        skelRoot = UsdSkel.Root.Define(stage, "/Skel")
        stage.SetDefaultPrim(skelRoot.GetPrim())

        skeleton = UsdSkel.Skeleton.Define(stage, skelRoot.GetPath().AppendChild("Skeleton"))
        animPrim = UsdSkel.Animation.Define(stage, skelRoot.GetPath().AppendChild("Motion"))

        stage.SetFramesPerSecond(self.fps_)
        stage.SetStartTimeCode(0)
        stage.SetEndTimeCode(self.lastFrame_)

        default_transforms = list(self.restTransforms_.values())
        skeleton.CreateBindTransformsAttr().Set(default_transforms)
        skeleton.CreateRestTransformsAttr().Set(default_transforms)
        skeleton.CreateJointsAttr().Set(list(self.joints_.values()))
        skeleton.GetPrim().GetRelationship("skel:animationSource").SetTargets([animPrim.GetPath()])

        animPrim.CreateJointsAttr().Set(list(self.joints_.values()))
        animPrim.CreateRotationsAttr()
        animPrim.CreateTranslationsAttr()
        animPrim.CreateScalesAttr().Set(
            [
                Gf.Vec3h(1, 1, 1),
            ]
            * len(self.joints_)
        )

        valueclip = Usd.ClipsAPI(animPrim)
        valueclip.SetClipPrimPath("/Motion")
        valueclip.SetClipManifestAssetPath(manifestFile.relative_to(self.__baseDir.parent).as_posix())
        valueclip.SetClipTemplateAssetPath(self.pattern_.relative_to(self.__baseDir.parent).as_posix())
        valueclip.SetClipTemplateStartTime(0)
        valueclip.SetClipTemplateEndTime(self.lastFrame_)
        valueclip.SetClipTemplateStride(self.__stride)

        # flush valueclips file
        self.flushTimesample()

        layer.TransferContent(stage.GetRootLayer())
        layer.Export(self.__mainFile.as_posix())

    def updateSkeleton(self, skeleton: list):
        self.joints_, self.jointNames_, self.restTransforms_ = hierarchy(skeleton)

    def addTimesample(self, sample: dict):
        frame = sample["fnum"]
        if self.initialFrame_ is None:
            self.initialFrame_ = frame
        frame -= self.initialFrame_
        self.lastFrame_ = max(self.lastFrame_, frame)
        self.timesamples_[(frame // self.__stride) * self.__stride][frame] = sample

        buckets = self.timesamples_.keys()
        if self.joints_ is not None and len(self.timesamples_[min(buckets)]) >= self.__stride:
            fullBucket = min(buckets)
            anims = self.timesamples_.pop(fullBucket)
            self.__writeAnimation(fullBucket, anims)

    def flushTimesample(self):
        for k, v in self.timesamples_.items():
            if len(v) < self.__stride:
                max_1 = min(v.keys()) + self.__stride - 1
                v[max_1] = v[max(v.keys())]
            self.__writeAnimation(k, v)

        for t in self.__writeAnimationThreads:
            t.join()

    def __writeAnimation(self, base, samples):
        file = Path(self.pattern_.as_posix().replace("#", str(base)))
        self.__writeAnimationThreads.append(
            multiprocessing.Process(
                target=saveValueClip,
                args=(
                    file.as_posix(),
                    self.joints_,
                    samples,
                ),
                name=file.name,
            )
        )
        self.__writeAnimationThreads[-1].start()


def hierarchy(skeleton: list):
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

    jointNames = OrderedDict()

    def BuildJointNames(s):
        jointNames[s.id] = s.name()
        for c in s.children:
            BuildJointNames(c)

    BuildJointNames(skel)

    restTransForms = OrderedDict()

    def BuildRests(s):
        restTransForms[s.id] = s.restTransform
        for c in s.children:
            BuildRests(c)

    BuildRests(skel)
    return joints, jointNames, restTransForms


def generateManifest(file: str):
    stage = Usd.Stage.CreateInMemory()

    animPrim = UsdSkel.Animation.Define(stage, "/Motion")
    animPrim.CreateRotationsAttr()
    animPrim.CreateTranslationsAttr()

    layer = stage.GetEditTarget().GetLayer()
    layer.TransferContent(stage.GetRootLayer())
    layer.Export(file)


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
            translation_series.append(Gf.Vec3f(*t))

        rotationsAttr.Set(rotation_series, time)
        translationsAttr.Set(translation_series, time)

    layer = stage.GetEditTarget().GetLayer()
    layer.TransferContent(stage.GetRootLayer())
    layer.Export(file)


__all__ = ["USDWriter"]
