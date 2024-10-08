import threading
import serial
import time
import tkinter as tk
from tkinter.scrolledtext import ScrolledText
import pandas as pd

# Global variables for user input
initial_temp = 0.0
initial_pH = 0.0
initial_Stirr_RPM = 0
initial_antifoam = 0
initial_air_RPM = 0
running_signal = 0
sample_signal_user = 0
stop_signal_user = 0

# Lock for thread synchronization
lock = threading.Lock()

# Placeholder for Arduino object
class MockArduino:
    def write(self, data):
        print(f"Mock write to Arduino: {data}")
# real arduino 
arduino = serial.Serial(port='COM11', baudrate=115200, timeout=.1) # Windows

# DataFrame columns
columns_out = ["total_cycle_time", "temp_inside", "temp_outside", "pH", "O2", "antifoam", "stirr_rpm", "air_RPM", "sample_signal", "running_signal", "Comment"]
arduino_out_df = pd.DataFrame(columns=columns_out)

columns_in = ["temp","pH","Stirr_RPM","antifoam","air_RPM","running_signal","sample_signal","stop_signal"]
arduino_in_df = pd.DataFrame(columns=columns_in)


def read_from_arduino(text_widget):
    global arduino_out_df
    while True:
        if arduino.in_waiting:  # Check if data is available to read
            data = arduino.readline().decode('utf-8').strip()
            if data:
                # Print incoming data to the text widget
                text_widget.insert(tk.END, f"Arduino: {data}\n")
                text_widget.see(tk.END)
                # Parse the data and append it to the DataFrame
                data_list = data.split(',')
                if len(data_list) == len(columns_out):
                    data_dict = dict(zip(columns_out, data_list))
                    new_row = pd.DataFrame([data_dict])
                    arduino_out_df = pd.concat([arduino_out_df, new_row], ignore_index=True)
        time.sleep(0.1)  # Small delay to prevent high CPU usage

# Function to collect user input from the GUI
def collect_user_input(entry_fields):
    global initial_temp, initial_pH, initial_Stirr_RPM, initial_antifoam, initial_air_RPM, running_signal, sample_signal_user, stop_signal_user
    while True:
        try:
            with lock:
                initial_temp = float(entry_fields['Temperature'].get())
                initial_pH = float(entry_fields['pH'].get())
                initial_Stirr_RPM = int(entry_fields['Stirrer RPM'].get())
                initial_antifoam = int(entry_fields['Antifoam'].get())
                initial_air_RPM = int(entry_fields['Air RPM'].get())
                running_signal = int(entry_fields['Running Signal'].get())
                sample_signal_user = int(entry_fields['Sample Signal'].get())
                stop_signal_user = int(entry_fields['Stop Signal'].get())
                write_to_arduino(initial_temp, initial_pH, initial_Stirr_RPM, initial_antifoam, initial_air_RPM, running_signal, sample_signal_user, stop_signal_user)
                time.sleep(1)  # Add a small delay to prevent high CPU usage

        except ValueError:
            print("Invalid input. Please enter the correct values.")

# Placeholder function to simulate sending data to Arduino
def write_to_arduino(temp, pH, Stirr_RPM, antifoam, air_RPM, running_signal, sample_signal=0, stop_signal=0):
    global arduino_in_df
    output_string = f"{temp},{pH},{Stirr_RPM},{antifoam},{air_RPM},{running_signal},{sample_signal},{stop_signal} \n"
    arduino.write(bytes(output_string, 'utf-8'))

    # save log to dataframe
    data_dict = dict(zip(columns_out, [temp, pH, Stirr_RPM, antifoam, air_RPM, running_signal, sample_signal, stop_signal]))
    new_row = pd.DataFrame([data_dict])
    arduino_in_df = pd.concat([arduino_in_df, new_row], ignore_index=True)
# Function to handle the main control loop
def control_loop():
    global stop_signal_user, sample_signal_user
    cycle_start_time = time.time()
    total_cycle_time = 100  # Example total cycle time in seconds

    while True:
        current_time = time.time()
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

        # Stop cycle part 
        if current_stop_signal_user == 1 or current_time - cycle_start_time > total_cycle_time:
            stop_signal = 1
            print("Cycle finished")
            break
        else:
            stop_signal = 0

        # Send the collected data to Arduino
        response = write_to_arduino(initial_temp, initial_pH, initial_Stirr_RPM, initial_antifoam, initial_air_RPM, running_signal, sample_signal, stop_signal)

        time.sleep(1)

# Function to create the user input window
def create_input_window():
    input_window = tk.Toplevel()
    input_window.title("User Input")

    labels = ["Temperature", "pH", "Stirrer RPM", "Antifoam", "Air RPM", "Running Signal", "Sample Signal", "Stop Signal"]
    entry_fields = {}

    for label in labels:
        row = tk.Frame(input_window)
        lab = tk.Label(row, width=15, text=label, anchor='w')
        ent = tk.Entry(row)
        row.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)
        lab.pack(side=tk.LEFT)
        ent.pack(side=tk.RIGHT, expand=tk.YES, fill=tk.X)
        entry_fields[label] = ent

    return entry_fields

# Main function to start the threads and GUI
def main():
    # Create the main window
    root = tk.Tk()
    root.title("Arduino Control")

    # Create a ScrolledText widget to display responses
    text_widget = ScrolledText(root, wrap=tk.WORD, width=50, height=20)
    text_widget.pack(padx=10, pady=10)

    # Create the user input window
    entry_fields = create_input_window()

    # Start the user input collection in a separate thread
    input_thread = threading.Thread(target=collect_user_input, args=(entry_fields,), daemon=True)
    input_thread.start()

    # Start the control loop in another thread
    control_thread = threading.Thread(target=control_loop, daemon=True)
    control_thread.start()

    # Start the thread to read responses from Arduino and update the GUI
    read_thread = threading.Thread(target=read_from_arduino, args=(text_widget,), daemon=True)
    read_thread.start()

    # Start the Tkinter main loop
    root.mainloop()

# Start the main function
if __name__ == "__main__":
    main()
