import gps
import math
import socket
import time
import random
import memcache
import collections
from droneapi.lib import VehicleMode, Location
from pymavlink import mavutil
from reg_gps_land_dist import landongps 




api = local_connect()

v = api.get_vehicles()[0]

shared = memcache.Client(['127.0.0.1:11211'], debug=0)

n_deq = collections.deque([])
e_deq = collections.deque([])
d_deq = collections.deque([])


def arm_and_takeoff():
    """Dangerous: Arm and takeoff vehicle - use only in simulation"""
    # NEVER DO THIS WITH A REAL VEHICLE - it is turning off all flight safety checks
    # but fine for experimenting in the simulator

    print "Arming and taking off"
    v.mode    = VehicleMode("STABILIZE")
    v.parameters["ARMING_CHECK"] = 0
    v.armed   = True
    print v.armed
    v.flush()

    while not v.armed and not api.exit:
        print v.armed
        print api.exit
        print "Waiting for arming..."
	time.sleep(1)

    print "Taking off, muthafuckas!"
	
    v.commands.takeoff(15) # Take off to 20m height

	# Pretend we have a RC transmitter connected
    rc_channels = v.channel_override
    rc_channels[3] = 1500 # throttle
    v.channel_override = rc_channels

    v.flush()
 
    while v.location.alt < 14:
        print "Ascending. Current Altitude: ", v.location.alt
        time.sleep(1)

    v.mode = VehicleMode("GUIDED")
    v.flush()


def hover_above_target():

    while 1:

        north = shared.get("north")
        east = shared.get("east")
        down = shared.get("down")
        mode = shared.get("mode")

        if mode == 0:
            landongps()

        #Add new observation and delete old one from NED deques
        n_deq.append(north)
        if len(n_deq) > 5:
            n_deq.popleft()


        e_deq.append(east)
        if len(e_deq) > 5:
            e_deq.popleft()


        d_deq.append(north)
        if len(d_deq) > 5:
            d_deq.popleft()



        n_avg = sum(n_deq) / len(n_deq)
        e_avg = sum(e_deq) / len(e_deq)
        d_avg = sum(d_deq) / len(d_deq)

        dist_to_vel = 0.15


        vel_n = n_avg * dist_to_vel
        vel_e = e_avg * dist_to_vel
        vel_d = d_avg * dist_to_vel

        #print "Commanded Velocities: ",vel_n,vel_e,vel_d
  
        msg = v.message_factory.set_position_target_local_ned_encode(
                0,       # time_boot_ms (not used)
                0, 0,    # target system, target component
                1,#mavutil.mavlink.MAV_FRAME_LOCAL_NED, # frame
                0b0000000111000111,  # type_mask (ignore pos | ignore acc)
                0, 0, 0, # x, y, z positions (not used)
                vel_n, vel_e, vel_d, # x, y, z velocity in m/s
                0, 0, 0, # x, y, z acceleration (not used)
                0, 0)    # yaw, yaw_rate (not used)

        v.flush()

        # send command to vehicle
        v.send_mavlink(msg)
        v.flush()

        time.sleep(0.1)




        vel = v.velocity
        #print "Current Velocity ", vel[0:3]

        v.flush()


def initial_descent():

    while 1:
        


        north = shared.get("north")
        east = shared.get("east")
        down = shared.get("down")
        mode = shared.get("mode")

        if mode == 0:
            landongps()


        #Add new observation and delete old one from NED deques
        n_deq.append(north)
        if len(n_deq) > 5:
            n_deq.popleft()


        e_deq.append(east)
        if len(e_deq) > 5:
            e_deq.popleft()


        d_deq.append(north)
        if len(d_deq) > 5:
            d_deq.popleft()



        n_avg = sum(n_deq) / len(n_deq)
        e_avg = sum(e_deq) / len(e_deq)
        d_avg = sum(d_deq) / len(d_deq)

        print n_avg, e_avg, d_avg

        dist_to_vel = 0.15


        vel_n = n_avg * dist_to_vel
        vel_e = e_avg * dist_to_vel
        vel_d = d_avg * dist_to_vel

        #print "Commanded Velocities: ",vel_n,vel_e,vel_d
  
        msg = v.message_factory.set_position_target_local_ned_encode(
                0,       # time_boot_ms (not used)
                0, 0,    # target system, target component
                1,#mavutil.mavlink.MAV_FRAME_LOCAL_NED, # frame
                0b0000000111000111,  # type_mask (ignore pos | ignore acc)
                0, 0, 0, # x, y, z positions (not used)
                vel_n, vel_e, vel_d, # x, y, z velocity in m/s
                0, 0, 0, # x, y, z acceleration (not used)
                0, 0)    # yaw, yaw_rate (not used)

        v.flush()

        # send command to vehicle
        v.send_mavlink(msg)
        v.flush()

        time.sleep(0.1)





        vel = v.velocity
        #print "Current Velocity ", vel[0:3]

        v.flush()





arm_and_takeoff()

v.flush()

#hover_above_target()

initial_descent()