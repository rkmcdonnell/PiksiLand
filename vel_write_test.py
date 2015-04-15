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

    v.mode = VehicleMode("ALT_HOLD")


def vel_write():

    iVel = v.velocity
    print "Initial Velocity ", iVel[0:3]

    vel_x = 5;
    vel_y = 0;
    vel_z = 0;

    msg = v.message_factory.set_position_target_local_ned_encode(
        0,       # time_boot_ms (not used)
        0, 0,    # target system, target component
        mavutil.mavlink.MAV_FRAME_LOCAL_NED, # frame
        0x01C7,  # type_mask (ignore pos | ignore acc)
        0, 0, 0, # x, y, z positions (not used)
        vel_x, vel_y, vel_z, # x, y, z velocity in m/s
        0, 0, 0, # x, y, z acceleration (not used)
        0, 0)    # yaw, yaw_rate (not used)


    # send command to vehicle
    v.send_mavlink(msg)
    v.flush()

    fVel = v.velocity
    print "Final Velocity ", fVel[0:3]

    time.sleep(5)

    f1Vel = v.velocity
    print "Final Velocity ", f1Vel[0:3]

    v.flush()

arm_and_takeoff()

vel_write()