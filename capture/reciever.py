import threading
import socketserver
import queue
from statistics import fmean
from datetime import datetime

from capture.decomposer import decomposePacket
from capture.Writer import USDWriter, BVHWriter, DebugWriter

CLIENT_QUEUES = dict()
CLIENT_QUEUES_LOCK = threading.Semaphore()

# TODO
# impl more sane way
WRITERS = {
    "usd": USDWriter,
    "bvh": BVHWriter,
    "debug": DebugWriter,
}
WRITER_OF_CHOICE = str()
WRITER_OPTIONS = dict()
# impl more sane way
# TODO


def worker(title: str, qs: dict, qk):
    q = qs[qk]
    flag = True
    skel = list()
    timesamples = dict()
    frame_offset = None
    title = datetime.now().strftime("%Y-%m-%d-%H-%M-%S_") + title
    frameTimes = list()

    writer = WRITERS[WRITER_OF_CHOICE](title, **WRITER_OPTIONS)

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

            if "fram" in item:
                if not frame_offset:
                    frame_offset = item["fram"]["fnum"]
                timesamples[(item["fram"]["fnum"] - frame_offset)] = item["fram"]
                writer.addTimesample(item["fram"])
                frameTimes.append(item["fram"]["uttm"])
            elif "skdf" in item:
                skel = item["skdf"]["btrs"]
                writer.updateSkeleton(skel)
            else:
                pass
            q.task_done()
        except Exception as e:
            print(e)

    qs.pop(qk)
    fps = 1.0 / fmean(map(lambda t: t[1] - t[0], zip(frameTimes, frameTimes[1:])))
    candidate = [
        30,
        50,
        60,
    ]
    if int(fps) in candidate:
        fps = int(fps)
    else:
        delta = list(map(lambda x: abs(x - fps), candidate))
        fps = int(candidate[delta.index(min(delta))])

    writer.fps_ = fps
    try:
        writer.close()
    except Exception as e:
        print(e)


class ThreadedUDPHandler(socketserver.BaseRequestHandler):
    def handle(self):
        data = self.request[0]
        dec = decomposePacket(data)
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
                        CLIENT_QUEUES,
                        self.client_address,
                    ),
                ).start()


class ThreadedUDPServer(socketserver.ThreadingMixIn, socketserver.UDPServer):
    def server_close(self):
        for q in CLIENT_QUEUES.values():
            q.put_nowait({"STOP_TOKEN": True})
        return super().server_close()


__all__ = ["WRITERS", "ThreadedUDPHandler", "ThreadedUDPServer"]
