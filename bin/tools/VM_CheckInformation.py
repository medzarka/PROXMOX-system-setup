import sys
import os

from tools.console_printing import ConsolePrint

class VM_CheckInformation:

    def __init__(self, data=[], exitOnError=True):

        self.data=data
        self.exitOnError=exitOnError

    def __proceed_exit(self):
        if self.exitOnError:
            sys.exit(-1)

    def proceed(self):

        self.data['MACHINE_ID'] = None
        self.data['MACHINE_DIR'] = None

        ConsolePrint.print_header2("#1 - Checking the machine provided information")
        ConsolePrint.print_header2("")
        
        #-------------------------------------------------------------------------
        # check if the machine ID is provided
        if len(sys.argv) == 2:
            self.data['MACHINE_ID'] = sys.argv[1]
            ConsolePrint.print_success(f"does machine ID provided? ... Ok")
            
        if self.data['MACHINE_ID'] is None:
            ConsolePrint.print_fail(f"Error: The machine ID has to be provided as a parameter.")
            self.__proceed_exit()
        
        #-------------------------------------------------------------------------
        # check if the machine folder exists 
        for filename in os.listdir(self.data['MACHINES_PATH']):
            if os.path.isdir(os.path.join(self.data['MACHINES_PATH'], filename)) and filename.startswith(f"{self.data['MACHINE_ID']}_"):
                self.data['MACHINE_DIR']=os.path.join(self.data['MACHINES_PATH'], filename)
                break
        if self.data['MACHINE_DIR'] is None:
            ConsolePrint.print_fail(f"Error: Unable to find the directoy {os.path.join(self.data['MACHINES_PATH'], self.data['MACHINE_ID'])}_xxxx.")
            self.__proceed_exit()
        ConsolePrint.print_success(f"does machine folder exist? ... Ok")

        #-------------------------------------------------------------------------
        # check if the machine information exist
        msg = ''
        if not os.path.isdir(os.path.join(self.data['MACHINE_DIR'], self.data['MACHINE_ROOTFS_DIRNAME'])):
            msg += f"The rootfs folder does not exist in {self.data['MACHINE_DIR']}"
        if not os.path.isfile(os.path.join(self.data['MACHINE_DIR'], self.data['MACHINE_INI_FILENAME'])):
            msg += f"\nThe machine ini file does not exist in {self.data['MACHINE_DIR']}"
        if not os.path.isfile(os.path.join(self.data['MACHINE_DIR'], self.data['MACHINE_DESCRIPTION_FILENAME'])):
            msg += f"\nThe machine description file does not exist in {self.data['MACHINE_DIR']}"


        if len(msg) == 0:
            ConsolePrint.print_success(f"does machine required files exist? ... Ok")
        else:
            ConsolePrint.print_fail(f"Error: missing information:")
            ConsolePrint.print_fail(msg)
            self.__proceed_exit()
        
        return self.data
