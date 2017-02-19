# kiln-controller
Python script to read max31850s and control SSR's to fire an electric kiln

update config.py desiredmax, to set desired max temperature,  outgoing email user, gmail pasword, etc

Run with:
sudo python RAMP.py

or via nohup:
nohup sudo python -u RAMP.py > ./log/test.log &

