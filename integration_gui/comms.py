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
parent = "C:/Users/marek/Documents"


# Initialize serial communication with the Arduino

# class MockArduino:
#     def write(self, data):
#         print(f"Mock write to Arduino: {data}")
        
#arduino = serial.Serial(port='/dev/ttyACM0', baudrate=115200, timeout=.1) # Linux
arduino = serial.Serial(port='COM11', baudrate=115200, timeout=.1) # Linux


# Function to send variables to the Arduino
def write_to_arduino(temp, pH, Stirr_RPM, antifoam, Air_RPM, running_signal, sample_signal=0, stop_signal=0):
    global arduino_in_df
    output_string = f"{temp},{pH},{Stirr_RPM},{antifoam},{Air_RPM},{running_signal},{sample_signal},{stop_signal} \n"
    arduino.write(bytes(output_string, 'utf-8'))
    print(f'Sent {output_string}')

    
# def log_to_file(parameters):
#     with open(f'/tmp/{session}/log_in', 'w') as f:
#         new_row = pd.DataFrame(parameters, ignore_index=True)
#         arduino_in_df = pd.concat([arduino_in_df, new_row], ignore_index=True)
#         print(arduino_in_df)
    
        
mock = 'mockArduino'
out_cols = ['temp_inside', 'temp_outside','ph', 'stirr_rpm', 'air_rpm']
def read_from_arduino(callback):
    if arduino.in_waiting:
        data = arduino.readline().decode('utf-8').strip()
        data_list = data.split(',')
        data_dict = dict(zip(out_cols, data_list))
        print(data_dict)
        callback(data_dict)
        
# def read_from_arduino(callback=None):
#     global arduino_out_df
#     while True:
#         if arduino.in_waiting:  # Check if data is available to read
#             data = arduino.readline().decode('utf-8').strip()
#             if data:
#                 # Print incoming data
#                 # print(f"Arduino: {data}")
#                 # Parse the data and append it to the DataFrame
#                 data_list = data.split(',')
#                 if len(data_list) == len(columns_out):
#                     data_dict = dict(zip(columns_out, data_list))
#                     new_row = pd.DataFrame([data_dict])
#                     arduino_out_df = pd.concat([arduino_out_df, new_row], ignore_index=True)
#         time.sleep(0.1) # Small delay to prevent high CPU usage
        
def start_session():
    global session
    global path
    
    uid = token_hex(16)
    session = uid
    print(f"Session UID {session}")
    
    path = os.path.join(parent, session)
    os.mkdir(path)

def start_read_thread(callback):
    def thread_function():
        while not stop_event.is_set():
            read_from_arduino(callback)
            time.sleep(0.1)
    
    read_thread = threading.Thread(target=thread_function)
    read_thread.daemon = True
    read_thread.start()
    
def write_thread(interval=1):
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
    global params
    params.update(new_params)

def stop_write_thread():
    stop_event.set()
    write_to_arduino(temp=0, pH=0, Stirr_RPM=0, antifoam=0, Air_RPM=0, sample_signal=0, running_signal=0, stop_signal=1)

def pause_write_thread():
    pause_event.set()
    
def resume_write_thread():
    pause_event.clear()
    
def send_antifoam_signal():
    def antifoam_thread():
        pause_write_thread()
        end_time = time.time() + 10
        while time.time() < end_time:
            write_to_arduino(**params, antifoam=1, sample_signal=3, running_signal=1, stop_signal=0)
            time.sleep(.1)
        resume_write_thread()
        
    af_thread = threading.Thread(target=antifoam_thread)
    af_thread.daemon = True
    af_thread.start()
            
def send_sample_signals():    
    def send_signal(sample_signal):
        sample = sample_signal
        write_to_arduino(**params, antifoam=0, sample_signal=sample, running_signal=1, stop_signal=0)
    
    def sample_signal_thread():
        pause_write_thread()
        print('Pobieranie próbki (signal 2)')
        end_time = time.time() + 10
        while time.time() < end_time:
            send_signal(2)
            time.sleep(1)

        print('Pobieranie próbki (signal 1)')
        end_time = time.time() + 10
        while time.time() < end_time:
            send_signal(1)
            time.sleep(1)

        end_time = time.time() + 10
        while time.time() < end_time:
            send_signal(3)
            time.sleep(1)
        resume_write_thread()

    thread = threading.Thread(target=sample_signal_thread)
    thread.daemon = True
    thread.start()

    
stop_event = threading.Event()
pause_event = threading.Event()

columns_out = ["total_cycle_time","temp_inside","temp_outside","pH","O2","antifoam","stirr_rpm","air_RPM","sample_signal","running_signal","Comment"]
arduino_out_df = pd.DataFrame(columns=columns_out)


columns_in = ["temp","pH","Stirr_RPM","antifoam","air_RPM","sample_signal"]
arduino_in_df = pd.DataFrame(columns=columns_in)