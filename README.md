# PiksiLand

For background on our project, you can find a copy of our final report here:  
https://www.dropbox.com/s/33yc60lk8twa2bz/Luzarraga_McDonnell_File.pdf?dl=0  

This document outlines the steps necessary to get our code up and running on your computer. If you have any questions, you can email us at luzarragan@gmail.com or rkmcd93@gmail.com, although many answers can probably be found more readily on Google. 

1. Installing Linux 
--
We recommend running Linux on your computer, as it is necessary if you want to use the simulator features in MAVProxy or the Piksi console. Running Linux in a virtual machine also create problems, so we recommend partitioning your drive and installing Linux on one of the partions. We used MacBook laptops and there are a variety of tutorials online that explain how to partition your drive and install Linux. We used rEFInd, which is a boot manager that will allow you to choose between Mac OS X, Linux, Windows, and other operating systems when you boot your computer. The exact steps for installing rEFInd will depend on what version of Mac OS X you are running. For our Linux operating system, we installed Ubuntu 14.04, which is available for free online. To install packages on Ubuntu, you will use the apt-get command, which you can read about here: https://help.ubuntu.com/lts/serverguide/apt-get.html. To use the sudo command, you will need to know the administrator password for your computer, which you will enter when you install Linux.  


2. Installing MAVProxy  
--  
MAVProxy will be used as the primary Ground Constrol Station (GCS). Instructions for installing MAVProxy on Linux can be found on the MAVProxy website: 
http://tridge.github.io/MAVProxy/    

3. Installing DroneKit  
--
You will need to install DroneKit's Python API's in order to use them. Instructions for installing DroneKit on Linux can be found on the 3DR DroneKit website: http://python.dronekit.io/guide/getting_started.html  


4. Installing Piksi console  
--  
Because you are now running Linux, you will need to run the Piksi console from source. The instructions for installing the Piksi console can be found on the Swift Nav website:  
http://docs.swiftnav.com/wiki/HOW-TO:_Running_the_Piksi_Console_from_source    


5. Installing Memcache   
--
Memcache is a package used to communicate between the Piksi console and MAVProxy. The simple.py script uses memcache to save the NED vector from the Piksi receivers to a memory location and the final_pikis_land.py script then retrieves the NED vector from this memory location, with very little delay. To install the memcache Python package, you will use pip install, so type into the command line

~~~
sudo pip install python-memcached
~~~

You will also need to use the apt-get command, so type into the command line

~~~
sudo apt-get install memcached
~~~


6. Installing the Proper Firmware  
-- 
Need to use Mission Planner and install unstable firware  



	
