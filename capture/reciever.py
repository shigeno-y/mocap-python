import threading
import socketserver
import queue
from datetime import datetime

from .decomposer import decomposePacket
from .Writer.USDWriter import USDWriter

CLIENT_QUEUES = dict()
CLIENT_QUEUES_LOCK = threading.Semaphore()


def worker(title: str, qs: dict, qk):
    q = qs[qk]
    flag = True
    skel = list()
    timesamples = dict()
    frame_offset = None
    title = datetime.now().strftime("%Y-%m-%d-%H-%M-%S_") + title

    usdWriter = USDWriter(title, stride=600)

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
                usdWriter.addTimesample(item["fram"])
            elif "skdf" in item:
                skel = item["skdf"]["btrs"]
                usdWriter.updateSkeleton(skel)
            else:
                pass
            q.task_done()
        except Exception as e:
            print(e)

    qs.pop(qk)
    # try:
    #    WriteDebug(title, skel, timesamples)
    #    pass
    # except Exception as e:
    #    print(e)
    # try:
    #    WriteBVH(title, skel, timesamples)
    # except Exception as e:
    #    print(e)
    try:
        usdWriter.close()
    except Exception as e:
        print(e)


class ThreadedUDPHandler(socketserver.BaseRequestHandler):
    def handle(self):
        data = self.request[0]
        # socket = self.request[1]
        # cur_thread = threading.current_thread()
        # print(self.client_address, cur_thread.name, decomposePacket(data))
        dec = decomposePacket(data)
        # dec["client"] = self.client_address
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
