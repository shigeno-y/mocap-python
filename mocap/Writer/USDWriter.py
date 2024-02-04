from pathlib import Path
from collections import OrderedDict
import multiprocessing

from pxr import Gf, Usd, UsdSkel
from .BaseWriter import BaseWriter
from .skelTree import SkelNode


class USDWriter(BaseWriter):
    def __init__(self, *args, clipPattern="clip.#.usd", do_more_on_flushTimesample=True, **kwargs):
        super().__init__(*args, **kwargs, output_extension=".usda")

        self._baseDir.absolute().mkdir(parents=True, exist_ok=True)

        self.pattern_ = self._baseDir / clipPattern
        self._do_more_on_flushTimesample = do_more_on_flushTimesample

        self.joints = list()
        self.jointNames = list()
        self.restTransForms = list()

    def updateSkeleton(self, skeleton: list):
        skel = None
        for s in sorted(skeleton, key=lambda x: x["bnid"]):
            if skel is None:
                skel = SkelNode(
                    s["bnid"],
                    s["tran"]["rotation"],
                    s["tran"]["translation"],
                    s["pbid"],
                )
                skel.global_to_self_transform = Gf.Matrix4d(
                    1,
                    0,
                    0,
                    0,  #
                    0,
                    1,
                    0,
                    0,  #
                    0,
                    0,
                    1,
                    0,  #
                    skel.translation[0],
                    skel.translation[1],
                    skel.translation[1],
                    1,
                )
            else:
                skel.append(
                    SkelNode(
                        s["bnid"],
                        s["tran"]["rotation"],
                        s["tran"]["translation"],
                        s["pbid"],
                    )
                )

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

        self.skeleton_ = skel
        self.joints = joints
        self.jointNames = jointNames
        self.restTransForms = restTransForms

    def close(self):
        joints = self.joints
        restTransforms = self.restTransForms
        # generate manifest file
        manifestFile = self._baseDir / "manifest.usda"
        generateManifest(manifestFile.as_posix())

        # flush valueclips file
        self.flushTimesample()

        # generate main file
        stage = Usd.Stage.CreateInMemory()
        layer = stage.GetEditTarget().GetLayer()
        skelRoot = UsdSkel.Root.Define(stage, "/Skel")
        stage.SetDefaultPrim(skelRoot.GetPrim())

        skeleton = UsdSkel.Skeleton.Define(stage, skelRoot.GetPath().AppendChild("Skeleton"))
        animPrim = UsdSkel.Animation.Define(stage, skelRoot.GetPath().AppendChild("Motion"))

        stage.SetFramesPerSecond(self._fps)
        stage.SetStartTimeCode(0)
        stage.SetEndTimeCode(self.lastFrame_)

        default_transforms = list(restTransforms.values())
        skeleton.CreateBindTransformsAttr().Set(default_transforms)
        skeleton.CreateRestTransformsAttr().Set(default_transforms)
        skeleton.CreateJointsAttr().Set(list(joints.values()))

        skelAnimBinding = UsdSkel.BindingAPI.Apply(skeleton.GetPrim())
        skelAnimBinding.CreateAnimationSourceRel().AddTarget(animPrim.GetPath())

        animPrim.CreateJointsAttr().Set(list(joints.values()))
        animPrim.CreateRotationsAttr()
        animPrim.CreateTranslationsAttr()
        animPrim.CreateScalesAttr().Set(
            [
                Gf.Vec3h(1, 1, 1),
            ]
            * len(joints)
        )

        valueclip = Usd.ClipsAPI(animPrim)
        valueclip.SetClipPrimPath("/Motion")
        valueclip.SetClipManifestAssetPath(manifestFile.relative_to(self._baseDir.parent).as_posix())
        valueclip.SetClipTemplateAssetPath(self.pattern_.relative_to(self._baseDir.parent).as_posix())
        valueclip.SetClipTemplateStartTime(0)
        valueclip.SetClipTemplateEndTime(max(self.timesamples_[max(self.timesamples_.keys())].keys()))
        valueclip.SetClipTemplateStride(self._stride)

        layer.TransferContent(stage.GetRootLayer())
        layer.Export(self._mainFile.as_posix())

    def flushTimesample(self):
        if self._do_more_on_flushTimesample:
            for base, v in self.timesamples_.items():
                if len(v) < self._stride:
                    max_1 = min(v.keys()) + self._stride - 1
                    v[max_1] = v[max(v.keys())]

            last_base = max(self.timesamples_.keys())
            last_pose_frame = max(self.timesamples_[last_base].keys())
            lase_pose = self.timesamples_[last_base][last_pose_frame]

            self.timesamples_[last_base + self._stride][last_base + self._stride] = lase_pose
            self.timesamples_[last_base + self._stride][last_base + (self._stride * 2) - 1] = lase_pose

        super().flushTimesample()

    def _writeAnimation(self, base, samples):
        file = Path(self.pattern_.as_posix().replace("#", str(base)))
        self._writeAnimationThreads.append(
            multiprocessing.Process(
                target=saveValueClip,
                args=(
                    file.as_posix(),
                    self.joints,
                    samples,
                ),
                name=file.name,
            )
        )
        self._writeAnimationThreads[-1].start()


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
