import os
import time
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import threading
import logging

class ThreadingBgWorker(threading.Thread):
    '''
    General background worker class.
    It have to be running as a Callable object to be invoked by the process.start()
    method of the threading.Thread class.
    It is a parent class for all background workers.
    It is a child class of the threading.Thread class.
    Parameters:
        - `name`: name of the worker
        - `event`: event to stop the worker
        - `timerMin`: time in minutes to run the worker
        - `slowDownSec`: time in seconds to slow down the worker
        - `periodicJobSec`: time in seconds to run a periodic job
        - `logging_on`: enable logging
        - `cli_name!`: name of the cli for different log file names
    '''
    def __init__(self,
                 name,
                 event,
                 timerMin = None,
                 slowDownSec = None,
                 periodicJobSec = None,
                 logging_on = True,
                 cli_name = None):
        
        super().__init__()
        self.name = name
        self.no_more_running = event
        self.running = False
        self.running_enabled = True
        self.pid = None
        self.thread_id = None
        self.iterations = 0
        self.slowDownSec = slowDownSec
        self.periodicJobSec = periodicJobSec
        self.cli_name = cli_name
        self.starttime = datetime.now(ZoneInfo('Europe/Paris'))
        # How often to process a periodic job
        self.periodicJobSec = periodicJobSec
        if self.periodicJobSec:
            self.periodicJobLastTime = datetime.now(ZoneInfo('Europe/Paris'))
            self.periodicJobNextTime = self.periodicJobLastTime + timedelta(seconds=self.periodicJobSec)
        self.runtime = None
        self.timeToStop = None
        self.lastStatus = None
        self.timerMin = timerMin
        if self.timerMin:
            self.timeToStop = self.starttime + timedelta(minutes=self.timerMin)
        self.calculateRuntime()

        self.logging_on = logging_on
        if self.logging_on:
            # configure logging for  this worker
            logger = logging.getLogger(f'{self.name}')
            logger.setLevel(logging.INFO)

            # check if handler of the logger already exists
            if not logger.hasHandlers():

                # create file handler for this worker

                if not os.path.exists('./logs'):
                    os.makedirs('./logs')
                if self.cli_name:
                    fh = logging.FileHandler(f'./logs/{self.cli_name}-{self.name}.log')
                else:
                    fh = logging.FileHandler(f'./logs/{self.name}.log')
                fh.setLevel(logging.INFO)

                # create formatter and add it to the handler
                formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
                fh.setFormatter(formatter)

                # add the handler to the logger
                logger.addHandler(fh)

            # add the logger to the worker
            self.loggi = logger

            # log the start of the worker
            self.loggi.info(f'Worker {self.name} started. Worker status at start:')
            self.log_status()

    # stop request will be checked for every iteration to stop the thread cleanly
    def askForStop(self):
        # if self.logging_on:
        #     self.loggi.info(f'askForStop: {self.running_enabled}')
        if self.running_enabled:
            return False
        else:
            return True
        
    # run the thread
    def run(self):
        self.running = True
        self.running_enabled = True
        self.pid = os.getpid()
        self.thread_id = threading.current_thread().native_id
        self.iterations = 0
        print(f'Starting for: {self.timerMin} minutes, will stop at: {self.timeToStop}.')
        if self.logging_on:
            self.loggi.info(f'Starting for: {self.timerMin} minutes, will stop at: {self.timeToStop}.')
        self.addToJobRun()
        self.doJob()

    # place request for stop the thread
    def stop(self):
        if self.logging_on:
            self.loggi.info(f'stop request: {self.running_enabled} at {datetime.now(ZoneInfo("Europe/Paris"))}')
        self.running_enabled = False

    # get the runtime of the thread
    def get_runtime(self):
        return self.runtime

    # get process id of the thread
    def get_pid(self):
        return self.pid
    
    def log_status(self):
        if self.logging_on:
            staust = self.get_status()
            for key, value in staust.items():
                self.loggi.info(f'  {key}: {value}')
        
    # get the status of the thread
    def get_status(self):
        if self.logging_on:
            self.loggi.info(f'ask for status at {datetime.now(ZoneInfo("Europe/Paris"))}')

        message = {}

        if self.timerMin:
            timeToStop_value = str(self.timeToStop.replace(microsecond=0, tzinfo=None).isoformat(' '))
            diff_minutes = round((self.timeToStop - datetime.now(ZoneInfo('Europe/Paris'))).total_seconds() / 60, 1)
            timer_value = f'{diff_minutes} / {self.timerMin} min'
        else:
            timeToStop_value = None
            diff_minutes = None
            timer_value = None

        parentStats = {
            'worker': self.name,
            'process-id': os.getpid(),
            'running': self.running,
            'running-enabled': self.running_enabled,
            # 'thread-id': threading.current_thread().native_id,
            'counter': str(self.iterations),
            'started-at': str(self.starttime.replace(microsecond=0, tzinfo=None).isoformat(' ')),
            'last-state-at': self.lastStatus,
            'runtime': self.runtime,
            'timer': timer_value,
            'will-stop-at': timeToStop_value,
            'slow-down': str(self.slowDownSec),
            'periodic-job-evry-sec': str(self.periodicJobSec)
        }

        message.update(parentStats)
        message.update(self.specificStatus())
        self.lastStatus = str(datetime.now(ZoneInfo('Europe/Paris')).replace(microsecond=0, tzinfo=None).isoformat(' '))
        return message.copy()

    # add user defined intialization to the process
    def addToJobRun(self):
        '''
        Method is to programm in child class.
        Things to do at the beginning of the process like logging settings. 
        '''
        pass

    # get the status of the specific status-items of the child-class
    def specificStatus(self) -> dict:
        '''
        Method is to programm in child class.
        Specific status-items provided by child-class. 
        '''
        return {}
    
    # tasks to do on end of the process
    def taskForStop(self):
        '''
        Method is to programm in child class.
        Things to do at the end of the process. 
        '''
        pass
    
    # tasks to do every time period
    def taskForPeriodicJob(self):
        '''
        Method is to programm in child class.
        Things to do after a defined period of the time (seconds) 
        '''
        pass
    
    # tasks to do every iteration of the main loop (doJob)
    def taskForIteration(self):
        '''
        Method is to programm in child class.
        Things to do during a single iteration of the process 
        '''
        pass

    # tasks to do at the end of the timer
    def taskForTimerEnd(self):
        '''
        Method is to programm in child class.
        Things to do at the end of the time-periode set for the process. 
        '''
        pass

    def periodicJobEnabled(self):
        if self.periodicJobSec:
            if (datetime.now(ZoneInfo('Europe/Paris')) >= self.periodicJobNextTime):
                self.periodicJobLastTime = datetime.now(ZoneInfo('Europe/Paris'))
                self.periodicJobNextTime = self.periodicJobLastTime + timedelta(seconds=self.periodicJobSec)
                return True
            else:
                return False
        else:
            return False

    def checkForStartPeriodicJob(self):
        if self.periodicJobEnabled():
            self.taskForPeriodicJob()

    def calculateRuntime(self):
        self.runtime = str((datetime.now(ZoneInfo('Europe/Paris')) - self.starttime))
        return self.runtime
    
    def set_timer(self, timerMin = None, timerMode = 'set'):
        '''
        Set a timer for the process.
        '''
        print(f'set_timer, minutes: {timerMin}, mode: {timerMode}')
        if self.logging_on:
            self.loggi.info(f'set_timer, minutes: {timerMin}, mode: {timerMode}')

        if timerMode == 'set':
            if timerMin:
                # Set new timer value from now
                self.timerMin = timerMin
                self.timeToStop = datetime.now(ZoneInfo('Europe/Paris')) + timedelta(minutes=self.timerMin)

            else:
                # Reset timer (set job to infinity-job)
                self.timerMin = None

        elif timerMode == 'add':
            if timerMin:
                # Add time to existing timer
                self.timerMin = self.timerMin + timerMin
                self.timeToStop = self.timeToStop + timedelta(minutes=timerMin)

            else:
                # Reset timer (set job to infinity-job)
                self.timerMin = None

        else:
            # Reset timer (set job to infinity-job)
            self.timerMin = None

    def doJob(self):
        while self.running:
            
            self.iterations += 1
            # Update runtime variable
            self.calculateRuntime()

            # What to do if stop command was send
            if self.askForStop():
                # Do something at the end
                self.taskForStop()
                self.log_status()
                self.running = False
                self.no_more_running.set()
                break

            # What to do by every iteration of the while-loop
            self.taskForIteration()
            # What to do by a period of time (set by self.periodicJobSec)
            # If self.periodicJobSec = None, the periodicJob will be not processed
            self.checkForStartPeriodicJob()

            # Slow-Down the Loop (useful for testing)
            if self.slowDownSec:
                time.sleep(self.slowDownSec)

            # Check the timer (if set)
            if self.timerMin:
                if (datetime.now(ZoneInfo('Europe/Paris')) >= self.timeToStop):
                    # What to do by timer end
                    if self.logging_on:
                        self.loggi.info(f'TimerEnd at {datetime.now(ZoneInfo("Europe/Paris"))}')
                    self.taskForTimerEnd()
                    self.log_status()
                    # Send information to host that the job is ready
                    self.running = False
                    self.no_more_running.set()
                    break
