import tempfile
import threading

from pxr import Gf
from .BaseWriter import BaseWriter
from .skelTree import SkelNode


class BVHWriter(BaseWriter):
    def __init__(self, *args, decomposeAxises=SkelNode.ZXY, **kwargs):
        super().__init__(*args, **kwargs, output_extension=".bvh")

        self._baseDir.absolute().mkdir(parents=True, exist_ok=True)

        self._decomposeAxises = decomposeAxises
        self._tempFiles = dict()

    def close(self):
        self.flushTimesample()

        with self._mainFile.open("w") as f:
            hierarchy(f, self.skeleton_, self._decomposeAxises)
            self._mergeAnimation(f)

    def _writeAnimation(self, base, samples):
        file = tempfile.TemporaryFile("w+")
        self._tempFiles[base] = file
        self._writeAnimationThreads.append(
            threading.Thread(
                target=saveAnimationFragment,
                args=(file, base, samples, self._decomposeAxises),
            )
        )
        self._writeAnimationThreads[-1].start()

    def _mergeAnimation(self, file):
        print("MOTION", file=file)
        print(f"Frames: {self.lastFrame_+1}", file=file)
        print(f"Frame Time: {1.0 / self.fps_}", file=file)

        for base in sorted(self._tempFiles):
            tmp = self._tempFiles.pop(base)
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
