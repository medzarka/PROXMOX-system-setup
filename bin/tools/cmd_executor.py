
import subprocess

from tools.console_printing import ConsolePrint

def execute_shell_command(cmd, stdout=True, stderr=True, exitOnError=True):
    '''
    Execute a given command in shell
    '''
    try:
        process_output = subprocess.run(cmd.split(), capture_output=True, text=True)
        if stdout and process_output.stdout != '':
            ConsolePrint.print_debug(f'Process output is: {process_output.stdout}')
        if stderr and process_output.stderr != '':
            ConsolePrint.print_warn(f'Process Errors: {process_output.stderr}')
        return process_output.returncode
    except FileNotFoundError:
        ConsolePrint.print_fail("Error --> Command not found")
        if exitOnError:
            return -1