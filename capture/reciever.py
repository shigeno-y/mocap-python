import threading
import socketserver
import queue
from datetime import datetime

from .decomposer import decomposePacket
from .Writer import WriteUSD

CLIENT_QUEUES = dict()
CLIENT_QUEUES_LOCK = threading.Semaphore()


def worker(title: str, qs: dict, qk, writer=WriteUSD):
    q = qs[qk]
    flag = True
    skel = None
    timesamples = dict()
    title = datetime.now().strftime("%Y-%m-%d-%H-%M-%S_") + title

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
                timesamples[item["fram"]["fnum"]] = item["fram"]
            elif "skdf" in item:
                skel = item["skdf"]["btrs"]
            else:
                pass
            q.task_done()
        except:
            pass

    qs.pop(qk)
    writer(title + ".bvh", skel, timesamples)


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
