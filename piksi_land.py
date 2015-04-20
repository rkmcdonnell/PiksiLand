from gps import *
import math
import socket
import time
import random
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

 # Dangerous: Arm and takeoff vehicle - use only in simulation
def arm_and_takeoff():
    print "Arming and taking off"
    v.mode    = VehicleMode("STABILIZE")
    v.parameters["ARMING_CHECK"] = 0
    v.armed   = True
    v.flush()

    while not v.armed and not api.exit:
        print "Waiting for arming..."
	time.sleep(1)

    print "Taking off!"
	
    v.commands.takeoff(10) # Take off to 20m height

	# Pretend we have a RC transmitter connected
    rc_channels = v.channel_override
    rc_channels[3] = 1500 # throttle
    v.channel_override = rc_channels

    v.flush()
 
    while v.location.alt < 9:
        print "Ascending. Current Altitude: ", v.location.alt
        time.sleep(1)

    v.mode = VehicleMode("GUIDED")
    print "Setting flight mode to Guided"
    v.flush()
    time.sleep(1)
    print "Entering approach"


# Controls the quadcopter using normal GPS
# If action == 0 -> lands at target
# If action == 1 -> returns after reaching 10 meters above the target
def regular_gps(action):
    try:
        # Don't let the user try to fly while the board is still booting
        if v.mode.name == "INITIALISING":
            print "Vehicle still booting, try again later"
            return

        # Use the python gps package to access the laptop GPS
        gpsd = gps(mode=WATCH_ENABLE)

        # Cruising altitude
        cruise = 10 

         # Initial destination (set to Princeton field by default)
        dest = Location(40.346479,-74.644052,cruise,is_relative=True)

        while not api.exit:
            # This is necessary to read the GPS state from the laptop
            gpsd.next()

            if v.mode.name != "GUIDED":
                print "User has changed flight modes - aborting target approach"
                break

            # Once we have a valid location (see gpsd documentation) we can start moving our vehicle around
            if (gpsd.valid & LATLON_SET) != 0:
                # Destination waypoint latitude and longitude
                dest_old = (dest.lat, dest.lon)
                # Target GPS latitude and longitude
                fix = (gpsd.fix.latitude,gpsd.fix.longitude)
                # Copter GPS latitude and longitude
                current = (v.location.lat,v.location.lon)
            
                # Only update direction if it has changed significantly since it was last checked
                if (vincenty(dest_old,fix).meters > 1):
                    dest = Location(gpsd.fix.latitude, gpsd.fix.longitude, cruise, is_relative=True)
                    v.commands.clear()
                    v.commands.goto(dest)
                    v.flush()
                    print "Updating destination to: %s" % dest

                dest_new =(dest.lat, dest.lon)
                hDist = vincenty(current, dest_new).meters
                vDist = abs(v.location.alt - dest.alt)
            
                if hDist < 1 and vDist < 1 and action == 0:
                    print "Destination reached. Beginning standard GPS Landing"
                    v.mode = VehicleMode("LAND")
                    v.flush()

                if hDist < 1 and vDist < 1 and action == 1:
                    print "At target area.  Switching to RTK hover mode"
                    return
                    
                time.sleep(0.1)

    except socket.error:
        print "Error: gpsd service does not seem to be running, plug in USB GPS or run run-fake-gps.sh"


def hover_above_target():
    n_targ = 0
    e_targ = 0
    d_targ = 10

    while 1:
        north = shared.get("north")
        east = shared.get("east")
        down = shared.get("down")
        mode = shared.get("mode")

        if mode == 0:
            print "Reverted to float mode.  Switching to regular GPS landing"
            regular_gps(0)

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

        n_error = n_targ - n_avg
        e_error = e_targ - e_avg
        d_error = d_targ - d_avg

        if abs(n_error) < 0.1 and abs(e_error) < 0.1 and abs(d_error)< 0.1:
            print "Positioned 10 meters above LZ.  Beginning initial descent."
            return

        dist_to_vel = 0.15

        vel_n =  n_error * dist_to_vel
        vel_e =  e_error * dist_to_vel
        vel_d = -d_error * dist_to_vel

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
    n_targ = 0
    e_targ = 0

    while 1:
        north = shared.get("north")
        east = shared.get("east")
        down = shared.get("down")
        mode = shared.get("mode")

        if mode == 0:
            print "Reverted to float mode.  Switching to regular GPS landing"
            regular_gps(0)

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

        if d_avg < 1:
            print "Positioned 1 meter above LZ.  Switching to land mode."
            v.mode = VehicleMode("LAND")

        n_error = n_targ - n_avg
        e_error = e_targ - e_avg
        #d_error = d_targ - d_avg

        dist_to_vel = 0.15
        descent_velocity = 0.5

        vel_n = n_error * dist_to_vel
        vel_e = e_error * dist_to_vel
        vel_d = descent_velocity

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

        # Send command to vehicle
        v.send_mavlink(msg)
        v.flush()

        time.sleep(0.1)

        vel = v.velocity
        #print "Current Velocity ", vel[0:3]

        v.flush()


# def landongps():
#     try:
#         # Don't let the user try to fly while the board is still booting
#         if v.mode.name == "INITIALISING":
#             print "Vehicle still booting, try again later"
#             return
#
#         cmds = v.commands
#         is_guided = False  # Have we sent at least one destination point?
#
#         # Use the python gps package to access the laptop GPS
#         gpsd = gps(mode=WATCH_ENABLE)
#
#         altitude = 10
#         while not api.exit:
#             # This is necessary to read the GPS state from the laptop
#             gpsd.next()
#
#             if is_guided and v.mode.name != "GUIDED":
#                 print "User has changed flight modes - aborting follow-me"
#                 break
#
#             # Once we have a valid location (see gpsd documentation) we can start moving our vehicle around
#             if (gpsd.valid & LATLON_SET) != 0:
#                 dest = Location(gpsd.fix.latitude, gpsd.fix.longitude, altitude, is_relative=True)
#                 #print "Going to: %s" % dest
#
#                 # A better implementation would only send new waypoints if the position had changed significantly
#                 cmds.goto(dest)
#                 is_guided = True
#                 #v.flush()
#
#                 altD = dest.alt
#                 latD = dest.lat
#                 lonD = dest.lon
#                 coordD = (latD, lonD)
#                 v.flush()
#
#                 # Send a new target every two seconds
#                 # For a complete implementation of follow me you'd want adjust this delay 
#                 vel = v.velocity
#                 speed = math.sqrt(vel[0] * vel[0] + vel[1] * vel[1])
#                 altQ = v.location.alt
#                 latQ = v.location.lat
#                 lonQ = v.location.lon
#                 coordQ = (latQ, lonQ)
#
#                 hDist = vincenty(coordQ, coordD).meters
#                 vDist = abs(altQ - altD)
#                 v.flush()
#
#                 print "Velocity: ", vel[0:3]
#                 print "Speed: ", speed
#                 print "Altitude: ", altQ
#                 print "Horizontal distance to target ", hDist
#                 print "Vertical distance to target ", vDist
#            
#                 if hDist < 0.5 and vDist < 0.5:
#                     v.mode = VehicleMode("LAND")
#
#                                       
#                 time.sleep(0.1)
#
#     except socket.error:
#         print "Error: gpsd service does not seem to be running, plug in USB GPS or run run-fake-gps.sh"

arm_and_takeoff()

v.flush()

regular_gps(1)

#v.flush()

# hover_above_target()

# v.flush()

# initial_descent()