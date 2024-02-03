
import sys
import os

class ConsolePrint:
    '''
    More in https://talyian.github.io/ansicolors/
    '''

    #########################################################################
    ## screen cleaning
    @staticmethod
    def clean_screen():
        os.system('clear' if os.name == 'posix' else 'cls')

    #########################################################################
    ## Headers
    @staticmethod
    def print_header1(message, end = '\n'):
        sys.stdout.write('\x1b[44m' + ""  + '\x1b[0m' + end)
        sys.stdout.write('\x1b[44m' + message.strip()  + '\x1b[0m' + end)
        sys.stdout.write('\x1b[44m' + ""  + '\x1b[0m' + end)

    @staticmethod
    def print_header2(message, end = '\n'):
        sys.stdout.write('\x1b[44m' + ""  + '\x1b[0m' + end)
        sys.stdout.write('\x1b[46m' + message.strip()  + '\x1b[0m' + end)

    ##########################################################################
    ## Logging
    @staticmethod
    def print_debug(message, end = '\n'):
        sys.stdout.write('\x1b[47m' + message.strip() + '\x1b[0m' + end)

    @staticmethod
    def print_info(message, end = '\n'):
        sys.stdout.write('\x1b[1;34m' + message.strip() + '\x1b[0m' + end)

    @staticmethod
    def print_warn(message, end = '\n'):
        sys.stdout.write('\x1b[1;33m' + message.strip() + '\x1b[0m' + end)

    @staticmethod
    def print_fail(message, end = '\n'):
        sys.stdout.write('\x1b[1;31m' + message.strip() + '\x1b[0m' + end)

    @staticmethod
    def print_success(message, end = '\n'):
        sys.stdout.write('\x1b[32m' + message.strip() + '\x1b[0m' + end)

    @staticmethod
    def print_bold(message, end = '\n'):
        sys.stdout.write('\x1b[1;37m' + message.strip() + '\x1b[0m' + end)

    