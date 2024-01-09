from pxr import Gf
from .skelTree import SkelNode


def Specifier(skel):
    return "ROOT" if skel.parent == 65535 else "JOINT"


def dump(node, file, indent=0, decomposeAxises=SkelNode.ZXY):
    indentPrefix = "  " * indent
    if indent == 0:
        print("HIERARCHY", file=file)
    print(indentPrefix, Specifier(node), " ", node.name(), sep="", file=file)
    print(indentPrefix, "{", sep="", file=file)
    print(indentPrefix, "  OFFSET {} {} {}".format(*(node.translation)), sep="", file=file)
    print(indentPrefix, "  CHANNELS 6 Xposition Yposition Zposition {}".format(decomposeAxises[1]), sep="", file=file)
    for c in node.children:
        dump(c, file, indent + 1, decomposeAxises)
    print(indentPrefix, "}", sep="", file=file)


def hierarchy(file, skeleton: dict):
    skel = None
    for idx, s in sorted(skeleton.items(), key=lambda x: x[0]):
        if idx == 0:
            skel = SkelNode(s["id"], s["rotation"], s["translation"], s["parent_id"])
        else:
            skel.append(SkelNode(s["id"], s["rotation"], s["translation"], s["parent_id"]))
    dump(skel, file)


def motion(file, timesamples: dict, *, secondsPerFrame=0.02, decomposeAxises=SkelNode.XYZ):
    print("MOTION", file=file)
    print(f"Frames: {len(timesamples)}", file=file)
    print(f"Frame Time: {secondsPerFrame}", file=file)

    for time, poses in sorted(timesamples.items()):
        # Xposition Yposition Zposition Zrotation Xrotation Yrotation
        for index, pose in sorted(poses.items()):
            t = pose["translation"]
            rotation = pose["rotation"]

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


def Write(file, skeleton: SkelNode, timesamples: dict, *, secondsPerFrame=0.02, decomposeAxises=SkelNode.ZXY):  # 50 Hz
    with open(file, "w") as f:
        hierarchy(f, skeleton)
        motion(f, timesamples, secondsPerFrame=secondsPerFrame, decomposeAxises=decomposeAxises)
