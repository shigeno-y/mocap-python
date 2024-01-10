from pxr import Gf
from .skelTree import SkelNode


def Specifier(skel):
    return "ROOT" if skel.parent == 65535 else "JOINT"


def dump(node, file, decomposeAxises, indent=0):
    indentPrefix = "  " * indent
    if indent == 0:
        print("HIERARCHY", file=file)
    print(indentPrefix, Specifier(node), " ", node.name(), sep="", file=file)
    print(indentPrefix, "{", sep="", file=file)
    print(indentPrefix, "  OFFSET {} {} {}".format(*[x * 100 for x in node.translation]), sep="", file=file)
    print(indentPrefix, "  CHANNELS 6 Xposition Yposition Zposition {}".format(decomposeAxises[1]), sep="", file=file)
    for c in node.children:
        dump(c, file, decomposeAxises, indent + 1)
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
    dump(skel, file, decomposeAxises)


def motion(
    file,
    timesamples: dict,
    decomposeAxises,
    secondsPerFrame=0.02,
):
    print("MOTION", file=file)
    print(f"Frames: {len(timesamples)}", file=file)
    print(f"Frame Time: {secondsPerFrame}", file=file)

    for frame, poses in sorted(timesamples.items()):
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


def Write(file, skeleton: SkelNode, timesamples: dict, *, secondsPerFrame=0.02, decomposeAxises=SkelNode.ZXY):
    with open(file, "w") as f:
        hierarchy(f, skeleton, decomposeAxises)
        motion(f, timesamples, decomposeAxises, secondsPerFrame=secondsPerFrame)
