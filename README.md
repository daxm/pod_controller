# Pod Controller
A Flask program that runs in a Docker container that provides a web "GUI" for controlling VMware VMs.

Notes to prep the server/VM to run/use this Git repo:
## Clone this repository
```bash
mkdir -p ~/containers
cd ~/containers
git clone https://github.com/daxm/pod_controller.git
cd ./pod_controller
```

## Install Docker
This script will install the necessary packages and set up your environment.
```bash
./install_docker.sh
```
## (**OPTIONAL**) Update User's group environment.
* Log out and back in to update your user's group or the runme.sh script won't work.

## (**OPTIONAL**) Copy and modify config files
The install_docker.sh file already copied the .env-example and userdata.yml-example files for you.  However, if you want
to overwrite those files (to start over) use the following commands:

* Variables used to connect to VMware:
```bash
cp ~/containers/pod_controller/flask/.env-example ~/containers/pod_controller/flask/.env
nano ~/containers/pod_controller/flask/.env
```

* Variables used to describe your VMs:
```bash
cp ~/containers/pod_controller/flask/userdata.yml-example ~/containers/pod_controller/flask/userdata.yml
nano ~/containers/pod_controller/flask/userdata.yml
```

## Build the containers
This file will create a directory for the mysql database and build a cert for nginx.
```bash
cd ~/containers/pod_controller
./runme.sh
```

## Post install updating.
If you need to modify the .env or userdata.yml files you'll need to re-run the runme.sh file.
