from decouple import config
from flask import Flask
from flask import render_template, request, flash, url_for, redirect, send_from_directory, Response
from ruamel.yaml import YAML
import vmware_vcenter
import logging
import os
from functools import wraps

logging.basicConfig(format='%(asctime)s %(levelname)s:%(message)s', level=logging.DEBUG)
log = logging.getLogger(__name__)

app = Flask(__name__)
USERDATA_FILE = 'userdata.yml'

yaml = YAML(typ='safe')
with open(USERDATA_FILE, 'r') as stream:
    try:
        userdata = (yaml.load(stream))
        pods = userdata['pods']
        log.info(f"Opened and loaded {USERDATA_FILE}")
    except:
        log.error(f"An error has occurred trying to open {USERDATA_FILE}.")
        exit(1)


def check_auth(username, password):
    """This function is called to check if a username/password combination is valid."""
    if username == 'daxm' and password == 'daxm..':
        return True
    return False


def authenticate():
    """Sends a 401 response that enables basic auth"""
    return Response('Could not verify your access level for that URL.\n'
                    'You have to login with proper credentials',
                    401,
                    {'WWW-Authenticate': 'Basic realm="Login Required"'})


def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            return authenticate()
        return f(*args, **kwargs)
    return decorated


def vsphere_connect() -> (classmethod, classmethod):
    # Connect to vSphere in order to use Dmitry's functions.
    return vmware_vcenter.connect2vsphere(host=config("VCENTER_HOST"),
                                          user=config("VCENTER_USERNAME"),
                                          pwd=config("VCENTER_PASSWORD"),
                                          port=config("VCENTER_PORT")
                                          )


def update_vms(esxi_content: classmethod, vms: dict) -> dict:
    # Populate/Update vms with current information.
    for vm in vms:
        # Get the object that matches the name of this vm.
        vm_object = vmware_vcenter.get_vm(esxi_content, vm['vmname'])
        # Get this vm's current power state and update the dictionary.
        vm['power_status'] = vmware_vcenter.get_vm_status(vm_object)
        # Get the vm's currently assigned portgroup and update the dictionary.
        try:
            network_adapter = vmware_vcenter.get_vm_network_adapters(vm_object)
            first_nic = 0
            vm['portgroup'] = network_adapter[first_nic].name
        except:
            log.info(f"No NIC attached to {vm['vmname']}")
        # Get the Status (Connected/Disconnected) of the NIC connected to the aforementioned portgroup.
        if 'portgroup_options' in vm:
            status = vmware_vcenter.get_vm_network_adapter_status(vm_object)
            if status:
                vm['nic_status'] = 'Connected'
            else:
                vm['nic_status'] = 'Disconnected'
    log.info("Updated 'vms' dict with current info from vCenter.")
    return vms


def get_human_readable_vm_name(pod_num: str, vmname: str) -> str:
    name = vmname
    for the_pod in pods:
        if the_pod['pod_number'] == pod_num:
            for vm in the_pod['vms']:
                if 'name' in vm and vm['vmname'] == vmname:
                    name = vm['name']
    log.info("Tried to provide a 'human readable' name for VM.")
    return name


def get_human_readable_portgroup_name(pod_num: str, vmname: str, portgroup: str) -> str:
    portgroup_name = portgroup
    for the_pod in pods:
        if the_pod['pod_number'] == pod_num:
            for vm in the_pod['vms']:
                if vm['vmname'] == vmname and 'portgroup_options' in vm:
                    for portgrouper in vm['portgroup_options']:
                        if portgroup == portgrouper['portgroup'] and 'name' in portgrouper:
                            portgroup_name = portgrouper['name']
    log.info("Tried to provide a 'human readable' name for PortGroup.")
    return portgroup_name


@requires_auth
def pod_main_page(pod_num, the_pod):
    esxi_content, esxi_connector = vsphere_connect()
    title = "Controlling %s" % the_pod['name']
    # Update the vms_template values with current data.
    vms = update_vms(esxi_content, the_pod['vms'])
    log.info(f"Rendering pod.html for pod {pod_num}.")
    return render_template("pod.html", title=title, vms=vms, pod_num=pod_num)


@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'),
                               'favicon.ico',
                               mimetype='image/vnd.microsoft.icon')


@app.route("/")
def index():
    title = "SDA PoV Pod Controller"
    log.info("Rendering homepage.")
    return render_template("index.html", title=title, pods=pods)


@app.route("/pod/<string:pod_num>")
def pod(pod_num: str):
    for the_pod in pods:
        if the_pod['pod_number'] == pod_num:
            return pod_main_page(pod_num, the_pod)
    # Return to index if invalid pod number is referenced.
    log.info(f"Pod named: {pod_num} not found. Rendering redirect URL.")
    return render_template("none_shall_pass.html")


@app.route("/poweroff/<string:pod_num>/<string:vmname>")
def poweroff(pod_num: str, vmname: str):
    esxi_content, esxi_connector = vsphere_connect()
    vm = vmware_vcenter.get_vm(esxi_content, vmname)
    vmware_vcenter.power_off_vm(vm)
    name = get_human_readable_vm_name(pod_num=pod_num, vmname=vmname)
    update_status_text = "Powering off %s" % name
    log.info(f"Powering off {vmname} for pod {pod_num}.")
    return render_template("update_status.html",
                           pod_num=pod_num,
                           vmname=vmname,
                           update_status_text=update_status_text)


@app.route("/poweron/<string:pod_num>/<string:vmname>")
def poweron(pod_num: str, vmname: str):
    esxi_content, esxi_connector = vsphere_connect()
    vm = vmware_vcenter.get_vm(esxi_content, vmname)
    vmware_vcenter.power_on_vm(vm)
    name = get_human_readable_vm_name(pod_num=pod_num, vmname=vmname)
    update_status_text = "Powering on %s" % name
    log.info(f"Powering on {name} for pod {pod_num}.")
    return render_template("update_status.html",
                           pod_num=pod_num,
                           vmname=vmname,
                           update_status_text=update_status_text)


@app.route("/set_portgroup/<string:pod_num>/<string:vmname>/<string:portgroup>")
def set_portgroup(pod_num: str, vmname: str, portgroup: str):
    esxi_content, esxi_connector = vsphere_connect()
    task_list = []
    vm = vmware_vcenter.get_vm(esxi_content, vmname)
    new_portgroup = vmware_vcenter.get_portgroup(esxi_content, portgroup)
    vmware_vcenter.change_vm_adapter_portgroup(vm,
                                               idx=0,
                                               new_portgroup=new_portgroup,
                                               disable_adapter_before_change=True,
                                               tasks=task_list)
    name = get_human_readable_vm_name(pod_num=pod_num, vmname=vmname)
    portgroup_name = get_human_readable_portgroup_name(pod_num=pod_num, vmname=vmname, portgroup=portgroup)
    update_status_text = "Moving %s NIC to %s" % (name, portgroup_name)
    log.info(f"Setting portgroup {portgroup_name} for VM {name}.")
    return render_template("update_status.html",
                           pod_num=pod_num,
                           vmname=vmname,
                           portgroup=portgroup,
                           update_status_text=update_status_text)


@app.route("/connect_nic/<string:pod_num>/<string:vmname>/<int:nic_num>")
def connect_nic(pod_num: str, vmname: str, nic_num: int):
    esxi_content, esxi_connector = vsphere_connect()
    vm = vmware_vcenter.get_vm(esxi_content, vmname)
    vmware_vcenter.connect_network_adapter(vm)
    name = get_human_readable_vm_name(pod_num=pod_num, vmname=vmname)
    update_status_text = "Connecting NIC for %s" % name
    log.info(f"Connecting NIC for VM {name} in pod {pod_num}.")
    return render_template("update_status.html",
                           pod_num=pod_num,
                           vmname=vmname,
                           nic_num=nic_num,
                           update_status_text=update_status_text)


@app.route("/disconnect_nic/<string:pod_num>/<string:vmname>/<int:nic_num>")
def disconnect_nic(pod_num: str, vmname: str, nic_num: int):
    esxi_content, esxi_connector = vsphere_connect()
    vm = vmware_vcenter.get_vm(esxi_content, vmname)
    vmware_vcenter.disconnect_network_adapter(vm)
    name = get_human_readable_vm_name(pod_num=pod_num, vmname=vmname)
    update_status_text = "Disconnecting NIC for %s" % name
    log.info(f"Disconnecting NIC for VM {name} in pod {pod_num}.")
    return render_template("update_status.html",
                           pod_num=pod_num,
                           vmname=vmname,
                           nic_num=nic_num,
                           update_status_text=update_status_text)


@app.route("/<path:path>")
def catchall(path):
    log.info(f"Path: {path} not found. Rendering redirect URL.")
    return render_template("none_shall_pass.html", path=path)


if __name__ == "__main__":
    log.info(f"Starting Flask app.")
    app.run(host='0.0.0.0')
