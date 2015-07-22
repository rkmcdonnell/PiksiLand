# PiksiLand

For background on our project, you can find a copy of our final report here:  
https://www.dropbox.com/s/33yc60lk8twa2bz/Luzarraga_McDonnell_File.pdf?dl=0  

This document outlines the steps necessary to get our code up and running on your computer. If you have any questions, you can email us at luzarragan@gmail.com or rkmcd93@gmail.com, although answers to many of your questions can probably be found more readily on Google. 

1. Installing Linux 
--
We recommend running Linux on your computer, as it is necessary if you want to use the simulator features in MAVProxy or the Piksi console. Running Linux in a virtual machine also create problems, so we recommend partitioning your drive and installing Linux on one of the partions. We used MacBook laptops and there are a variety of tutorials online that explain how to partition your drive and install Linux. We used rEFInd, which is a boot manager that will allow you to choose between Mac OS X, Linux, Windows, and other operating systems when you boot your computer. The exact steps for installing rEFInd will depend on what version of Mac OS X you are running. For our Linux operating system, we installed Ubuntu 14.04, which is available for free online. To install packages on Ubuntu, you will use the apt-get command, which you can read about here: https://help.ubuntu.com/lts/serverguide/apt-get.html. To use the sudo command, you will need to know the administrator password for your computer, which you will enter when you install Linux.  


2. Installing MAVProxy  
--  
MAVProxy will be used as your primary Ground Constrol Station (GCS). Instructions for installing MAVProxy on Linux can be found on the MAVProxy website: 
http://tridge.github.io/MAVProxy/    

3. Setting up SITL on Linux  
--
MAVProxy has a Software In The Loop (SITL) simulator that you can use to debug your code if you are running Linux. Instructions for setting up the simulator on Linux can be found on the ArduPilot website: http://dev.ardupilot.com/wiki/simulation-2/sitl-simulator-software-in-the-loop/setting-up-sitl-on-linux/  


4. Installing DroneKit  
--
You will need to install DroneKit's Python API's in order to use them. Instructions for installing DroneKit on Linux can be found on the 3DR DroneKit website: http://python.dronekit.io/guide/getting_started.html  


5. Installing Piksi console  
--  
If you are running Linux, you will need to run the Piksi console from source. Instructions for installing the Piksi console can be found on the Swift Nav website:  
http://docs.swiftnav.com/wiki/HOW-TO:_Running_the_Piksi_Console_from_source    


6. Installing Memcache   
--
Memcache is a package used to communicate between the Piksi console and MAVProxy. The simple.py script uses memcache to save the NED vector from the Piksi receivers to a memory location and the final_pikis_land.py script then retrieves the NED vector from this memory location, with very little delay. To install the memcache Python package, enter into the command line:

~~~
sudo pip install python-memcached
~~~

To install the memcache Linux package, enter into the command line:

~~~
sudo apt-get install memcached  
~~~


7. Installing the Proper Firmware  
-- 
Need to use Mission Planner and install unstable firware  



	
