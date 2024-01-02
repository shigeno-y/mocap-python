import threading
import socketserver
import queue

from decomposer import decomposePacket

CLIENT_QUEUES = dict()


def hierarchyWriter(file, skeleton: dict):
    print(
        """\
HIERARCHY
ROOT root
{
  OFFSET 0 93.2929 0
  CHANNELS 6 Xposition Yposition Zposition Zrotation Xrotation Yrotation
  JOINT torso_1
  {
    OFFSET 0 5.07867 -1.15138
    CHANNELS 6 Xposition Yposition Zposition Zrotation Xrotation Yrotation
    JOINT torso_2
    {
      OFFSET 0 5.61661 1.07143
      CHANNELS 6 Xposition Yposition Zposition Zrotation Xrotation Yrotation
      JOINT torso_3
      {
        OFFSET -1.02604e-17 5.98978 0.11501
        CHANNELS 6 Xposition Yposition Zposition Zrotation Xrotation Yrotation
        JOINT torso_4
        {
          OFFSET -1.10457e-17 6.50583 -0.443523
          CHANNELS 6 Xposition Yposition Zposition Zrotation Xrotation Yrotation
          JOINT torso_5
          {
            OFFSET -1.97295e-17 7.60548 -1.50593
            CHANNELS 6 Xposition Yposition Zposition Zrotation Xrotation Yrotation
            JOINT torso_6
            {
              OFFSET -2.53307e-17 9.49737 -0.914492
              CHANNELS 6 Xposition Yposition Zposition Zrotation Xrotation Yrotation
              JOINT torso_7
              {
                OFFSET -2.90401e-17 10.5513 1.57691
                CHANNELS 6 Xposition Yposition Zposition Zrotation Xrotation Yrotation
                JOINT neck_1
                {
                  OFFSET -1.29193e-17 4.78644 0.715339
                  CHANNELS 6 Xposition Yposition Zposition Zrotation Xrotation Yrotation
                  JOINT neck_2
                  {
                    OFFSET -1.8116e-17 4.82109 0.421791
                    CHANNELS 6 Xposition Yposition Zposition Zrotation Xrotation Yrotation
                    JOINT head
                    {
                      OFFSET -2.00958e-17 4.83041 0.765062
                      CHANNELS 6 Xposition Yposition Zposition Zrotation Xrotation Yrotation
                      End Site
                      {
                        OFFSET 0 0 0
                      }
                    }
                  }
                }
                JOINT l_shoulder
                {
                  OFFSET 1.23299 -7.60731 7.53374
                  CHANNELS 6 Xposition Yposition Zposition Zrotation Xrotation Yrotation
                  JOINT l_up_arm
                  {
                    OFFSET 12.9547 3.2495 -3.26872
                    CHANNELS 6 Xposition Yposition Zposition Zrotation Xrotation Yrotation
                    JOINT l_low_arm
                    {
                      OFFSET 29.2081 0.0598081 0.137039
                      CHANNELS 6 Xposition Yposition Zposition Zrotation Xrotation Yrotation
                      JOINT l_hand
                      {
                        OFFSET 24.234 0.0496219 0.113701
                        CHANNELS 6 Xposition Yposition Zposition Zrotation Xrotation Yrotation
                        End Site
                        {
                          OFFSET 0 0 0
                        }
                      }
                    }
                  }
                }
                JOINT r_shoulder
                {
                  OFFSET -1.23299 -7.60729 7.53365
                  CHANNELS 6 Xposition Yposition Zposition Zrotation Xrotation Yrotation
                  JOINT r_up_arm
                  {
                    OFFSET -12.9547 3.2495 -3.26872
                    CHANNELS 6 Xposition Yposition Zposition Zrotation Xrotation Yrotation
                    JOINT r_low_arm
                    {
                      OFFSET -29.2081 0.0598081 0.137039
                      CHANNELS 6 Xposition Yposition Zposition Zrotation Xrotation Yrotation
                      JOINT r_hand
                      {
                        OFFSET -24.234 0.0496218 0.113702
                        CHANNELS 6 Xposition Yposition Zposition Zrotation Xrotation Yrotation
                        End Site
                        {
                          OFFSET 0 0 0
                        }
                      }
                    }
                  }
                }
              }
            }
          }
        }
      }
    }
  }
  JOINT l_up_leg
  {
    OFFSET 9.23673 -4.20556 2.0327
    CHANNELS 6 Xposition Yposition Zposition Zrotation Xrotation Yrotation
    JOINT l_low_leg
    {
      OFFSET -0.852353 -38.7721 -0.655187
      CHANNELS 6 Xposition Yposition Zposition Zrotation Xrotation Yrotation
      JOINT l_foot
      {
        OFFSET -2.32622 -40.4017 -6.04875
        CHANNELS 6 Xposition Yposition Zposition Zrotation Xrotation Yrotation
        JOINT l_toes
        {
          OFFSET 0.779096 -9.8844 12.4959
          CHANNELS 6 Xposition Yposition Zposition Zrotation Xrotation Yrotation
          End Site
          {
            OFFSET 0 0 0
          }
        }
      }
    }
  }
  JOINT r_up_leg
  {
    OFFSET -9.23673 -4.20556 2.0327
    CHANNELS 6 Xposition Yposition Zposition Zrotation Xrotation Yrotation
    JOINT r_low_leg
    {
      OFFSET 0.852353 -38.7721 -0.655187
      CHANNELS 6 Xposition Yposition Zposition Zrotation Xrotation Yrotation
      JOINT r_foot
      {
        OFFSET 2.32622 -40.4017 -6.04875
        CHANNELS 6 Xposition Yposition Zposition Zrotation Xrotation Yrotation
        JOINT r_toes
        {
          OFFSET -0.779096 -9.8844 12.4959
          CHANNELS 6 Xposition Yposition Zposition Zrotation Xrotation Yrotation
          End Site
          {
            OFFSET 0 0 0
          }
        }
      }
    }
  }
}""",
        file=file,
    )


def motionWriter(
    file,
    timesamples: dict,
    *,
    secondsPerFrame=0.02,
    decomposeAxises=(
        (1, 0, 0),
        (0, 1, 0),
        (0, 0, 1),
    ),
):
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
            r = quat.Decompose(*decomposeAxises)

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
                skel = item
            elif item["PACKET_TYPE"] == "POSE":
                timesamples[item["time"]] = item["motion"]
            else:
                pass
            q.task_done()
        except:
            pass

    with open(title + ".bvh", "w") as f:
        hierarchyWriter(f, skel)
        motionWriter(f, timesamples, decomposeAxises=((0, 0, 1), (1, 0, 0), (0, 1, 0)))


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
