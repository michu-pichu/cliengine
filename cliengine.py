import cmd
import sys
# import subprocess
from enum import Enum
import logging
import signal
import threading
import argparse

# valid workers
class ValidWorkers(str, Enum):
   testworker1 = 'tw1'
   testworker2 = 'tw2'
   testworker3 = 'tw3'

# valid timer modes
class ValidTimerModes(str, Enum):
   add = 'add'
   set = 'set'
   clear = 'clear'

# import background worker classes
# Base class for background worker (ThreadingBgWorker)
from threadingbgworker import ThreadingBgWorker

shellname = 'myshell'

# --------- Valid Workers - Definitions ------------
# Test class for background worker (tw)
# ValidWorker: wt --> Class: TestBgWorker
class TestBgWorker(ThreadingBgWorker):
    def __init__(self, name, event):
        super().__init__(name=name, event=event, slowDownSec=1, timerMin=1, cli_name=shellname)
        self.iterations = 0

    def addToJobRun(self):
        pass

    def specificStatus(self) -> dict:
        return {'iterations': self.iterations}
    
    def taskForTimerEnd(self):
        print(f'Worker {self.name} timer end.')
    
    def taskForStop(self):
        print(f'Worker {self.name} stopped.')

worker_definitons = {
    'tw1': TestBgWorker,
    'tw2': TestBgWorker,
    'tw3': TestBgWorker,
}
# --------- Valid Workers - Definitions ------------


# Class leadApiCLI that manages background processes
class cliEngine(cmd.Cmd):


    def __init__(self,
                 shellname,
                 worker_events,
                 valid_workers,
                 logger):

        super().__init__()
        self._make_intro(shellname)
        self.background_processes = {}
        self.prompt = f'{shellname}> '
        self.events = worker_events
        self.valid_workers = valid_workers
        self.logger = logger
        self.logger.info(f'{shellname} started.')


    def _make_intro(self, shellname):
        intro = '------------------------------------------------------------------------\n'
        intro += f'Welcome to the {shellname}.\n'
        intro += '------------------------------------------------------------------------\n'
        intro += '\n'
        intro += '  Type help or ?      to list commands.\n'
        intro += "  Type start <name>   to start a background process.\n"
        intro += "  Type stop <name>    to stop a background process.\n"
        intro += "  Type timer <name> <mode> <value> to set a timer for the process.\n"
        intro += "  Type list           to list all working background processes.\n"
        intro += "  Type status <name>  to get the status of a background process.\n"
        intro += "  Type status_all     to get the status of all background processes.\n"
        intro += "  Type help <command> to get help for a specific command.\n"
        intro += "  Type exit or quit   to leave the shell.\n"
        intro += '\n'
        intro += "  Valid names are:\n"
        for worker in ValidWorkers:
            intro += f'    {worker.value}\n'
        intro += '\n'
        intro += f"Warning: Stopping this {shellname} will also stop all started\n"
        intro += "background processes.\n"
        intro += f"For more information, please contact the {shellname} administrator.\n"
        intro += '------------------------------------------------------------------------\n'


    def validate_name(self, name):
        """Checks if the procesname is valid."""
        check = False
        for worker in ValidWorkers:
            if name == worker.value:
                check = True
                break
        
        if not check:
            print(f'Error: Process {name} does not exist or is not valid.')
            self.logger.error(f'Error: Process {name} does not exist or is not valid.')
            return False
        
        return True


    def clear_events_and_processes(self):
        """Clears all events and processes."""

        # clear processes those events are set
        for name, event in self.events.items():
            # stop process if the event is set
            if event.is_set():
                if name in self.background_processes:
                    process = self.background_processes[name]
                    process.stop()
                    del self.background_processes[name]

        # remove all processes that are not alive
        for process in self.background_processes:
            if not self.background_processes[process].is_alive():
                del self.background_processes[process]

        for event in self.events:
            if self.events[event].is_set():
                self.events[event].clear()


    def check_name_for_start(self, name):
        """Checks if the procesname is valid and if the process is already running."""
        if not self.validate_name(name):
            return False
        
        # clear events and processes
        self.clear_events_and_processes()

        # check if name is already in use
        if name in self.background_processes:
            print(f'Error: Process {name} is already running.')
            self.logger.error(f'Error: Process {name} is already running.')
            return False
        
        return True
    

    def check_name_for_stop(self, name):
        """Checks if the procesname is valid and if the process is running."""
        if not self.validate_name(name):
            return False

        # check if name is already in use
        if name not in self.background_processes:
            print(f'Error: Process {name} is not running.')
            self.logger.error(f'Error: Process {name} is not running.')
            return False

        return True
    

    def check_name_for_prozess_update(self, name):
        """Checks if the procesname is valid and if the process is running."""
        if not self.validate_name(name):
            return False

        # clear events and processes
        self.clear_events_and_processes()

        # check if name is already in use
        if name not in self.background_processes:
            print(f'Error: Process {name} is not running.')
            self.logger.error(f'Error: Process {name} is not running.')
            return False

        return True


    def do_start(self, name):
        """Starts a background process with the given name."""
        print(f'Starting process: {name}')
        self.logger.info(f'Starting process: {name}')

        if not self.check_name_for_start(name):
            return

        process = worker_definitons[name](name=name, event=self.events[name])
        process.start()
        self.background_processes[name] = process
        print(f'Started process: {name}')
        self.logger.info(f'Started process: {name}')


    def help_start(self):
        print('Starts a background process with the given name.')
        print('Usage: start <name>')
        print('Valid names are:')
        for worker in ValidWorkers:
            print(f'  {worker.value}')


    def do_stop(self, name):
        """Stops a background process with the given name."""
        print(f'Stopping process: {name}')
        self.logger.info(f'Stopping process: {name}')

        if not self.check_name_for_stop(name):
            return

        process = self.background_processes[name]
        process.stop()
        process.join()
        del self.background_processes[name]
        self.logger.info(f'Stopped process: {name}')
        print(f'Stopped process: {name}')


    def help_stop(self):
        print('Stops a background process with the given name.')
        print('Usage: stop <name>')


    def do_timer(self, arg):
        """Sets a timer for a background process."""

        arguments = self._splitline(arg)
        # check if arguments are valid
        if len(arguments) == 3:
            worker_name = arguments[0]
            timer_mode = arguments[1]
            timer_value_min = arguments[2]
            self.logger.debug(f'Worker name: {worker_name}, timer mode: {timer_mode}, timer value: {timer_value_min}')
        elif len(arguments) == 2:
            worker_name = arguments[0]
            timer_mode = arguments[1]
            self.logger.debug(f'Worker name: {worker_name}, timer mode: {timer_mode}')
            if timer_mode == ValidTimerModes.clear.value:
                timer_value_min = None
            else:
                print('Error: Invalid number of arguments.')
                self.logger.error('Error: Invalid number of arguments.')
                self.help_timer()
                return
        else:
            print('Error: Invalid number of arguments.')
            self.logger.error('Error: Invalid number of arguments.')
            self.help_timer()
            return
        
        # check if worker_name is in ValidWorkers Enum
        if not self.check_name_for_prozess_update(worker_name):
            self.help_timer()
            return

        # check if timer_mode is in ValidTimerModes Enum
        check = False
        for mode in ValidTimerModes:
            if timer_mode == mode.value:
                check = True
                break
        if not check:
            print(f'Error: Invalid timer mode {mode}.')
            self.logger.error(f'Error: Invalid timer mode {mode}.')
            self.help_timer()
            return

        try:
            timer_value_min = float(timer_value_min)
        except ValueError:
            print(f'Error: Invalid timer value {timer_value_min}.')
            self.logger.error(f'Error: Invalid timer value {timer_value_min}.')
            self.help_timer()
            return
        if timer_value_min <= 0:
            print(f'Error: Invalid timer value {timer_value_min}.')
            self.logger.error(f'Error: Invalid timer value {timer_value_min}.')
            self.help_timer()
            return
        # set timer
        if worker_name in self.background_processes:
            process = self.background_processes[worker_name]
            if timer_mode == ValidTimerModes.add.value:
                process.set_timer(timerMin=timer_value_min, timerMode=timer_mode)
            elif timer_mode == ValidTimerModes.set.value:
                process.set_timer(timerMin=timer_value_min, timerMode=timer_mode)
            elif timer_mode == ValidTimerModes.clear.value:
                process.set_timer(timerMin=None, timerMode=timer_mode)
            else:
                print(f'Error: Invalid timer mode.')
                self.logger.error(f'Error: Invalid timer mode.')
                self.help_timer()
                return
            print(f'Set timer: {worker_name}, timer_mode {timer_mode}, {timer_value_min} minutes.')
            self.logger.info(f'Set timer: {worker_name}, timer_mode {timer_mode}, {timer_value_min} minutes.')


    def help_timer(self):
        print('Usage: timer <worker_name> <timer_mode> <timer_value_min>')
        print('   or: timer <worker_name> clear')
        line = '   worker_name: ' + str([member.value for member in ValidWorkers])
        print(line)
        line = '   timer_mode: ' + str([member.value for member in ValidTimerModes])
        print(line)
        print('   timer_value_min: <int> or <float> in minutes')


    def do_list(self, arg):
        """Lists all background processes."""
        self.logger.info('Listing all background processes.')

        # clear events and processes
        self.clear_events_and_processes()

        if len(self.background_processes) == 0:
            print(' ...no background processes running.')
            self.logger.info(' ...no background processes running.')
            return

        for name, process in self.background_processes.items():
            print(f'{name}: runtime: {process.get_runtime()}')


    def help_list(self):
        print('Lists all background processes.')
        print('Usage: list')


    # show status of a background process with the given name
    def do_status(self, name):
        """Shows the status of a background process with the given name."""
        self.logger.info(f'Showing status of process: {name}')
        if name not in self.background_processes:
            print('Error: Process does not exist.')
            return
        
        process = self.background_processes[name]
        # stop process if it the event is set
        if self.events[name].is_set() or not process.is_alive():
            print(f'Process {name} has stopped.')
            process.stop()
            del self.background_processes[name]
            return
        
        print(f'{name}: ')
        for key, value in process.get_status().items():
            print(f'    {key}: {value}')


    def help_status(self):
        print('Shows the status of a background process with the given name.')
        print('Usage: status <name>')


    # show status of all background processes
    def do_status_all(self, arg):
        """Shows the status of all background processes."""
        self.logger.info('Showing status of all background processes.')

        # clear events and processes
        self.clear_events_and_processes()

        if not self.background_processes:
            print('No active processes.')
        else:
            # for name, event in self.events.items():
            #     # stop process if it the event is set
            #     if event.is_set():
            #         print(f'Process {name} has stopped.')
            #         if name in self.background_processes:
            #             process = self.background_processes[name]
            #             process.stop()
            #             del self.background_processes[name]
            if not self.background_processes:
                print('No more active processes.')
                return
            for name, process in self.background_processes.items():
                print('-' * 20)
                print(f'{name}: ')
                print(f'is_alive: {process.is_alive()}')
                for key, value in process.get_status().items():
                    print(f'    {key}: {value}')

    def help_status_all(self):
        print('Shows the status of all background processes.')
        print('Usage: status_all')

    # split line into arguments
    def _splitline(self, line):
        if line:
            arguments = line.split()
            # return arguments in a list
            return arguments
        else:
            return None

    def _stop_all_processes(self):
        # print(self.background_processes)
        self.logger.info('Stopping all background processes.')

        # clear events and processes
        self.clear_events_and_processes()

        if self.background_processes:
            for process in self.background_processes.values():
                process.stop()
                # print('direkt nach stop...')
                process.join(timeout=5)
                self.logger.info(f'  Process {process.name} stopped.')
        else:
            print('no processes to stop ...')

    def do_quit(self, arg):
        """Quits the CLI."""
        self.logger.info("Quitting CLI...")
        self._stop_all_processes()
        self.logger.info("CLI stopped.")
        return True
    
    def help_quit(self):
        print('Quits the CLI.')
        print('Usage: quit')

    def do_exit(self, arg):
        """Exits the shell."""
        self.logger.info("Exiting CLI...")
        self._stop_all_processes()
        self.logger.info("CLI stopped.")
        return True

    def help_exit(self):
        print("syntax: exit \n")
        print("Exits the shell.")
        print("Other possible commands: quit, ^C (EOF)")


# --------------- after main --------------------
# Class to use after "if __name__ == '__main__':"

class mainProcess():

    def __init__(self,
                 shellname,
                 valid_workers,
                 worker_definitons = worker_definitons):

        self.shellname = shellname
        self.valid_workers = valid_workers,
        self.background_processes_for_batch = {}
        self.worker_definitons = worker_definitons
        self.worker_events = {}
        
        for worker in self.valid_workers:
            self.worker_events[worker.value] = threading.Event()

        # parse command line arguments
        self.parser = argparse.ArgumentParser(description=f'CLI for the {self.shellname}.')
        self.parser.add_argument('--mode', choices=['batch', 'cli'], default='batch', help='Run the Programm in batch mode or CLI mode.')
        self.args = self.parser.parse_args()

        # configure logging for this module
        self.logger = logging.getLogger(self.shellname)
        self.logger.setLevel(logging.INFO)

        # create a file handler
        self.handler = logging.FileHandler(f'./logs/{self.shellname}.log')
        self.handler.setLevel(logging.INFO)

        # create a logging format and add it to the handler
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        self.handler.setFormatter(formatter)

        # add the handler to the logger
        self.logger.addHandler(self.handler)

        if self.args.mode == 'batch':
            self.logger.info(f'----- Starting {self.shellname} in BATCH mode. -----')
            # Start all valid workers in batch mode
            self.start_all_processes_for_batch()
            print('you can clean stop the batch mode with CTRL+C')
            # Register signal handler for SIGINT and SIGTERM
            signal.signal(signal.SIGINT, self.handle_signal)
            signal.signal(signal.SIGTERM, self.handle_signal)

        elif self.args.mode == 'cli':
            self.logger.info(f'----- Starting {self.shellname} in CLI mode. -------')
            # Start CLI
            self.cli = cliEngine(shellname=self.shellname, worker_events=self.worker_events)
            self.cli.cmdloop()

        else:
            self.logger.error(f'Invalid mode {self.args.mode}.')
            print('Invalid mode.')
            sys.exit(1)

        
    def handle_signal(self, signal, frame):
        # Signal handling: React to the received signal
        print("Signal received. Stop all background processes and exit...")
        self.logger.info("Signal received. Stop all background processes and exit...")
        self.stop_all_processes_in_batch()


    def start_all_processes_for_batch(self):
        # start all background processes
        self.logger.info('Starting all background processes.')
        for worker in self.valid_workers:
            name = worker.value
            process = self.worker_definitons[name](name=name, event=self.worker_events[name])
            process.start()
            self.background_processes_for_batch[name] = process
            print(f'Started process {name}.')
            self.logger.info(f'Started process {name}.')

    def stop_all_processes_in_batch(self):
        # stop all background processes
        self.logger.info('Stopping all background processes.')
        for name, process in self.background_processes_for_batch.items():
            process.stop()
            process.join(timeout=5)
            print(f'Stopped process {name}.')
            self.logger.info(f'Stopped process {name}.')
