import gps
import math
import socket
import time
from droneapi.lib import VehicleMode, Location
from pymavlink import mavutil

api = local_connect()

v = api.get_vehicles()[0]

def arm_and_takeoff():
    """Dangerous: Arm and takeoff vehicle - use only in simulation"""
    # NEVER DO THIS WITH A REAL VEHICLE - it is turning off all flight safety checks
    # but fine for experimenting in the simulator

    print "Arming and taking off"
    v.mode    = VehicleMode("STABILIZE")
    v.parameters["ARMING_CHECK"] = 0
    v.armed   = True
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
 
    while v.location.alt < 14.5:
        print "Ascending. Current Altitude: ", v.location.alt
        time.sleep(1)

    v.mode = VehicleMode("GUIDED")
    v.flush()


def pos_write():

    pos_x = 10;
    pos_y = 10;
    pos_z = 0;

    while 1:

        msg = v.message_factory.set_position_target_local_ned_encode(
            0,       # time_boot_ms (not used)
            0, 0,    # target system, target component
            1,#mavutil.mavlink.MAV_FRAME_LOCAL_NED, # frame
            0b0000000111111000,  # type_mask (ignore pos | ignore acc)
            pos_x, pos_y, pos_z, # x, y, z positions (not used)
            0, 0, 0, # x, y, z velocity in m/s
            0, 0, 0, # x, y, z acceleration (not used)
            0, 0)    # yaw, yaw_rate (not used)

        v.flush()

        # send command to vehicle
        v.send_mavlink(msg)
        v.flush()

        vel = v.velocity
        print "Current Velocity ", vel[0:3]

        v.flush()

        time.sleep(3)

arm_and_takeoff()

v.flush()

pos_write()