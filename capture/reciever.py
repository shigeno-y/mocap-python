import threading
import socketserver
import queue

from .decomposer import decomposePacket
from .skelTree import SkelNode

CLIENT_QUEUES = dict()
CLIENT_QUEUES_LOCK = threading.Semaphore()


def hierarchyWriter(file, skeleton: dict):
    skel = None
    for idx, s in sorted(skeleton.items(), key=lambda x: x[0]):
        if idx == 0:
            skel = SkelNode(s["id"], s["rotation"], s["translation"], s["parent_id"])
        else:
            skel.append(SkelNode(s["id"], s["rotation"], s["translation"], s["parent_id"]))
    skel.dump(file)


def motionWriter(file, timesamples: dict, *, secondsPerFrame=0.02, decomposeAxises=SkelNode.XYZ):
    from pxr import Gf

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


def worker(title: str, q: queue.Queue):
    flag = True
    skel = None
    timesamples = dict()

    while flag:
        try:
            try:
                item = q.get(timeout=1)
            except queue.Empty:
                flag = False
                continue
            if "STOP_TOKEN" in item:
                flag = False
                break

            if item["PACKET_TYPE"] == "SKEL":
                skel = item["skeleton"]
            elif item["PACKET_TYPE"] == "POSE":
                timesamples[item["time"]] = item["motion"]
            else:
                pass
            q.task_done()
        except:
            pass

    with open(title + ".bvh", "w") as f:
        hierarchyWriter(f, skel)
        motionWriter(f, timesamples, decomposeAxises=SkelNode.ZXY)


class ThreadedUDPHandler(socketserver.BaseRequestHandler):
    def handle(self):
        data = self.request[0]
        # socket = self.request[1]
        # cur_thread = threading.current_thread()
        # print(self.client_address, cur_thread.name, decomposePacket(data))
        dec = decomposePacket(data)
        dec["client"] = self.client_address
        with CLIENT_QUEUES_LOCK:
            if self.client_address in CLIENT_QUEUES.keys():
                CLIENT_QUEUES[self.client_address].put_nowait(dec)
            else:
                CLIENT_QUEUES[self.client_address] = queue.Queue()
                threading.Thread(
                    target=worker,
                    daemon=True,
                    args=(
                        "{}_{}".format(*self.client_address),
                        CLIENT_QUEUES[self.client_address],
                    ),
                ).start()


class ThreadedUDPServer(socketserver.ThreadingMixIn, socketserver.UDPServer):
    def server_close(self):
        for q in CLIENT_QUEUES.values():
            q.put_nowait({"STOP_TOKEN": True})
        return super().server_close()
