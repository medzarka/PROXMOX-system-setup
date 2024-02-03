
import sys
import os

from tools.console_printing import ConsolePrint
from tools.VM_CheckInformation import VM_CheckInformation
from tools.VM_LoadConfigurations import VM_LoadConfigurations
from tools.VM_CreateVirtualMachine import VM_CreateVirtualMachine

import subprocess
import configparser 
from urllib.parse import urlparse
import random
import tempfile 


#----------------------------------------------------------------------------------------

def config(): 
    # System configurations
    DATA = {}
    # #PVE data
    DATA['PVE_CACHE_PATH']='/var/lib/vz/template/cache'
    DATA['PVE_ISO_PATH']='/var/lib/vz/template/iso'
    DATA['PVE_LXC_CONF']='/etc/pve/lxc'
    DATA['PVE_VM_CONF']='/etc/pve/lxc' # TODO

    # Machine data
    DATA['MACHINE_INI_FILENAME'] = 'machine.ini'
    DATA['MACHINE_DESCRIPTION_FILENAME']= 'description.md'
    DATA['MACHINE_ROOTFS_DIRNAME'] = 'rootfs'
    DATA['MACHINES_PATH'] = os.path.abspath(os.path.join(__file__, os.pardir, os.pardir, 'machines'))

    return DATA

#----------------------------------------------------------------------------------------
def main(DATA): 

    MACHINE_ID=None  
    MACHINE_DIR = None

    MACHINE_CONF = None
    MACHINE_TYPE = None
    
    ############################################################################
    os.system('clear' if os.name == 'posix' else 'cls')
    ConsolePrint.print_header1("")
    ConsolePrint.print_header1("####################################")
    ConsolePrint.print_header1("#    Creating a virtual machine.   #")
    ConsolePrint.print_header1("####################################")
    ConsolePrint.print_header1("")

    ############################################################################
    # Check virtual machine information
    vm_check_config = VM_CheckInformation(data=DATA)
    DATA = vm_check_config.proceed()

    ############################################################################
    # load machine configuration
    vm_load_config = VM_LoadConfigurations(data=DATA)
    DATA = vm_load_config.proceed()


    ############################################################################
    # Create the virtual Machine
    vm_create_cm = VM_CreateVirtualMachine(data=DATA)
    DATA = vm_create_cm.proceed()
    


    sys.exit(-1)

    ############################################################################
    ############################################################################
    ##########################################################
    # Clean old virtual machine 
    ColorPrint.print_pass("-- Step 3 -- Clean old virtual machine")
    if MACHINE_TYPE == 'LXC':
        print("Stopping old container")
        res = execute_shell_command(f"pct stop {MACHINE_ID}")
        if res == 0:
            print("Waiting 3 sec for container to die")
            res = execute_shell_command(f"sleep 3")
            print("Backup the old container")
            res = execute_shell_command(f"vzdump {MACHINE_ID}")
            print("Deleting old container")
            res = execute_shell_command(f"pct destroy {MACHINE_ID}")
        else:
            print("Machine not found.")
       
    ############################################################################
    ############################################################################
    ##########################################################
    # Create the VM
    ColorPrint.print_pass("-- Step 4 -- Create the virtual machine")
    if MACHINE_TYPE == 'LXC':
        cmd = f"pct create {MACHINE_ID} {os.path.join(PVE_CACHE_PATH, MACHINE_DATA['VM_IMAGE_NAME'])}"
        cmd += f" --arch {MACHINE_DATA['ARCH']}"
        cmd += f" --hostname {MACHINE_DATA['HOSTNAME']}"
        cmd += f" --cores {MACHINE_DATA['CORES']}"
        cmd += f" --memory {MACHINE_DATA['MEMORY']}"
        cmd += f" --swap {MACHINE_DATA['SWAP']}"
        cmd += f" --net0 name=eth0,bridge={MACHINE_DATA['BRIDGE']},firewall=0,gw={MACHINE_DATA['GW']},ip={MACHINE_DATA['IP']}/24,ip6=auto,type=veth"
        if MACHINE_DATA['VLAN'] != '':
           cmd += f",tag={MACHINE_DATA['VLAN']}"
        if MACHINE_DATA['IP2'] != '' and MACHINE_DATA['BRIDGE2'] != '' :
            cmd += f" --net1 name=eth1,bridge={MACHINE_DATA['BRIDGE2']},firewall=0,ip={MACHINE_DATA['IP2']}/24,ip6=auto,type=veth"
            if MACHINE_DATA['VLAN2'] != '':
                cmd += f",tag={MACHINE_DATA['VLAN2']}"
        cmd += f" --nameserver {MACHINE_DATA['DNS']}"
        cmd += f" --storage {MACHINE_DATA['STORAGE']}"
        cmd += f" --rootfs {MACHINE_DATA['STORAGE']}:{MACHINE_DATA['DISK_SIZE']}" 
        cmd += f" --unprivileged {MACHINE_DATA['UNPRIVILEGED']}"
        if MACHINE_DATA['FEATURES'] != '':
            cmd += f" --features {MACHINE_DATA['FEATURES']}"
        cmd += f" --ostype {MACHINE_DATA['OS_TYPE']}"
        cmd += f" --password={MACHINE_DATA['PASSWORD']}"
        cmd += f" --start {MACHINE_DATA['START']}"
        cmd += f" --onboot {MACHINE_DATA['ONBOOT']}"
        cmd += f" --timezone {MACHINE_DATA['TIMEZONE']}"
        cmd += f" --ssh-public-keys {MACHINE_DATA['SSH-KEY']}"
        cmd += f" --tags {MACHINE_DATA['TAGS']}"

        res = execute_shell_command(cmd)
        if res != 0:
            print(f"Machine not created. Check with the command line {cmd}")
            sys.exit(-1)
        
        print(f"Machine with id={MACHINE_ID} created.")
        
            

    if MACHINE_TYPE == 'VM':
        ColorPrint.print_fail(f"Not yet implemented")
        sys.exit(-1)
        # TODO


    ############################################################################
    ############################################################################
    ##########################################################
    # Post-install
    ColorPrint.print_pass("-- Step 5 -- Post-install")
    if MACHINE_TYPE == 'LXC':
        print(f"Rebooting machine with id={MACHINE_ID}.")
        execute_shell_command(f"pct reboot {MACHINE_ID}")
        print(f"Waiting 3 seconds.")
        execute_shell_command(f"sleep 3")
        print(f"copy post-install script/data files.")
        _rootfs_path = os.path.join(MACHINE_DIR, 'rootfs')
        _rootfs_zip_path = os.path.join(MACHINE_DIR, 'rootfs.tar.gz')
        _secret_file = os.path.join(MACHINE_DIR, 'env', 'passwd')
        _setup_file = os.path.join(MACHINE_DIR, 'setup.sh')
        if os.path.isdir(_rootfs_path):
            print(f"\t- compress the rootfs folder ({_rootfs_path}.")
            execute_shell_command(f"tar -zvcf {_rootfs_zip_path} -C {MACHINE_DIR} rootfs")
            print(f"\t- push the compressed rootfs folder to vm ({_rootfs_zip_path}.")
            execute_shell_command(f"pct push {MACHINE_ID} {_rootfs_zip_path} /root/rootfs.tar.gz")
            print(f"\t- delete the compressed rootfs folder.")
            execute_shell_command(f"rm -rf {_rootfs_zip_path}")
        print(f"\t- push password file ({_secret_file}).")
        execute_shell_command(f"pct push {MACHINE_ID} {_secret_file} /root/secret")
        if os.path.isfile(_setup_file):
            print(f"\t- push the setup file to the virtual machine ({_setup_file}).")
            execute_shell_command(f"pct push {MACHINE_ID} {_setup_file} /root/setup.sh")
            print(f"\t- make the setup file executable.")
            execute_shell_command(f"pct exec {MACHINE_ID} chmod +x /root/setup.sh")
            print(f"\t- run the setup file.")
            ColorPrint.print_bold('**************************************************')
            execute_shell_command(f"pct exec {MACHINE_ID} /root/setup.sh", stdout=True)
            ColorPrint.print_bold('**************************************************')
        print(f"rebooting.")
        execute_shell_command(f"pct reboot {MACHINE_ID}")

        print(f"Work done.")


    else:
        print(f"The description file is not found. Ignoring.")
# __name__ 
if __name__=="__main__": 
    DATA=config()
    main(DATA) 
