import serial
import time
import threading
import pandas as pd

# lock to ensure safety access to variables from multiple threads
lock = threading.Lock()


# Initialize serial communication with the Arduino
#arduino = serial.Serial(port='/dev/ttyACM0', baudrate=115200, timeout=.1) # Linux
arduino = serial.Serial(port='COM10', baudrate=115200, timeout=.1) # Windows

def read_from_arduino():
    global arduino_out_df
    while True:
        if arduino.in_waiting:  # Check if data is available to read
            data = arduino.readline().decode('utf-8').strip()
            if data:
                # Print incoming data
                # print(f"Arduino: {data}")
                # Parse the data and append it to the DataFrame
                data_list = data.split(',')
                if len(data_list) == len(columns_out):
                    data_dict = dict(zip(columns_out, data_list))
                    new_row = pd.DataFrame([data_dict])
                    arduino_out_df = pd.concat([arduino_out_df, new_row], ignore_index=True)
        time.sleep(0.1) # Small delay to prevent high CPU usage


# Format 
#pH input/output FLoat  xx.xx
# temp input/output Float xx.xx

# Function to send variables to the Arduino
def write_to_arduino(temp, pH, Stirr_RPM, antifoam, air_RPM, running_signal, sample_signal=0, stop_signal=0):
    global arduino_in_df
    output_string = f"{temp},{pH},{Stirr_RPM},{antifoam},{air_RPM},{running_signal},{sample_signal},{stop_signal} \n"
    arduino.write(bytes(output_string, 'utf-8'))

    # save log to dataframe
    data_dict = dict(zip(columns_out, [temp, pH, Stirr_RPM, antifoam, air_RPM, running_signal, sample_signal, stop_signal]))
    new_row = pd.DataFrame([data_dict])
    arduino_in_df = pd.concat([arduino_in_df, new_row], ignore_index=True)
    

# Function to collect user input
def collect_user_input():
    global initial_temp, initial_pH, initial_Stirr_RPM, initial_antifoam, initial_air_RPM, running_signal, sample_signal_user, stop_signal_user
    while True:
        try:
            with lock:
                initial_temp = float(input("Enter Temperature: "))
                initial_pH = float(input("Enter pH: "))
                initial_Stirr_RPM = int(input("Enter Stirrer RPM: "))
                initial_antifoam = int(input("Enter Antifoam (0/1): "))
                initial_air_RPM = int(input("Enter Air RPM: "))
                running_signal = int(input("Enter Running Signal (0/1): "))
                sample_signal_user = int(input("Enter Sample Signal (0/1): "))
                stop_signal_user = int(input("Enter Stop Signal (0/1): "))
                write_to_arduino(initial_temp, initial_pH, initial_Stirr_RPM, initial_antifoam, initial_air_RPM, running_signal, sample_signal_user, stop_signal_user)

        except ValueError:
            print("Invalid input. Please enter the correct values.")




# Create DataFrames to store the data sent to and received from the Arduino
columns_out = ["total_cycle_time","temp_inside","temp_outside","pH","O2","antifoam","stirr_rpm","air_RPM","sample_signal","running_signal","Comment"]
arduino_out_df = pd.DataFrame(columns=columns_out)

columns_in = ["temp","pH","Stirr_RPM","antifoam","air_RPM","running_signal","sample_signal","stop_signal"]
arduino_in_df = pd.DataFrame(columns=columns_in)




# set initial parameters from the user goes HERE they can be modified during the program
initial_temp = 15.0 #float(input("Enter Temperature: "))
initial_pH = 7.0 # float(input("Enter pH: "))
initial_Stirr_RPM = 100 #int(input("Enter Stirrer RPM: "))
initial_antifoam = 1 #int(input("Enter Antifoam (0/1): "))
initial_air_RPM = 150 #int(input("Enter Air RPM: "))

# in seconds
total_cycle_time = 15 

# define the cycle time from user 
# interface input


# interface start button

# start of the program 
print("Program started.")
cycle_start_time = time.time()
running_signal = 1
sample_signal_user = 0
stop_signal_user = 0


# Start a thread for continuous reading from Arduino
read_thread = threading.Thread(target=read_from_arduino, daemon=True)
read_thread.start()

# start the thread to collect user input1
user_input_thread = threading.Thread(target=collect_user_input, daemon=True)
user_input_thread.start()





while True:
        #print(time.time()/100000)
        # main loop constantly sending data to arduino
        current_time = time.time()
        
        




        # update parameters and signals with the ones from user_input_thread 
        with lock:
            temp = initial_temp
            pH = initial_pH
            Stirr_RPM = initial_Stirr_RPM
            antifoam = initial_antifoam
            air_RPM = initial_air_RPM
            current_running_signal = running_signal
            current_sample_signal_user = sample_signal_user
            current_stop_signal_user = stop_signal_user
        

        ######################## Sample pickup part ########################
        if current_sample_signal_user != 0:
            sample_start_time = current_time
            
        if 'sample_start_time' in locals():
            elapsed_time = current_time - sample_start_time
            if elapsed_time <= 10:
                # Draw sample for 10 seconds
                sample_signal = 1
            elif 10 < elapsed_time < 20:
                # Return remains from drawing tube
                sample_signal = 2
            else:
                # Stop sample signal after 20 seconds (turns off pump)
                sample_signal = 0

        else:
            sample_signal = 0
        

        # stop cycle part 
        if current_stop_signal_user == 1 or current_time - cycle_start_time > total_cycle_time:
            stop_signal = 1
            print("Cycle finished")
            break
        else:
            stop_signal = 0

        # Send the collected data to Arduino
        response = write_to_arduino(temp, pH, Stirr_RPM, antifoam, air_RPM, running_signal, sample_signal, stop_signal)


        time.sleep(1)



        if stop_signal == 1:
            break

        # set main loop frequency
        time.sleep(3)   
     
   

arduino.close()  # Ensure the serial connection is closed when exiting the program

print(arduino_out_df)
print(arduino_in_df)