import sys
import os

from tools.console_printing import ConsolePrint
from tools.config_loader import Configurations
from tools.password_generator import PasswordGenerator
from tools.cmd_executor import execute_shell_command

class VM_CreateVirtualMachine:

    def __init__(self, data=[], exitOnError=True):

        self.data=data
        self.exitOnError=exitOnError

    
    def __proceed_exit(self):
        if self.exitOnError:
            sys.exit(-1)

    def __destroy_old_machine(self): # TODO check the case where the container could not be stopped
        ConsolePrint.print_success(f"Destroy the old container if it exists")
        res = execute_shell_command(f"pct stop {self.data['MACHINE_DATA']['VMID']} -skiplock")
        if res == 0:
            ConsolePrint.print_debug("Waiting 3 sec for container to die")
            res = execute_shell_command(f"sleep 3")
            if self.data['MACHINE_DATA']['MAKE_BACKUP_BEFORE_DESTROY'] == 1:
                ConsolePrint.print_debug("Backup the old container")
                res = execute_shell_command(f"vzdump {self.data['MACHINE_DATA']['VMID']}")
    
        ConsolePrint.print_success("Deleting old container")
        res = execute_shell_command(f"pct destroy {self.data['MACHINE_DATA']['VMID']}")
    
    def __create_lxc_machine(self):
        ConsolePrint.print_success(f"Create a LXC machine:")
        MACHINE_ID = self.data['MACHINE_DATA']['VMID']
        MACHINE_DATA = self.data['MACHINE_DATA']
        cmd = f"pct create {MACHINE_ID} {os.path.join(self.data['PVE_CACHE_PATH'], MACHINE_DATA['VM_IMAGE_NAME'])}"
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
        cmd += f" --unprivileged {MACHINE_DATA['IMPRIVILEGED']}"
        if MACHINE_DATA['FEATURES'] != '':
            cmd += f" --features {MACHINE_DATA['FEATURES']}"
        cmd += f" --ostype {MACHINE_DATA['OSTYPE']}"
        cmd += f" --password={MACHINE_DATA['PASSWORD']}"
        cmd += f" --start {MACHINE_DATA['START']}"
        cmd += f" --onboot {MACHINE_DATA['ONBOOT']}"
        cmd += f" --timezone {MACHINE_DATA['TIMEZONE']}"
        cmd += f" --ssh-public-keys {MACHINE_DATA['SSH-KEYS']}"
        cmd += f" --tags {MACHINE_DATA['TAGS']}"
                                
        res = execute_shell_command(cmd)
        if res != 0:
            print(f"Machine not created. Check with the command line {cmd}")
            sys.exit(-1)
        
        print(f"Machine with id={MACHINE_ID} created.")

    def __update_lxc_description(self):
        MACHINE_ID = self.data['MACHINE_DATA']['VMID']
        _desctipion_path = os.path.join(self.data['MACHINE_DIR'], self.data['MACHINE_DESCRIPTION_FILENAME'])
        ConsolePrint.print_success(f"Update container description from {_desctipion_path}.")
        if os.path.isfile(_desctipion_path):
            _lxc_conf_file = os.path.join(self.data['PVE_LXC_CONF'], f'{MACHINE_ID}.conf')
            desc_org = open(_desctipion_path, 'r')
            desc_dest = open(_lxc_conf_file, 'a')
            for line in desc_org.readlines():
                desc_dest.write(f'\n#{line}')
            desc_org.close()
            desc_dest.close()
        ConsolePrint.print_success(f"Done")

    def __apply_lxc_setup(self):
        MACHINE_ID = self.data['MACHINE_DATA']['VMID']
        MACHINE_DIR = self.data['MACHINE_DIR']
        ConsolePrint.print_success(f"Rebooting machine with id={MACHINE_ID}.")
        execute_shell_command(f"pct reboot {MACHINE_ID}")
        ConsolePrint.print_success(f"Waiting 3 seconds.")
        execute_shell_command(f"sleep 3")
        ConsolePrint.print_success(f"copy post-install script/data files.")
        _rootfs_path = os.path.join(MACHINE_DIR, 'rootfs')
        _rootfs_zip_path = os.path.join(MACHINE_DIR, 'rootfs.tar.gz')
        _secret_file = os.path.join(MACHINE_DIR, 'env', 'password.txt')
        _setup_file = os.path.join(MACHINE_DIR, 'setup.sh')
        if os.path.isdir(_rootfs_path):
            ConsolePrint.print_success(f"\t- compress the rootfs folder ({_rootfs_path}.")
            execute_shell_command(f"tar -zvcf {_rootfs_zip_path} -C {_rootfs_path} .")
            ConsolePrint.print_success(f"\t- push the compressed rootfs folder to vm ({_rootfs_zip_path}.")
            execute_shell_command(f"pct push {MACHINE_ID} {_rootfs_zip_path} /root/rootfs.tar.gz")
        ConsolePrint.print_success(f"\t- push password file ({_secret_file}).")
        execute_shell_command(f"pct push {MACHINE_ID} {_secret_file} /root/secret")
        if os.path.isfile(_setup_file):
            ConsolePrint.print_success(f"\t- push the setup file to the virtual machine ({_setup_file}).")
            execute_shell_command(f"pct push {MACHINE_ID} {_setup_file} /root/setup.sh")
            ConsolePrint.print_success(f"\t- make the setup file executable.")
            execute_shell_command(f"pct exec {MACHINE_ID} chmod +x /root/setup.sh")
            ConsolePrint.print_success(f"\t- run the setup file.")
            ConsolePrint.print_debug('**************************************************')
            execute_shell_command(f"pct exec {MACHINE_ID} /root/setup.sh", stdout=True)
            ConsolePrint.print_debug('**************************************************')
        ConsolePrint.print_success(f"rebooting.")
        execute_shell_command(f"pct reboot {MACHINE_ID}")

        ConsolePrint.print_success(f"Work done.")


    def __destroy_old_vm(self): # TODO check the case where the container could not be stopped
        ConsolePrint.print_success(f"Destroy the old VM if it exists")
        res = execute_shell_command(f"qm stop {self.data['MACHINE_DATA']['VMID']} -skiplock")
        if res == 0:
            ConsolePrint.print_debug("Waiting 3 sec for VM to die")
            res = execute_shell_command(f"sleep 3")
            if self.data['MACHINE_DATA']['MAKE_BACKUP_BEFORE_DESTROY'] == 1:
                ConsolePrint.print_debug("Backup the old container")
                res = execute_shell_command(f"vzdump {self.data['MACHINE_DATA']['VMID']}")
    
        ConsolePrint.print_success("Deleting old container")
        res = execute_shell_command(f"qm destroy {self.data['MACHINE_DATA']['VMID']} --destroy-unreferenced-disks  --purge")

    def __create_vm_machine(self):
        ConsolePrint.print_success(f"Create a VM machine:")
        MACHINE_ID = self.data['MACHINE_DATA']['VMID']
        MACHINE_DATA = self.data['MACHINE_DATA']

        ## Machine VID, name, OS type, tags, architecture
        cmd = f"qm create {MACHINE_ID} --acpi 1"
        cmd += f" --name {MACHINE_DATA['HOSTNAME']}"
        cmd += f" --ostype {MACHINE_DATA['OSTYPE']}"
        cmd += f" --tags {MACHINE_DATA['TAGS']}"
        cmd += f" --arch {MACHINE_DATA['ARCH']}"
        cmd += f" --machine {MACHINE_DATA['MACHINE']}"
        cmd += f" --onboot {MACHINE_DATA['ONBOOT']}"
        #autostart = default is 0
        if MACHINE_DATA['ARCH']== 0:
            cmd += f" --tablet 0"
        

        ## VM agent
        if MACHINE_DATA['AGENT'] == '1':
            cmd += f" --agent enabled=1,freeze-fs-on-backup=1,fstrim_cloned_disks=1,type=virtio"
        else:
            cmd += f" --agent enabled=0"
        
        ## CPU/MEMORY and Machine type
        cmd += f" --memory {MACHINE_DATA['MEMORY']}"
        cmd += f" --cpu {MACHINE_DATA['CPU']}"
        cmd += f" --socket 1"
        cmd += f" --cores {MACHINE_DATA['CORES']}"
        if MACHINE_DATA['BALLOON'] == '1':
            cmd += f" --balloon {MACHINE_DATA['MEMORY']}"
        else:
            cmd += f" --balloon 0"

        ## BIOS
        if MACHINE_DATA['BIOS'] == 'seabios':
            cmd += f" --bios seabios"
        if MACHINE_DATA['BIOS'] == 'ovmf':
            cmd += f" --bios ovmf"
            cmd += f" --efidisk0 {MACHINE_DATA['STORAGE']}:vm-{MACHINE_ID}-disk-0,efitype=4m,pre-enrolled-keys=1,size=4M"
            cmd += f" --tpmstate0 {MACHINE_DATA['STORAGE']}:vm-{MACHINE_ID}-disk-2,size=4M,version=v2.0"

        ## Disk and boot
        if MACHINE_DATA['VM_IMAGE_NAME'] != '':
            cmd += f" --boot order=scsi0 --scsihw virtio-scsi-single"
            cmd += f" --scsi0 {MACHINE_DATA['STORAGE']}:0,import-from=\"{MACHINE_DATA['VM_IMAGE_NAME']}\",aio=native,cache=unsafe,discard=on,iothread=1,size=32G,ssd=1"
            # TODO aio=native or default to io_uring ?

        ## Network
        cmd += f" --net0 virtio,bridge={MACHINE_DATA['BRIDGE']},firewall=0"
        if MACHINE_DATA['VLAN'] != '':
           cmd += f",tag={MACHINE_DATA['VLAN']}"
        if MACHINE_DATA['IP2'] != '' and MACHINE_DATA['BRIDGE2'] != '' :
            cmd += f" --net1 model=virtio,bridge={MACHINE_DATA['BRIDGE2']},firewall=0"
            if MACHINE_DATA['VLAN2'] != '':
                cmd += f",tag={MACHINE_DATA['VLAN2']}"

        ## VGA
        if 'serial' in MACHINE_DATA['VGA']:
            cmd += f" --serial0 socket"
        cmd += f" --vga {MACHINE_DATA['VGA']}"


        ## CloudInit

        #cipassword: $5$BGSNkgN3$TvOzawviLbX07ZrqwEn.rA6nrHfuz4I.szqeIG1zyF0
        #ciuser: abc
        #ide0: local-lvm:vm-101-cloudinit,media=cdrom
        #ipconfig0: ip=10.10.10.10/24,gw=10.10.10.1,ip6=auto
        #searchdomain: pve01.lan
        #nameserver: 9.9.9.9
        # cdrom
        # cicustom
        # citype
        # ciupgrade
        # sshkeys
       
        
        print(cmd)
                                
        res = execute_shell_command(cmd)
        if res != 0:
            print(f"Machine not created. Check with the command line {cmd}")
            sys.exit(-1)
        
        print(f"Machine with id={MACHINE_ID} created.")

    def proceed(self):
        ConsolePrint.print_header2("")
        ConsolePrint.print_header2(f"#3 - Create the virtual Machine")
        ConsolePrint.print_header2("")
        

        if self.data['MACHINE_DATA']['MACHINE_TYPE'] == 'LXC':
            self.__destroy_old_lxc()
            self.__create_lxc_machine()
            self.__update_lxc_description()
            self.__apply_lxc_setup()


        elif self.data['MACHINE_DATA']['MACHINE_TYPE'] == 'VM':
            self.__destroy_old_vm()
            self.__create_vm_machine()
            self.__update_vm_description()
            self.__apply_vm_setup()

            #qm shutdown <vmid> --forceStop --skiplock

        else:
            ConsolePrint.print_fail(f"Error: machine type not recoginzed: {self.data['MACHINE_DATA']['MACHINE_TYPE']}.")
            self.__proceed_exit()
    
        