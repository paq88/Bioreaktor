import serial
import time
import threading
import pandas as pd
from secrets import token_hex
import os

lock = threading.Lock()
params = {}
write_thread_instance = None
session = None
parent = "/tmp/"


# Initialize serial communication with the Arduino        
arduino = serial.Serial(port='/dev/ttyACM0', baudrate=115200, timeout=.1) # Linux
arduino.flush()


def write_to_arduino(temp, pH, Stirr_RPM, antifoam, Air_RPM, running_signal, sample_signal=0, stop_signal=0):
    """Send variables to arduino"""
    output_string = f"{temp},{pH},{Stirr_RPM},{antifoam},{Air_RPM},{running_signal},{sample_signal},{stop_signal} \n"
    arduino.write(bytes(output_string, 'utf-8'))
    #print(f'Sent {output_string}')
   
        
out_cols = ['temp_inside', 'temp_outside','ph', 'stirr_rpm', 'air_rpm', 'oxygen']
global old_reads
old_reads = {}

def read_from_arduino(callback):
    """Reads variables from arduino"""
    global old_reads
    if arduino.in_waiting:
        data = arduino.readline().decode('utf-8').strip()
        data_list = data.split(',')
        data_dict = dict(zip(out_cols, data_list))
        if data_dict != old_reads:
            log_events(f'\t{time.ctime()[11:19]}\t|\t{cycle_time}\t|\t{working_time}\t|\tCurrent readings: {data_dict}')
        print(data_dict)
        old_reads = data_dict
        callback(data_dict)
        
def start_session():
    """Session initialize"""
    global session
    global path
    
    uid = token_hex(16)
    session = uid
    print(f"Session UID {session}")
    
    path = os.path.join(parent, session)
    os.mkdir(path)
    log_events(f'\t{time.ctime()}\t|\tSession started\t|\tUID {uid}\n\n\tDate\t|\tCycle time\t|\tWorking time\t|\tEvent')
    

def start_read_thread(callback):
    """Reading thread"""
    def thread_function():
        while not stop_event.is_set():
            read_from_arduino(callback)
            time.sleep(1)
    
    read_thread = threading.Thread(target=thread_function)
    read_thread.daemon = True
    read_thread.start()
    
def write_thread(interval=1):
    """Writing thread"""
    global write_thread_instance
    
    if write_thread_instance and write_thread_instance.is_alive():
        print("Thread already running")
        return

    def thread_function():
        while not stop_event.is_set():
            if not pause_event.is_set():
                write_to_arduino(**params,antifoam=0, running_signal=1, stop_signal=0)
            time.sleep(interval)
    
    stop_event.clear()  
    pause_event.clear()         
    write_thread_instance = threading.Thread(target=thread_function)
    write_thread_instance.daemon = True
    write_thread_instance.start()
    
def update_params(new_params):
    """Update params from GUI"""
    global params
    if params is not new_params:
            log_events(f'\t{time.ctime()[11:19]}\t|\t{cycle_time}\t|\t{working_time}\t|\tCurrent params: {new_params}\n')
    params.update(new_params)

def stop_write_thread():
    """Terminate write thread"""
    global old_reads
    log_events(f'\t{time.ctime()[11:19]}\t|\t{cycle_time}\t|\t{working_time}\t|\tCycle ended\n')
    old_reads = {}
    stop_event.set()
    write_to_arduino(temp=0, pH=0, Stirr_RPM=0, antifoam=0, Air_RPM=0, sample_signal=0, running_signal=0, stop_signal=1)

def pause_write_thread(reason=0):
    """Pause write thread"""
    pause_event.set()
    if reason != 0:
        log_events(f'\t{time.ctime()[11:19]}\t|\t{cycle_time}\t|\t{working_time}\t|\tCycle paused\n')
    
def resume_write_thread(reason=0):
    """Resume write thread"""
    pause_event.clear()
    if reason != 0:
        log_events(f'\t{time.ctime()[11:19]}\t|\t{cycle_time}\t|\t{working_time}\t|\tCycle resumed\n')
    
def send_antifoam_signal():
    """Add antifoam into mixture"""
    def antifoam_thread():
        pause_write_thread(3)
        end_time = time.time() + 10
        log_events(f'\t{time.ctime()[11:19]}\t|\t{cycle_time}\t|\t{working_time}\t|\tAnti-foam added\n')
        while time.time() < end_time:
            write_to_arduino(**params, antifoam=1, sample_signal=3, running_signal=1, stop_signal=0)
            time.sleep(.1)
        resume_write_thread(3)
        
    af_thread = threading.Thread(target=antifoam_thread)
    af_thread.daemon = True
    af_thread.start()
            
def send_sample_signals():
    """Draw sample from mixture"""
    def send_signal(sample_signal):
        sample = sample_signal
        write_to_arduino(**params, antifoam=0, sample_signal=sample, running_signal=1, stop_signal=0)
    
    def sample_signal_thread():
        pause_write_thread(2)
        #print('Pobieranie próbki (signal 2)')
        log_events(f'\t{time.ctime()[11:19]}\t|\t{cycle_time}\t|\t{working_time}\t|\tDrawing sample\n')
        end_time = time.time() + 10
        while time.time() < end_time:
            send_signal(2)
            time.sleep(1)

        #print('Pobieranie próbki (signal 1)')
        end_time = time.time() + 10
        while time.time() < end_time:
            send_signal(1)
            time.sleep(1)

        end_time = time.time() + 10
        while time.time() < end_time:
            send_signal(3)
            time.sleep(1)
        log_events(f'\t{time.ctime()[11:19]}\t|\t{cycle_time}\t|\t{working_time}\t|\tSample drawn\n')
        resume_write_thread(2)

    thread = threading.Thread(target=sample_signal_thread)
    thread.daemon = True
    thread.start()
    
def log_events(event):
    """Log every change in cycle"""
    global log_file
    with open(f'{path}/event_log.txt', 'a') as log_file:
        log_file.write(f'{event}\n')

def read_logs(callback):
    """Read logs from session file and send them to GUI event log"""
    def thread_function():
            while not stop_event.is_set():
                with open(f'{path}/event_log.txt', 'r') as log:
                    x = log.read()
                    callback(x)
                    time.sleep(1)
    
    read_logs_thread = threading.Thread(target=thread_function)
    read_logs_thread.daemon = True
    read_logs_thread.start()

def update_cycle_time(timer):
    """Update current cycle time"""
    global cycle_time
    cycle_time = timer
    
def update_working_time(timer):
    """Update current working time"""
    global working_time
    working_time = timer

    
stop_event = threading.Event()
pause_event = threading.Event()
global temp_inside_list
global temp_outside_list
global ph_list
global oxygen_list
temp_inside_list = []
temp_outside_list = []
ph_list = []
oxygen_list = []
cycle_time = '--:--:--'
working_time = '--:--:--'