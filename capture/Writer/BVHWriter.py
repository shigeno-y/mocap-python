from pathlib import Path
from collections import defaultdict
import tempfile
import threading

from pxr import Gf
from capture.Writer.skelTree import SkelNode


class BVHWriter:
    def __init__(
        self,
        mainFileBasename: str,
        *,
        stride: int = 600,
        framesPerSecond=60,
        decomposeAxises=SkelNode.ZXY,
        output_base=None,
        **kwargs,
    ):
        self.__baseDir = Path(mainFileBasename)
        if output_base is not None:
            self.__baseDir = Path(output_base) / self.__baseDir.name
        self.__baseDir.absolute().mkdir(parents=True, exist_ok=True)
        self.__mainFile = self.__baseDir / "main.bvh"

        self.__stride = stride
        self.fps_ = framesPerSecond
        self.__decomposeAxises = decomposeAxises

        self.__tempFiles = dict()

        self.skeleton_ = list()
        self.timesamples_ = defaultdict(dict)
        self.initialFrame_ = None
        self.lastFrame_ = -1
        self.__writeAnimationThreads = list()

    def close(self):
        self.flushTimesample()

        with self.__mainFile.open("w") as f:
            hierarchy(f, self.skeleton_, self.__decomposeAxises)
            self.__mergeAnimation(f)

    def updateSkeleton(self, skeleton: list):
        self.skeleton_ = skeleton

    def addTimesample(self, sample: dict):
        frame = sample["fnum"]
        if self.initialFrame_ is None:
            self.initialFrame_ = frame
        frame -= self.initialFrame_
        self.lastFrame_ = max(self.lastFrame_, frame)
        self.timesamples_[(frame // self.__stride) * self.__stride][frame] = sample

        buckets = self.timesamples_.keys()
        if len(self.timesamples_[min(buckets)]) >= self.__stride:
            fullBucket = min(buckets)
            anims = self.timesamples_.pop(fullBucket)
            self.__writeAnimation(fullBucket, anims)

    def flushTimesample(self):
        for t in self.timesamples_.items():
            self.__writeAnimation(*t)

        for t in self.__writeAnimationThreads:
            t.join()

    def __writeAnimation(self, base, samples):
        file = tempfile.TemporaryFile("w+")
        self.__tempFiles[base] = file
        self.__writeAnimationThreads.append(
            threading.Thread(
                target=saveAnimationFragment,
                args=(file, base, samples, self.__decomposeAxises),
            )
        )
        self.__writeAnimationThreads[-1].start()

    def __mergeAnimation(self, file):
        print("MOTION", file=file)
        print(f"Frames: {self.lastFrame_+1}", file=file)
        print(f"Frame Time: {1.0 / self.fps_}", file=file)

        for base in sorted(self.__tempFiles):
            tmp = self.__tempFiles.pop(base)
            tmp.seek(0)
            file.write(tmp.read())
            tmp.close()


def Specifier(skel):
    return "ROOT" if skel.parent == 65535 else "JOINT"


def dumpHierarchy(node, file, decomposeAxises, indent=0):
    indentPrefix = "  " * indent
    if indent == 0:
        print("HIERARCHY", file=file)
    print(indentPrefix, Specifier(node), " ", node.name(), sep="", file=file)
    print(indentPrefix, "{", sep="", file=file)
    print(indentPrefix, "  OFFSET {} {} {}".format(*[x * 100 for x in node.translation]), sep="", file=file)
    print(indentPrefix, "  CHANNELS 6 Xposition Yposition Zposition {}".format(decomposeAxises[1]), sep="", file=file)
    for c in node.children:
        dumpHierarchy(c, file, decomposeAxises, indent + 1)
    if len(node.children) == 0:
        print(indentPrefix, "  End Site", sep="", file=file)
        print(indentPrefix, "  {", sep="", file=file)
        print(indentPrefix, "    OFFSET 0 0 0", sep="", file=file)
        print(indentPrefix, "  }", sep="", file=file)
    print(indentPrefix, "}", sep="", file=file)


def hierarchy(file, skeleton: list, decomposeAxises):
    skel = None
    for s in sorted(skeleton, key=lambda x: x["bnid"]):
        if skel is None:
            skel = SkelNode(s["bnid"], s["tran"]["rotation"], s["tran"]["translation"], s["pbid"])
        else:
            skel.append(SkelNode(s["bnid"], s["tran"]["rotation"], s["tran"]["translation"], s["pbid"]))
    dumpHierarchy(skel, file, decomposeAxises)


def saveAnimationFragment(file, base, samples, decomposeAxises):
    # with tmp.open("w") as file:
    for frame, poses in sorted(samples.items()):
        # Xposition Yposition Zposition Zrotation Xrotation Yrotation
        for pose in sorted(poses["btrs"], key=lambda x: x["bnid"]):
            t = pose["tran"]["translation"]
            rotation = pose["tran"]["rotation"]
            quat = Gf.Rotation(Gf.Quaternion(rotation[3], Gf.Vec3d(rotation[0], rotation[1], rotation[2])))
            r = quat.Decompose(*decomposeAxises[0])
            print(
                round(t[0] * 100, 5),
                round(t[1] * 100, 5),
                round(t[2] * 100, 5),
                round(r[0], 5),
                round(r[1], 5),
                round(r[2], 5),
                sep=" ",
                file=file,
                end=" ",
            )
        print(file=file)
    file.flush()


__all__ = ["BVHWriter"]
