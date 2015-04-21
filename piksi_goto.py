from gps import *
import math
import socket
import time
import memcache
import collections
from droneapi.lib import VehicleMode, Location
from pymavlink import mavutil
from geopy.distance import vincenty

api = local_connect()
v = api.get_vehicles()[0]

shared = memcache.Client(['127.0.0.1:11211'], debug=0)

n_deq = collections.deque([])
e_deq = collections.deque([])
d_deq = collections.deque([])

def piksi_goto():
    print "Setting flight mode to Guided"
    v.mode = VehicleMode("GUIDED")
    v.flush()
    time.sleep(3)

    n_targ = 0
    e_targ = 0
    d_targ = 5

    dist_to_vel = 0.05

    while 1:
        north = shared.get("north")
        east = shared.get("east")
        down = shared.get("down")
        mode = shared.get("mode")

        if v.mode.name != "GUIDED":
            print "User has changed flight modes - aborting target approach"
            break

        if mode == 0:
            print "Reverted to float mode.  Exiting goto script."
            return

        #Add new observation and delete old one from NED deques
        n_deq.append(north)
        if len(n_deq) > 5:
            n_deq.popleft()

        e_deq.append(east)
        if len(e_deq) > 5:
            e_deq.popleft()

        d_deq.append(down)
        if len(d_deq) > 5:
            d_deq.popleft()

        n_avg = sum(n_deq) / len(n_deq)
        e_avg = sum(e_deq) / len(e_deq)
        d_avg = sum(d_deq) / len(d_deq)

        print "NED avg values: ", n_avg, e_avg, d_avg


        n_error = n_avg - n_targ
        e_error = e_avg - e_targ
        d_error = d_avg - d_targ

        vel_n =  n_error * dist_to_vel
        vel_e =  e_error * dist_to_vel
        vel_d = d_error * dist_to_vel

        print "Commanded Velocities: ",vel_n,vel_e,vel_d
  
        msg = v.message_factory.set_position_target_local_ned_encode(
                0,       # time_boot_ms (not used)
                0, 0,    # target system, target component
                mavutil.mavlink.MAV_FRAME_LOCAL_NED, # frame
                0b0000000111000111,  # type_mask (ignore pos | ignore acc)
                0, 0, 0, # x, y, z positions (not used)
                vel_n, vel_e, vel_d, # x, y, z velocity in m/s
                0, 0, 0, # x, y, z acceleration (not used)
                0, 0)    # yaw, yaw_rate (not used)
        v.flush()

        # send command to vehicle
        v.send_mavlink(msg)
        v.flush()

        time.sleep(0.2)

        vel = v.velocity
        print "Current Velocity ", vel[0:3]

        v.flush()

piksi_goto()