# PiksiLand

For background on our project, you can find a copy of our final report here:  
https://www.dropbox.com/s/33yc60lk8twa2bz/Luzarraga_McDonnell_File.pdf?dl=0  

This document outlines the steps necessary to get our code up and running on your computer. If you have any questions, you can email us at luzarragan@gmail.com or rkmcd93@gmail.com, although answers to many of your questions can probably be found more readily on Google. 


1. Installing Linux 
--
We recommend running Linux on your computer, as it is necessary if you want to use the simulator features in MAVProxy or the Piksi console. Running Linux in a virtual machine also create problems, so we recommend partitioning your drive and installing Linux on one of the partions. We used MacBook laptops and there are a variety of tutorials online that explain how to partition your drive and install Linux. We used rEFInd, which is a boot manager that will allow you to choose between Mac OS X, Linux, Windows, and other operating systems when you boot your computer. The exact steps for installing rEFInd will depend on what version of Mac OS X you are running. For our Linux operating system, we installed Ubuntu 14.04, which is available for free online. To install packages on Ubuntu, you will use the apt-get command, which you can read about here: https://help.ubuntu.com/lts/serverguide/apt-get.html. To use the sudo command, you will need to know the administrator password for your computer, which you will enter when you install Linux.  


2. Installing MAVProxy  
--  
MAVProxy will be used as your primary Ground Constrol Station (GCS). Instructions for installing MAVProxy on Linux and using the GCS can be found on the MAVProxy website: 
http://tridge.github.io/MAVProxy/    


3. Setting up SITL on Linux  
--
MAVProxy has a Software In The Loop (SITL) simulator that you can use to debug your code if you are running Linux. Instructions for setting up the simulator on Linux can be found on the ArduPilot website: http://dev.ardupilot.com/wiki/simulation-2/sitl-simulator-software-in-the-loop/setting-up-sitl-on-linux/  


4. Installing DroneKit  
--
You will need to install DroneKit's Python API's in order to use them. Instructions for installing DroneKit on Linux can be found on the 3DR DroneKit website: http://python.dronekit.io/guide/getting_started.html  


5. Installing the Piksi Console  
--  
If you are running Linux, you will need to run the Piksi console from source. Instructions for installing the Piksi console can be found on the Swift Nav website:  
http://docs.swiftnav.com/wiki/HOW-TO:_Running_the_Piksi_Console_from_source    


6. Installing Memcache   
--
Memcache is a package used to communicate between the Piksi console and MAVProxy. The simple.py script uses memcache to save the NED vector from the Piksi receivers to a memory location and the final_piksi_land.py script then retrieves the NED vector from this memory location. To install the memcache Python package, enter into the command line:

~~~
sudo pip install python-memcached
~~~

To install the memcache Linux package, enter into the command line:

~~~
sudo apt-get install memcached  
~~~


7. Installing the Latest Firmware    
-- 
The final_piksi_land.py script controls the quadcopter by sending velocity commands over MAVProxy based on the NED vector it receives from the Piksi receivers. In order to send velocity commands to the quadcopter, you must be using the most recent version of the ArduPilot firmware, which is not a stable release. Normally, you could update the firware using APM Planner, which is available for both Mac OS X and Linux. In order to install custom firmware, however, you must install it using Mission Planner, which is only available on Windows. Therefore, in order to run our code, you will need access to a Windows computer. First, you should install Mission Planner, which is available on the ArduPilot website: http://ardupilot.com/downloads/?did=82. Next, download the latest firmware version from firmware.diydrones.com. We downloaded the latest version from http://firmware.diydrones.com/Copter/latest/PX4-quad/, but new versions are added periodically, so you might need to search around the site to find the right one. After you download the latest firmware, choose the "custom firmware" option in Mission Planner and select the file you just downloaded. Once you have uploaded the latest firmware to the quadcopter, you should be able to send velocity commands to it directly.  

8. Installing GPSD  
--
If you want to use a standard GPS receiver as a backup target in case the Piksi receivers lose RTK lock, you need to have a GPS receiver plugged into the USB port of the laptop and transmitting GPS coordinates in the NMEA format. The GPS receiver should do this automatically once it is plugged in, as long as you have installed gpsd. This should be installed on Linux by default, but to make sure, type into the command line: 

~~~
sudo apt-get install gpsd
~~~

9. Attempting an Autonomous Landing
--
Before any test flights, make sure you follow all steps on the pre-flight safety checklist. In order for the code to run, you should have the standard GPS receiver plugged into the laptop and transmitting GPS coordinates. The quadcopter should be on and communicating with the laptop over MAVProxy. One Piksi receiver should be plugged into the laptop and the other Piksi receiver should be receiving power from the quadcopter. Open the Piksi console and wait for the Piksi to receive RTK lock. After the Piksi console indicates RTK lock, try to judge if the NED vector seems accurate. If not, you should reset IAR and converge to a new solution because you have a false lock. Once you achieve RTK lock and the solution seems accurate, you should launch the simple.py script by navigating to its directory and entering at the command line:

~~~
python simple.py
~~~

Once simple.py is running and writing NED values using memcache, take off manually using the controller. Once the quadcopter is at a decent altitude (we usually used about 10 meters), run the final_piksi_land.py script in MAVProxy by typing into the command line:

~~~
api start final_piksi_land.py
~~~

Note: This will only work if you are in the directory where final_piksi_land.py is located.  

After you launch the script, the quadcopter should hopefully perform an autonomous landing. One person should at all times be watching the quadcopter with the controller in their hands so that they can assume manual control in case the quadcopter begins to act strangely.  

It is important to remember that the Piksi receivers can be quite temperamental and often lose RTK lock, in which case the script should revert to using the standard GPS receiver as its target, although this does not always work.


Well that's everything. If we forgot anything or you have any questions, feel free to email us.  

Best,  
Nick and Ryan





	
