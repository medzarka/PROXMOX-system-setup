
import os
import sys
import shutil

from tools.console_printing import ConsolePrint
from tools.config_loader import Configurations
from tools.cmd_executor import execute_shell_command

my_path = __file__
TMP_WORK_DIR=os.path.join(os.path.dirname(__file__), 'tmp')
os.makedirs(TMP_WORK_DIR,exist_ok=True)

PVE_CACHE_PATH="/var/lib/vz/template/cache"
ALPINE_TEMPLATE_SCRIPT=os.path.join(os.path.dirname(__file__), 'tools', 'alpine-make-vm-image')
ALPINE_TEMPLATE_DATA_FOLDER=os.path.join(os.path.dirname(os.path.dirname(__file__)), 'vm_templates', 'alpine')
ALPINE_TEMPLATE_ROOTFS=os.path.join(ALPINE_TEMPLATE_DATA_FOLDER, 'rootfs')
ALPINE_TEMPLATE_PACKAGES=os.path.join(ALPINE_TEMPLATE_DATA_FOLDER, 'packages')
ALPINE_TEMPLATE_REPOSITORIES=os.path.join(ALPINE_TEMPLATE_DATA_FOLDER, 'repositories')
ALPINE_TEMPLATE_SETUP=os.path.join(ALPINE_TEMPLATE_DATA_FOLDER, 'setup.sh')
ALPINE_TEMPLATE_INFO_FILE=os.path.join(ALPINE_TEMPLATE_DATA_FOLDER, 'alpine_info.ini')

ALPINE_TEMPLATE_REQUIRED_INFO=['ALPINE_VERSION', 'IMAGE_NAME', 'IMAGE_SIZE']
ALPINE_TEMPLATE_INFO={}


__is_ok = True
ConsolePrint.clean_screen()


ConsolePrint.print_header1('Create an Apline Linux VM template')


####################################################################
ConsolePrint.print_header2('1 - Create temporary work directroy:')
os.makedirs(TMP_WORK_DIR,exist_ok=True)
if os.path.isdir(TMP_WORK_DIR):
    ConsolePrint.print_success(f"The TMP dir is created ({TMP_WORK_DIR})")
else:
    __is_ok=False
    ConsolePrint.print_fail(f"The TMP dir could not be created ({TMP_WORK_DIR})")

####################################################################
ConsolePrint.print_header2('2 - Check VM template required resources:')



# alpine template script exists
if os.path.isfile(ALPINE_TEMPLATE_SCRIPT):
    ConsolePrint.print_success(f"The alpine script to create a template exists ({ALPINE_TEMPLATE_SCRIPT}) ")
    os.chmod(ALPINE_TEMPLATE_SCRIPT , 0o777)
else:
    ConsolePrint.print_fail(f"The alpine script to create a template does not exist ({ALPINE_TEMPLATE_SCRIPT}) ")
    __is_ok = False

# alpine data folder exists
if os.path.isdir(ALPINE_TEMPLATE_DATA_FOLDER):
    ConsolePrint.print_success(f"The alpine data folder exists ({ALPINE_TEMPLATE_DATA_FOLDER}) ")
else:
    ConsolePrint.print_fail(f"The alpine data folder does not exist ({ALPINE_TEMPLATE_DATA_FOLDER}) ")
    __is_ok = False

# alpine rootfs folder exists
if os.path.isdir(ALPINE_TEMPLATE_ROOTFS):
    ConsolePrint.print_success(f"The alpine template rootfs folder exists ({ALPINE_TEMPLATE_ROOTFS}) ")
else:
    ConsolePrint.print_fail(f"The alpine template rootfs folder does not exist ({ALPINE_TEMPLATE_ROOTFS}) ")
    __is_ok = False

# alpine packages list exists
if os.path.isfile(ALPINE_TEMPLATE_PACKAGES):
    ConsolePrint.print_success(f"The alpine packages list file exists ({ALPINE_TEMPLATE_PACKAGES}) ")
else:
    ConsolePrint.print_fail(f"The alpine packages list file does not exist ({ALPINE_TEMPLATE_PACKAGES}) ")
    __is_ok = False

# alpine setup script exists
if os.path.isfile(ALPINE_TEMPLATE_SETUP):
    ConsolePrint.print_success(f"The alpine setup script file exists ({ALPINE_TEMPLATE_SETUP}) ")
    os.chmod(ALPINE_TEMPLATE_SETUP , 0o777)
else:
    ConsolePrint.print_fail(f"The alpine setup script file does not exist ({ALPINE_TEMPLATE_SETUP}) ")
    __is_ok = False

# alpine repositories list exists
if os.path.isfile(ALPINE_TEMPLATE_REPOSITORIES):
    ConsolePrint.print_success(f"The alpine repositories list file exists ({ALPINE_TEMPLATE_REPOSITORIES}) ")
else:
    ConsolePrint.print_fail(f"The alpine repositories list file does not exist ({ALPINE_TEMPLATE_REPOSITORIES}) ")
    __is_ok = False

# alpine information list exists
if os.path.isfile(ALPINE_TEMPLATE_INFO_FILE):
    ConsolePrint.print_success(f"The alpine information list file exists ({ALPINE_TEMPLATE_INFO_FILE}) ")
    # alpine information are complete ?
    __conf = Configurations(ALPINE_TEMPLATE_INFO_FILE)
    ALPINE_TEMPLATE_INFO['MACHINE_TYPE'] = __conf.readConfig('ALPINE', 'MACHINE_TYPE')
    for _info in ALPINE_TEMPLATE_REQUIRED_INFO:
        ALPINE_TEMPLATE_INFO[_info] = __conf.readConfig('ALPINE', _info)
        if ALPINE_TEMPLATE_INFO[_info] is None or ALPINE_TEMPLATE_INFO[_info] == '':
            ConsolePrint.print_fail(f"Missing information: {_info}")
            __is_ok = False

else:
    ConsolePrint.print_fail(f"The alpine information list file does not exist ({ALPINE_TEMPLATE_INFO_FILE}) ")
    __is_ok = False


if __is_ok is False:
    ConsolePrint.print_fail(f"Script aborded because some issues raised.")
else:
    ConsolePrint.print_success(f"Start virtual machine template creation:")
    cmd = f"{ALPINE_TEMPLATE_SCRIPT}"
    cmd += f" --image-format raw"
    cmd += f" --image-size {ALPINE_TEMPLATE_INFO['IMAGE_SIZE']}G"
    cmd += f" --partition"
    cmd += f" --repositories-file {ALPINE_TEMPLATE_REPOSITORIES}"
    cmd += f" --packages \""
    _startLine=True
    with open(ALPINE_TEMPLATE_PACKAGES, 'r') as f:
        for _line in f.readlines():
            if _startLine:
                cmd += f"{_line.replace(os.linesep, '')}"
                _startLine=False
            else:
                cmd += f" {_line.replace(os.linesep, '')}"
    cmd += f"\""
    cmd += f" --fs-skel-dir {ALPINE_TEMPLATE_ROOTFS}"
    cmd += f" --fs-skel-chown root:root"
    cmd += f" --script-chroot"
    ALPINE_TEMPLATE_IMAGE_FILE_TMP_FULLPATH= os.path.join(TMP_WORK_DIR, ALPINE_TEMPLATE_INFO['IMAGE_NAME'])
    cmd += f" {ALPINE_TEMPLATE_IMAGE_FILE_TMP_FULLPATH} -- {ALPINE_TEMPLATE_SETUP}"

    ConsolePrint.print_debug(f"---------------------")
    ConsolePrint.print_debug(f"Executing the command : {cmd}")
    ConsolePrint.print_debug(f"---------------------")

    res = execute_shell_command(cmd)
    if res == 0:
        ConsolePrint.print_success("The alpine template creation script ended with success")
        ALPINE_TEMPLATE_IMAGE_FILE_FULLPATH=os.path.join(PVE_CACHE_PATH, ALPINE_TEMPLATE_INFO['IMAGE_NAME'])
        res = execute_shell_command(f"cp -f {ALPINE_TEMPLATE_IMAGE_FILE_TMP_FULLPATH} {ALPINE_TEMPLATE_IMAGE_FILE_FULLPATH}")
        if res == 0:
            ConsolePrint.print_success("The alpine template file is copied to the PVE templates cache ({PVE_CACHE_PATH})")
        else:
            ConsolePrint.print_fail(f"The alpine template file could not be copied to the PVE templates cache ({PVE_CACHE_PATH})")

    else:
        ConsolePrint.print_fail(f"The alpine template creation script ended with sone issues. (exit code = {res})")

####################################################################
ConsolePrint.print_header2('Clean temporary work directroy:')

shutil.rmtree(TMP_WORK_DIR, ignore_errors=False)
execute_shell_command("rm -rf /tmp/alpine-make-vm-image*")

if not os.path.isdir(TMP_WORK_DIR):
    ConsolePrint.print_success(f"The alpine temporary work directroy is cleaned ({TMP_WORK_DIR}) ")
else:
    ConsolePrint.print_fail(f"The alpine temporary work directroy could not be cleaned ({TMP_WORK_DIR}) ")


#sudo rm -rf $ALPINE_IMAGE_NAME
#sudo ./alpine-make-vm-image \
#              --image-format raw \
#              --image-size ${DISK_SIZE}G \
#              --partition \
#              --repositories-file scripts/repositories \
#              --packages "$(cat ${PACKAGE_FILE})" \
#              --fs-skel-dir ${SKEL_DIR} \
#              --fs-skel-chown root:root \
#              --script-chroot \
#              ${ALPINE_IMAGE_NAME} -- ./scripts/configure.sh