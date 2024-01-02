import threading
import socketserver
import queue

from decomposer import decomposePacket

CLIENT_QUEUES = dict()


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
                skel = item
            elif item["PACKET_TYPE"] == "POSE":
                timesamples[item["time"]] = item["motion"]
            else:
                pass
            q.task_done()
        except:
            pass

    with open(title + ".bvh", "w") as f:
        from pprint import pprint

        pprint(skel, stream=f)
        pprint(timesamples, stream=f)


class ThreadedUDPHandler(socketserver.BaseRequestHandler):
    def handle(self):
        data = self.request[0]
        # socket = self.request[1]
        # cur_thread = threading.current_thread()
        # print(self.client_address, cur_thread.name, decomposePacket(data))
        dec = decomposePacket(data)
        dec["client"] = self.client_address
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
