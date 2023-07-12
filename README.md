
# `cliengine` Module Documentation

The `cliengine` module provides a Command Line Interface (CLI) for managing background processes. It is based on Python's `cmd` module and allows users to start, stop, and check the status of background processes. Background processes will be started in a separate thread and can be stopped by the user or by a timer.

## Classes and Functions

### Classes

**`TestBgWorker`**

A test class for background workers. It inherits from the `ThreadingBgWorker` class and provides methods to add specific tasks, retrieve specific status, and provide tasks for timer end and stop. 

```python
class TestBgWorker(ThreadingBgWorker):
    def __init__(self, name, event):
        ...

    def addToJobRun(self):
        ...

    def specificStatus(self) -> dict:
        ...

    def taskForTimerEnd(self):
        ...

    def taskForStop(self):
        ...
```

**`cliEngine`**

This class provides the Command Line Interface (CLI) based on the `cmd` module. It offers a variety of methods for managing background processes, including starting and stopping processes, setting timers, displaying the status of all processes, and more.

```python
class cliEngine(cmd.Cmd):
    def __init__(self, shellname, worker_events, valid_workers, worker_definitons, logger):
        ...
    ...
```

**`mainProcess`**

This class represents the main process of the shell. It is the only process that can start background processes. It provides methods to react to received signals and start or stop all background processes.

```python
class mainProcess():
    def __init__(self, shellname, valid_workers = valid_workers, worker_definitons = worker_definitons):
        ...
    ...
```

## Usage

To use this module, you first need to create an instance of the `mainProcess` class and pass the shell name, the valid workers, and the worker definitions as arguments. 

```python
main = mainProcess(shellname='myshell')
```

When running the module in the command line, you can use the commands `start`, `stop`, `timer`, `list`, `status`, `status_all`, `quit`, and `exit` to manage background processes. You can also enter `help` or `?` to get a list of available commands, or enter `help <command>` to get help on a specific command. 

```shell
myshell> start tw1
Starting process: tw1
Started process: tw1
myshell> status tw1
tw1: 
    is_alive: True
    runtime: 5.00238823890686
    timer: 60
    timer_mode: add
    iterations: 0
```

To exit the module, you can either enter `quit` or `exit`. 

```shell
myshell> exit
Exiting CLI...
Stopped process: tw1
CLI stopped.
```

## Logger

This module uses Python's `logging` module to log information about the module's activities. The logs are stored in a file located in the `./logs/` directory and named after the shell. 

## More Information

For more information, including a complete list of methods and their descriptions, please look into the source code of the module.
