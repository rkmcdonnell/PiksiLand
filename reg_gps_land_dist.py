import gps
import math
import socket
import time
from droneapi.lib import VehicleMode, Location
from geopy.distance import vincenty

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
    #while (v.
    #while not api.exit:
    #   print "Dis bitch is hovering"
    #  time.sleep(1)
    while v.location.alt < 14:
        print "Ascending. Current Altitude: ", v.location.alt
        time.sleep(1)

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
                                        
                time.sleep(1)

    except socket.error:
        print "Error: gpsd service does not seem to be running, plug in USB GPS or run run-fake-gps.sh"

arm_and_takeoff()

landongps()
