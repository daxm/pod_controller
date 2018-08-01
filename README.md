# Pod Controller
A Flask program that runs in a Docker container that provides a web "GUI" for controlling VMware VMs.

Notes to prep the server/VM to run/use this Git repo:
# Clone this repository
```bash
mkdir -p ~/containers
cd ~/containers
git clone https://github.com/daxm/pod_controller.git
cd ./pod_controller

```

# Install Docker
```bash
./install_docker.sh

```
# Update User's group environment.
* Log out and back in to update your user's group or the runme.sh script won't work.

# Update env_file to meet password requirements
```bash
cd ~/containers/pod-controller/flask
nano .env

```

# Update userdata.yml to match your environment.
```bash
cd ~/containers/pod-controller/flask
nano userdata.yml

```

# Build the containers
This file will create a directory for the mysql database and build a cert for nginx.
```bash
cd ~/containers/docker-guacamole-server
./runme.sh

```

# Post install updating.
If you need to modify the .env or userdata.yml files you'll need to re-run the runme.sh file.
