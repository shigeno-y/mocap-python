from pathlib import Path
from collections import OrderedDict

from pxr import Gf
from mocap.Writer.USDWriter import USDWriter

from bvh import Bvh


def composeFromBVH(infile: Path, output_base: Path, stride: int):
    bvh = None
    with infile.open() as f:
        bvh = Bvh(f.read())

    usdMain = infile.with_suffix("").name
    usd = USDWriter(
        usdMain,
        output_base=output_base,
        stride=stride,
        framesPerSecond=round(1.0 / bvh.frame_time),
    )

    usd.initialFrame_ = 0
    usd.lastFrame_ = bvh.nframes

    composeSkeleton(usd, bvh)
    composeAnimation(usdMain, output_base, stride, bvh, usd.skeleton_)

    usd.frameTimes_.append(0)
    usd.frameTimes_.append(bvh.frame_time)
    usd.frameTimes_.append(bvh.frame_time * 2)

    usd.close()


def composeSkeleton(usd: USDWriter, bvh: Bvh):
    skeleton = list()

    joints = bvh.get_joints_names()
    for j in joints:
        tmp = dict()
        tmp["bnid"] = bvh.get_joint_index(j)
        tmp["pbid"] = bvh.joint_parent_index(j)
        tmp["tran"] = dict()
        # BVH may only contain identity-quat
        tmp["tran"]["rotation"] = (
            0,
            0,
            0,
            1,
        )
        tmp["tran"]["translation"] = bvh.joint_offset(j)

        skeleton.append(tmp)

    usd.updateSkeleton(skeleton)


def composeAnimation(outfile: str, output_base: Path, stride: int, bvh: Bvh, skeleton):
    import multiprocessing

    pool = list()

    for chunk in range((bvh.nframes // stride) + 1):
        pool.append(
            multiprocessing.Process(
                target=traverseBVH,
                args=(
                    outfile,
                    output_base,
                    stride,
                    bvh,
                    skeleton,
                    chunk * stride,
                    ((chunk + 1) * stride) - 1,
                ),
            )
        )
        pool[-1].start()

    for t in pool:
        t.join()


def traverseBVH(
    outfile: str, output_base: Path, stride: int, bvh: Bvh, skeleton: OrderedDict, start_frame: int, last_frame: int
):
    usd = USDWriter(outfile, output_base=output_base, stride=stride)
    usd.initialFrame_ = 0
    usd.updateSkeleton(skeleton)
    joints = bvh.get_joints_names()
    for frame in range(start_frame, min(last_frame, bvh.nframes)):
        tmp = dict()
        tmp["fnum"] = frame
        tmp["uttm"] = frame * bvh.frame_time
        tmp["btrs"] = list()
        for j in joints:
            ttmp = dict()
            rot, tra = composeRotationTranslation(bvh, j, frame)

            ttmp["bnid"] = bvh.get_joint_index(j)
            ttmp["tran"] = dict()
            ttmp["tran"]["rotation"] = rot
            ttmp["tran"]["translation"] = tra

            tmp["btrs"].append(ttmp)
        usd.addTimesample(tmp)
    usd.flushTimesample()


def composeRotationTranslation(bvh: Bvh, joint: str, frame: int):
    ROTATION_AXIS = {
        "X": (
            1,
            0,
            0,
        ),
        "Y": (
            0,
            1,
            0,
        ),
        "Z": (
            0,
            0,
            1,
        ),
    }
    TRANSLATION_INDEX = {
        "X": 0,
        "Y": 1,
        "Z": 2,
    }

    rot = Gf.Rotation().SetIdentity()
    tra = [0, 0, 0]

    for ch in bvh.joint_channels(joint):
        val = bvh.frame_joint_channel(frame, joint, ch)
        if "rotation" in ch:
            rot *= Gf.Rotation(ROTATION_AXIS[ch[0]], val)
        elif "position" in ch:
            tra[TRANSLATION_INDEX[ch[0]]] = val

    r = Gf.Quatf(rot.GetQuat())

    return (
        *r.GetImaginary(),
        r.GetReal(),
    ), Gf.Vec3f(*tra)
