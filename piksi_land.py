from gps import *
import math
import socket
import time
import memcache
import collections
import csv
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
    
    v.commands.takeoff(10) # Take off to 10m height

    # Pretend we have a RC transmitter connected
    rc_channels = v.channel_override
    rc_channels[3] = 1500 # throttle
    v.channel_override = rc_channels

    v.flush()
 
    while v.location.alt < 9:
        print "Ascending. Current Altitude: ", v.location.alt
        time.sleep(1)


# Controls the quadcopter using normal GPS
# If action == 0 -> lands at target
# If action == 1 -> returns after reaching 10 meters above the target
def regular_gps(action):
    try:

        # Don't let the user try to fly while the board is still booting
        if v.mode.name == "INITIALISING":
            print "Vehicle still booting, try again later"
            return

        print "Setting flight mode to Guided"
        v.mode = VehicleMode("GUIDED")
        v.flush()
        time.sleep(3)

        # Use the python gps package to access the laptop GPS
        gpsd = gps(mode=WATCH_ENABLE)

        # Cruising altitude
        cruise = 5 

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
                #if (vincenty(dest_old,fix).meters > 1):
                dest = Location(gpsd.fix.latitude, gpsd.fix.longitude, cruise, is_relative=True)
                v.commands.clear()
                v.commands.goto(dest)
                v.flush()
                print "Updating destination to %s" % dest

                dest_new =(dest.lat, dest.lon)
                hDist = vincenty(current, dest_new).meters
                vDist = abs(v.location.alt - dest.alt)
            
                if hDist < 0.2 and action == 0:
                    print "Destination reached. Landing using regular GPS"
                    v.mode = VehicleMode("LAND")
                    v.flush()
                    return 

                if hDist < 0.5 and action == 1:
                    print "At target area.  Switching to RTK hover mode"
                    return
                    
                time.sleep(0.2)

    except socket.error:
        print "Error: gpsd service does not seem to be running, plug in USB GPS or run run-fake-gps.sh"


def piksi_land():
    if v.mode.name != "GUIDED":
        print "Setting flight mode to Guided"
        v.mode = VehicleMode("GUIDED")
        v.flush()
        time.sleep(4)

    n_targ = 0
    e_targ = 0
    d_targ = 5

    reached = False
    count = 0

    #Parameters to be tuned for best results:
    p_gain = 0.15               # proportional gain (distance to velocity)
    descent_vel = 0.5           # meters per second
    max_vel = 5                 # meters per second
    deque_length = 5            # number of entries in smoothing deque
    landmode_height = 0.8         # meters
    rate = 10                   # Hz

    timestr = time.strftime("%Y%m%d-%H%M")   

    csvfile = open(timestr + '.csv', 'wb')
    writer = csv.writer(csvfile)
    writer.writerow(('p_gain','descent_vel','max_vel',
                     'deque_length', 'landmode_height','rate'))
    writer.writerow((p_gain, descent_vel, max_vel,
                     deque_length, landmode_height, rate))
    writer.writerow(('','',''))
    writer.writerow(('n_pos','e_pos','d_pos',
                     'n_avg','e_avg','d_avg',
                     'n_msg','e_msg','d_msg',
                     'n_vel','e_vel','d_vel','time'))

    while 1:
        north = shared.get("north")
        east = shared.get("east")
        down = shared.get("down")
        mode = shared.get("mode")

        if mode == 0:
            print "Reverted to float mode.  Switching to regular GPS landing"
            regular_gps(0)
            return

        #Add new observation and delete old one from NED deques
        n_deq.append(north)
        if len(n_deq) > deque_length:
            n_deq.popleft()

        e_deq.append(east)
        if len(e_deq) > deque_length:
            e_deq.popleft()

        d_deq.append(down)
        if len(d_deq) > deque_length:
            d_deq.popleft()

        n_avg = sum(n_deq) / len(n_deq)
        e_avg = sum(e_deq) / len(e_deq)
        d_avg = sum(d_deq) / len(d_deq)

        print "NED avg values: ", n_avg, e_avg, d_avg

        if abs(d_avg) < landmode_height:
            print "Positioned directly above LZ.  Switching to land mode."
            v.mode = VehicleMode("LAND")
            v.flush()
            return

        n_error = n_avg - n_targ
        e_error = e_avg - e_targ
        d_error = d_avg - d_targ

        if abs(n_error) < 0.5 and abs(e_error) < 0.5:
            if not reached:
                print "Positioned 10 meters above LZ.  Beginning initial descent."
            reached = True

        if n_error >= 0:
            vel_n =  min(n_error * p_gain, max_vel)
        else:
            vel_n =  max(n_error * p_gain, -max_vel)            

        if e_error >= 0:
            vel_e =  min(e_error * p_gain, max_vel)
        else:
            vel_e =  max(e_error * p_gain, -max_vel) 

        if reached:
            vel_d = descent_vel
        else:
            vel_d = d_error * p_gain
            vel_d = min(vel_d, max_vel)

        print "Commanded Velocities: ",vel_n,vel_e,vel_d
  
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

        time.sleep(1/float(rate))

        vel = v.velocity
        print "Current Velocity ", vel[0:3]

        v.flush()

        elapsed = count * (1/float(rate)) 

        writer.writerow((north,east,down,
                         n_avg, e_avg, d_avg,
                         vel_n, vel_e, vel_d,
                         vel[0],vel[1],vel[2],elapsed))

        count += 1


#arm_and_takeoff()

#v.flush()
regular_gps(0)

#piksi_land()