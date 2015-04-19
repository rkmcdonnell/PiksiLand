import gps
import math
import socket
import time
import random
import memcache
import collections
from droneapi.lib import VehicleMode, Location
from pymavlink import mavutil



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


def approach_target():

    v.mode    = VehicleMode("GUIDED")

    try:

        # Don't let the user try to fly while the board is still booting
        if v.mode.name == "INITIALISING":
            print "Vehicle still booting, try again later"
            return

        cmds = v.commands
        is_guided = False  # Have we sent at least one destination point?

        # Use the python gps package to access the laptop GPS
        gpsd = gps.gps(mode=gps.WATCH_ENABLE)

        while not api.exit:
            # This is necessary to read the GPS state from the laptop
            gpsd.next()

            if is_guided and v.mode.name != "GUIDED":
                print "User has changed flight modes - aborting target approach"
                break

            # Once we have a valid location (see gpsd documentation) we can start moving our vehicle around
            if (gpsd.valid & gps.LATLON_SET) != 0:
                altitude = 10  # in meters
                dest = Location(gpsd.fix.latitude, gpsd.fix.longitude, altitude, is_relative=True)
                #print "Going to: %s" % dest

                # A better implementation would only send new waypoints if the position had changed significantly
                cmds.goto(dest)
                is_guided = True
                #v.flush()

                altD = dest.alt
                latD = dest.lat
                lonD = dest.lon
                coordD = (latD, lonD)
                v.flush()

                # Send a new target every two seconds
                # For a complete implementation of follow me you'd want adjust this delay 
                vel = v.velocity
                speed = math.sqrt(vel[0] * vel[0] + vel[1] * vel[1])
                altQ = v.location.alt
                latQ = v.location.lat
                lonQ = v.location.lon
                coordQ = (latQ, lonQ)

                hDist = vincenty(coordQ, coordD).meters
                vDist = abs(altQ - altD)
                v.flush()


 
      
                print "Velocity: ", vel[0:3]
                print "Speed: ", speed
                print "Altitude: ", altQ
                print "Horizontal distance to target ", hDist
                print "Vertical distance to target ", vDist
            
                if hDist < 0.1 and vDist < 0.1:
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

        n_error = n_targ - n_avg
        e_error = e_targ - e_avg
        d_error = d_targ - d_avg

        if n_error < 0.1 and e_error < 0.1 and d_error < 0.1:
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

        # send command to vehicle
        v.send_mavlink(msg)
        v.flush()

        time.sleep(0.1)





        vel = v.velocity
        #print "Current Velocity ", vel[0:3]

        v.flush()



def landongps():

    v.mode    = VehicleMode("GUIDED")

    try:

        # Don't let the user try to fly while the board is still booting
        if v.mode.name == "INITIALISING":
            print "Vehicle still booting, try again later"
            return

        cmds = v.commands
        is_guided = False  # Have we sent at least one destination point?

        # Use the python gps package to access the laptop GPS
        gpsd = gps.gps(mode=gps.WATCH_ENABLE)

        while not api.exit:
            # This is necessary to read the GPS state from the laptop
            gpsd.next()

            if is_guided and v.mode.name != "GUIDED":
                print "User has changed flight modes - aborting follow-me"
                break

            # Once we have a valid location (see gpsd documentation) we can start moving our vehicle around
            if (gpsd.valid & gps.LATLON_SET) != 0:
                altitude = 15  # in meters
                dest = Location(gpsd.fix.latitude, gpsd.fix.longitude, altitude, is_relative=True)
                #print "Going to: %s" % dest

                # A better implementation would only send new waypoints if the position had changed significantly
                cmds.goto(dest)
                is_guided = True
                #v.flush()

                altD = dest.alt
                latD = dest.lat
                lonD = dest.lon
                coordD = (latD, lonD)
                v.flush()

                # Send a new target every two seconds
                # For a complete implementation of follow me you'd want adjust this delay 
                vel = v.velocity
                speed = math.sqrt(vel[0] * vel[0] + vel[1] * vel[1])
                altQ = v.location.alt
                latQ = v.location.lat
                lonQ = v.location.lon
                coordQ = (latQ, lonQ)

                hDist = vincenty(coordQ, coordD).meters
                vDist = abs(altQ - altD)
                v.flush()


 
      
                print "Velocity: ", vel[0:3]
                print "Speed: ", speed
                print "Altitude: ", altQ
                print "Horizontal distance to target ", hDist
                print "Vertical distance to target ", vDist
            
                if hDist < 0.1 and vDist < 0.1:
                    v.mode = VehicleMode("LAND")

                                        
                time.sleep(0.1)

    except socket.error:
        print "Error: gpsd service does not seem to be running, plug in USB GPS or run run-fake-gps.sh"



arm_and_takeoff()

v.flush()

approach_target()

v.flush()

hover_above_target()

v.flush()

initial_descent()