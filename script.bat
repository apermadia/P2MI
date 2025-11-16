@echo off
echo Adding Firewall Rules for XPlaneConnect...
netsh advfirewall firewall add rule name="XPlaneConnect UDP from PythonPC" dir=in action=allow protocol=UDP localport=49009 remoteip=192.168.10.2
netsh advfirewall firewall add rule name="XPlaneConnect TCP from PythonPC" dir=in action=allow protocol=TCP localport=49009 remoteip=192.168.10.2
echo Done!
pause
