#!/usr/bin/env python3
"""
Functions built from VMWare samples by Dmitry to provide functionality to the SDA PoV SJC pods.
"""

from pyvim.connect import Disconnect, SmartConnectNoSSL
from pyVmomi import vim, vmodl
import atexit
import logging

log = logging.getLogger(__name__)

def wait_for_tasks(service_instance, tasks):
    """Given the service instance si and tasks, it returns after all the tasks are complete"""
    property_collector = service_instance.content.propertyCollector
    task_list = [str(task) for task in tasks]
    # Create filter
    obj_specs = [vmodl.query.PropertyCollector.ObjectSpec(obj=task)
                 for task in tasks]
    property_spec = vmodl.query.PropertyCollector.PropertySpec(type=vim.Task,
                                                               pathSet=[],
                                                               all=True)
    filter_spec = vmodl.query.PropertyCollector.FilterSpec()
    filter_spec.objectSet = obj_specs
    filter_spec.propSet = [property_spec]
    pcfilter = property_collector.CreateFilter(filter_spec, True)
    try:
        version, state = None, None
        # Loop looking for updates till the state moves to a completed state.
        while len(task_list):
            update = property_collector.WaitForUpdates(version)
            for filter_set in update.filterSet:
                for obj_set in filter_set.objectSet:
                    task = obj_set.obj
                    for change in obj_set.changeSet:
                        if change.name == 'info':
                            state = change.val.state
                        elif change.name == 'info.state':
                            state = change.val
                        else:
                            continue

                        if not str(task) in task_list:
                            continue

                        if state == vim.TaskInfo.State.success:
                            # Remove task from taskList
                            task_list.remove(str(task))
                        elif state == vim.TaskInfo.State.error:
                            raise task.info.error
            # Move to next version
            version = update.version
    finally:
        if pcfilter:
            pcfilter.Destroy()


def get_object(content, vimtype, name):
    """
     Get the vsphere object associated with a given text name
    """
    container = content.viewManager.CreateContainerView(content.rootFolder, vimtype, True)
    for view in container.view:
        if view.name == name:
            container.Destroy()
            return view
    container.Destroy()


def get_portgroup(content, name):
    return get_object(content, [vim.Network], name)


def get_vm(content, name):
    return get_object(content, [vim.VirtualMachine], name)


def get_all_portgroups(content):
    portgroup_view = content.viewManager.CreateContainerView(content.rootFolder, [vim.Network], True)
    portgroups = [portgroup for portgroup in portgroup_view.view]
    portgroup_view.Destroy()
    return portgroups


def get_all_vms(content):
    vm_view = content.viewManager.CreateContainerView(content.rootFolder, [vim.VirtualMachine], True)
    vms = [vm for vm in vm_view.view]
    vm_view.Destroy()
    return vms


def get_esxi_hosts(content):
    esxi_host_view = content.viewManager.CreateContainerView(content.rootFolder, [vim.HostSystem], True)
    esxi_hosts = [esxi_host for esxi_host in esxi_host_view.view]
    esxi_host_view.Destroy()
    return esxi_hosts


def get_vm_network_adapters(vm, portgroups=True):
    network_adapters = []
    for device in vm.config.hardware.device:
        if isinstance(device, vim.vm.device.VirtualEthernetCard):
            if portgroups:
                network_adapter = device.backing.network
                network_adapters.append(network_adapter)
            else:
                network_adapters.append(device)
    return network_adapters


def get_vm_status(vm):
    return vm.runtime.powerState


def power_on_vm(vm, tasks=None):
    task = vm.PowerOn()
    if tasks is not None:
        tasks.append(task)
    else:
        return task


def power_off_vm(vm, tasks=None):
    task = vm.PowerOff()
    if tasks is not None:
        tasks.append(task)
    else:
        return task


def print_objects(objects):
    for esxi_object in objects:
        print("Object id: {!r}, name: {}".format(esxi_object, esxi_object.name))


def connect_network_adapter(vm, idx=0, tasks=None):
    vm_network_adapters = get_vm_network_adapters(vm, portgroups=False)
    modified_adapter = vm_network_adapters[idx]

    device_spec = vim.vm.device.VirtualDeviceSpec()
    device_spec.operation = vim.vm.device.VirtualDeviceSpec.Operation.edit
    device_spec.device = modified_adapter
    device_spec.device.connectable.connected = True
    config_spec = vim.vm.ConfigSpec(deviceChange=[device_spec])
    task = vm.ReconfigVM_Task(config_spec)
    if tasks is not None:
        tasks.append(task)
    else:
        return task


def disconnect_network_adapter(vm, idx=0, tasks=None):
    vm_network_adapters = get_vm_network_adapters(vm, portgroups=False)
    modified_adapter = vm_network_adapters[idx]

    device_spec = vim.vm.device.VirtualDeviceSpec()
    device_spec.operation = vim.vm.device.VirtualDeviceSpec.Operation.edit
    device_spec.device = modified_adapter
    device_spec.device.connectable.connected = False
    config_spec = vim.vm.ConfigSpec(deviceChange=[device_spec])
    task = vm.ReconfigVM_Task(config_spec)
    if tasks is not None:
        tasks.append(task)
    else:
        return task


def change_vm_adapter_portgroup(vm: classmethod,
                                idx: int=0,
                                new_portgroup: str=None,
                                disable_adapter_before_change: bool=True,
                                tasks=None):
    if disable_adapter_before_change:
        if tasks is not None:
            disconnect_network_adapter(vm, idx, tasks)
        else:
            raise ValueError("If disabling adapter is required first, please provide tasks variable")
    vm_network_adapters = get_vm_network_adapters(vm, portgroups=False)
    modified_adapter = vm_network_adapters[idx]
    device_spec = vim.vm.device.VirtualDeviceSpec()
    device_spec.operation = vim.vm.device.VirtualDeviceSpec.Operation.edit
    device_spec.device = modified_adapter
    device_spec.device.backing.network = new_portgroup
    device_spec.device.backing.deviceName = new_portgroup.name
    device_spec.device.connectable.startConnected = True
    config_spec = vim.vm.ConfigSpec(deviceChange=[device_spec])
    task = vm.ReconfigVM_Task(config_spec)
    if tasks is not None:
        tasks.append(task)
    else:
        return task


def get_vm_network_adapter_status(vm: classmethod, idx: int=0) -> classmethod:
    vm_network_adapters = get_vm_network_adapters(vm, portgroups=False)
    adapter = vm_network_adapters[idx]
    return adapter.connectable.connected


def test_getting_data(esxi_content: classmethod) -> None:
    all_portgroups = get_all_portgroups(esxi_content)
    all_vms = get_all_portgroups(esxi_content)
    print_objects(all_portgroups)
    print_objects(all_vms)
    vm = get_vm(esxi_content, TEST_VM_NAME)
    vm_status = get_vm_status(vm)
    print("VM {} is {}".format(vm.name, vm_status))
    vm_network_adapters = get_vm_network_adapters(vm)
    print("VM {} has the following network adapters configured:".format(vm.name))
    print_objects(vm_network_adapters)


def test_tasks(esxi_content: classmethod, esxi_connector: classmethod) -> None:

    task_list = []
    vm = get_vm(esxi_content, TEST_VM_NAME)
    print("Current status of VM {} is {}".format(TEST_VM_NAME, get_vm_status(vm)))

    # power_on_vm(vm, tasks=task_list)

    print("VM {} has the following network adapters configured:".format(vm.name))
    vm_network_adapters = get_vm_network_adapters(vm)
    print_objects(vm_network_adapters)

    new_portgroup = get_portgroup(esxi_content, TEST_PORTGROUP)
    change_vm_adapter_portgroup(vm, idx=0, new_portgroup=new_portgroup, disable_adapter_before_change=True,
                                tasks=task_list)

    wait_for_tasks(esxi_connector, task_list)

    print("VM {} has the following network adapters configured:".format(vm.name))
    vm_network_adapters = get_vm_network_adapters(vm)
    print_objects(vm_network_adapters)


def connect2vsphere(host: str, user: str, pwd: str, port: int):
    esxi_connector = SmartConnectNoSSL(host=host, user=user, pwd=pwd, port=port)
    atexit.register(Disconnect, esxi_connector)
    esxi_content = esxi_connector.RetrieveContent()
    return esxi_content, esxi_connector


def main() -> None:
    """Run tests."""
    HOST = '1.1.1.1'
    PORT = '443'
    USERNAME = 'test_user'
    PASSWORD = 'good_luck_guessing!'

    print("Establish connection to vSphere.")
    esxi_content, esxi_connector = connect2vsphere(host=HOST, user=USERNAME, pwd=PASSWORD, port=PORT)
    print("\n\nRun test_getting_data():")
    test_getting_data(esxi_content)
    print("\n\nRun test_tasks():")
    test_tasks(esxi_content, esxi_connector)


if __name__ == "__main__":
    # For the test functions
    TEST_VM_NAME = "p1_client2"
    TEST_PORTGROUP = "Pod1_Edge1-Port11"

    main()
