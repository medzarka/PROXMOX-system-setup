import sys
import os

from tools.console_printing import ConsolePrint
from tools.config_loader import Configurations
from tools.password_generator import PasswordGenerator
from tools.cmd_executor import execute_shell_command

class VM_LoadConfigurations:

    def __init__(self, data=[], exitOnError=True):

        self.data=data
        self.exitOnError=exitOnError

        self.COMMON_CONFIG=['MACHINE_TYPE', 'VMID', 'ARCH', 'CORES', 'DESCRIPTION', 'HOSTNAME', 
                            'MEMORY', 'NAMESERVER', 'SEARCHDOMAIN', 'ONBOOT', 'TAGS', 'STORAGE', 
                            'START', 'SSH-KEYS', 'OSTYPE', 'IP', 'GW', 'DNS', 'BRIDGE', 'VLAN', 
                            'IP2', 'BRIDGE2', 'VLAN2', 'DISK_SIZE', 'VM_IMAGE_NAME', 'VM_IMAGE_URL',
                            'MAKE_BACKUP_BEFORE_DESTROY', 'PASSWORD']

        self.LXC_CONFIG=['FEATURES', 'SWAP', 'TIMEZONE', 'IMPRIVILEGED' ]
        
        self.VM_CONFIG=['AGENT', 'ARCH', 'BALLOON', 'BIOS', 'CPU', 'OSTYPE',  'TABLET', 'VGA', 'MACHINE' ] # TODO check the list
        

        self.COMMON_DEFAULTS= {'MACHINE_TYPE': None, 
                        'VMID' : None, 
                        'CORES': 1, 
                        'HOSTNAME' : None, 
                        'DESCRIPTION': '',
                        'MEMORY': 1024,
                        'NAMESERVER': '9.9.9.9', # Quad9 DNS
                        'SEARCHDOMAIN': 'bluewave.pve01.lan',
                        'ONBOOT': 0, 
                        'TAGS': '',
                        'STORAGE': 'local-lvm',
                        'START': 0,
                        'SSH-KEYS': '',
                        'IP': None, 
                        'GW': None, 
                        'DNS': None, 
                        'BRIDGE': None,  
                        'VLAN': '',  
                        'IP2': '',  
                        'BRIDGE2': '', 
                        'VLAN2': '',
                        'DISK_SIZE': 4,
                        'VM_IMAGE_NAME': None,
                        'VM_IMAGE_URL': None,
                        'PASSWORD': '',
                        'MAKE_BACKUP_BEFORE_DESTROY':0,
                    }
        
        self.DEFAULTS_LXC = {'ARCH': ['amd64', ['amd64', 'arm64', 'armhf', 'i386', 'riscv32', 'riscv64']],
                            'OSTYPE': ['unmanaged', ['alpine', 'archlinux', 'centos', 'debian', 'devuan', 'fedora', 'gentoo', 'nixos', 'opensuse', 'ubuntu', 'unmanaged']],
                            'FEATURES': 'keyctl=1,nesting=1,fuse=1',
                            'SWAP': 512, 
                            'TIMEZONE': 'Asia/Riyadh', 
                            'IMPRIVILEGED': 1
                    }
        
        self.DEFAULTS_VM = {'AGENT': ['1', ['1', '0']],
                            'ARCH': ['x86_64', ['aarch64', 'x86_64']],
                            'BALLOON': ['1', ['1', '0']],
                            'BIOS': ['seabios', ['seabios', 'ovmf']],
                            'CPU': ['host', ['host', 'kvm64', 'x86-64-v2-AES', 'x86-64-v3', 'x86-64-v4' ]], #https://pve.proxmox.com/pve-docs/pve-admin-guide.html#chapter_qm_vcpu_list
                            'OSTYPE' : ['l26', ['l24', 'l26', 'other', 'solaris', 'w2k', 'w2k3', 'w2k8', 'win10', 'win11', 'win7', 'win8', 'wvista', 'wxp']],
                            'TABLET': ['1', ['1', '0']],
                            'VGA': ['serial0', ['cirrus', 'none', 'qxl', 'qxl2', 'qxl3', 'qxl4', 'serial0', 'serial1', 'serial2', 'serial3', 'std', 'virtio', 'virtio-gl', 'vmware']], # TODO update the possible values
                            'MACHINE': ['q35', ['i440fx', 'q35']],

                            # CIPASSWORD is PASSWORD
                            #'CIUSER': ['x86_64', ['aarch64', 'x86_64']],
                            #'CIPASSWORD': ['x86_64', ['aarch64', 'x86_64']],
                            #'CIUPGRADE': ['x86_64', ['aarch64', 'x86_64']],                            
                            #'CDROM': ['x86_64', ['aarch64', 'x86_64']],
                            #'CICUSTOM': ['x86_64', ['aarch64', 'x86_64']],                            
                            #'CITYPE': ['x86_64', ['aarch64', 'x86_64']],
                            #'CIUPGRADE': ['x86_64', ['aarch64', 'x86_64']],
                            
                    }

        self.CONFIG = {}
        self.DEFAULTS = {}

    def __check_password(self):
        if self.data['MACHINE_DATA']['PASSWORD'] is None or self.data['MACHINE_DATA']['PASSWORD'] == '':
            __env_dir = os.path.join(self.data['MACHINE_DIR'], 'env')
            __pass_file = os.path.join(__env_dir, 'password.txt')

            if not os.path.exists(__env_dir):
                os.makedirs(__env_dir)

            if os.path.isfile(__pass_file):
                f=open(__pass_file, 'r')
                self.data['MACHINE_DATA']['PASSWORD']=f.read()
                f.close()
                ConsolePrint.print_success(f"Password loaded from {__pass_file}.") 
            else:
                self.data['MACHINE_DATA']['PASSWORD']=PasswordGenerator.generate_password()
                f=open(__pass_file, 'w')
                f.write(self.data['MACHINE_DATA']['PASSWORD'])
                f.close()
                ConsolePrint.print_success(f"New password is generated in {__pass_file}.")
    
    def __check_sshkey(self):
        # TODO generating ssh key depends on machine type !

        __env_dir = os.path.join(self.data['MACHINE_DIR'], 'env')
        if not os.path.exists(__env_dir):
                os.makedirs(__env_dir)

        if self.data['MACHINE_DATA']['SSH-KEYS'] is None or self.data['MACHINE_DATA']['SSH-KEYS'] == '':
            
            # first, we check if we have already an ssh-key in var folder, else, we create one
            __id_rsa__file = os.path.join(__env_dir, 'id_rsa') 
            __id_rsa_pub__file = os.path.join(__env_dir, 'id_rsa.pub') 

            if os.path.isfile(__id_rsa__file) and os.path.isfile(__id_rsa_pub__file):
                self.data['MACHINE_DATA']['SSH-KEYS'] = __id_rsa_pub__file
                ConsolePrint.print_success(f"SSH-KEYS updated to {__id_rsa_pub__file}.") 
            else:
                res = execute_shell_command(f"ssh-keygen -t rsa -b 4096 -N '' -f {__id_rsa__file}")
                if res != 0:
                    ConsolePrint.print_fail(f"Error: unable to create ssh key in {__id_rsa__file}.")
                    self.__proceed_exit()
                self.data['MACHINE_DATA']['SSH-KEYS'] = __id_rsa_pub__file
                ConsolePrint.print_success(f"New public ssh key is generated in {__id_rsa_pub__file}.")

            
        else:
            # we check if the provided file exists or no
            __key_file = self.data['MACHINE_DATA']['SSH-KEYS']
            if not os.path.isfile(__key_file):
                ConsolePrint.print_fail(f"Error: SSH-KEY file does not exist ({__key_file}).") 
                ConsolePrint.print_fail(f"Check if you entered an absolute path and not a relative one.") 
                self.__proceed_exit()

    def __check_vm_image(self):
         
        # check if the vm image exists. else download it. if not possible, stop with error
        __vm_image_path = os.path.join(self.data['PVE_CACHE_PATH'], self.data['MACHINE_DATA']['VM_IMAGE_NAME'])
        if not os.path.isfile(__vm_image_path):
            ConsolePrint.print_warn(f"The image file is not found ({self.data['MACHINE_DATA']['VM_IMAGE_NAME']}).")
            if self.data['MACHINE_DATA']['VM_IMAGE_URL'] is None or len(self.data['MACHINE_DATA']['VM_IMAGE_URL']) == 0:
                ConsolePrint.print_fail(f"Error: The vm image is not privided and could not be downloaded.")
                self.__proceed_exit()

            print(f"Downloading the image file to {__vm_image_path}")
            res = execute_shell_command(f"wget {self.data['MACHINE_DATA']['VM_IMAGE_URL']} -O {__vm_image_path}")
            if res != 0:
                ConsolePrint.print_fail(f"Error: unable to download image file from {self.data['MACHINE_DATA']['VM_IMAGE_URL']}.")
                self.__proceed_exit()
            print(f"Image file is downloaded.")

    def __update_defaults(self):
        self.DEFAULTS= {}

    def __proceed_exit(self):
        if self.exitOnError:
            sys.exit(-1)

    def proceed(self):
        ConsolePrint.print_header2("")
        ConsolePrint.print_header2(f"#2 - Reading machine configurations")
        ConsolePrint.print_header2("")
        
        # Read configurations 
        __conf = Configurations(os.path.join(self.data['MACHINE_DIR'], self.data['MACHINE_INI_FILENAME']))
        self.data['MACHINE_TYPE'] = __conf.readConfig('MACHINE', 'MACHINE_TYPE')

        # Extract machine type
        if self.data['MACHINE_TYPE'] == 'LXC':
            ConsolePrint.print_success(f"Machine type ... {self.data['MACHINE_TYPE']}")
            self.CONFIG = self.COMMON_CONFIG + self.LXC_CONFIG
            self.DEFAULTS = {**self.COMMON_DEFAULTS, **self.DEFAULTS_LXC}

        elif self.data['MACHINE_TYPE'] == 'VM':
            ConsolePrint.print_success(f"Machine type ... {self.data['MACHINE_TYPE']}")
            self.CONFIG = self.COMMON_CONFIG + self.VM_CONFIG
            self.DEFAULTS = {**self.COMMON_DEFAULTS, **self.DEFAULTS_VM}
            #self.__proceed_exit()
            # TODO update self.DEFAULTS_VM

        else:
            ConsolePrint.print_fail(f"Error: Machine Type not recognized ({self.data['MACHINE_TYPE']}).")
            self.__proceed_exit() 

        # Extract machine configurations
        self.data['MACHINE_DATA'] = {}
                
        for _data in self.CONFIG:
            self.data['MACHINE_DATA'][_data] = __conf.readConfig('MACHINE', _data)
            if self.data['MACHINE_DATA'][_data] is None or len(self.data['MACHINE_DATA'][_data]) == 0:
                if _data in self.DEFAULTS.keys():
                    if self.DEFAULTS[_data] is None:
                        ConsolePrint.print_fail(f"Error: The mandatory configuration {_data} is not defined.")
                        self.__proceed_exit()
                    else:
                        if type(self.DEFAULTS[_data]) == list:
                            self.data['MACHINE_DATA'][_data] = self.DEFAULTS[_data][0]
                        else:
                            self.data['MACHINE_DATA'][_data] = self.DEFAULTS[_data]
                        ConsolePrint.print_warn(f"Warning: Default value is provided for the option '{_data}={self.data['MACHINE_DATA'][_data]}' .")
            else:
                if type(self.DEFAULTS[_data]) == list and self.data['MACHINE_DATA'][_data] not in self.DEFAULTS[_data][1]:
                    ConsolePrint.print_fail(f"Error: The configuration {_data}={self.data['MACHINE_DATA'][_data]} is not correct.")
                    self.__proceed_exit() 
                    
                ConsolePrint.print_success(f"The option {_data} is set to {self.data['MACHINE_DATA'][_data]} .")
        
        self.__check_password()
        self.__check_sshkey()
        self.__check_vm_image()

        return self.data
