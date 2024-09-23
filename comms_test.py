import serial
import time
import threading

# Initialize serial communication with the Arduino
arduino = serial.Serial(port='/dev/ttyACM0', baudrate=115200, timeout=.1)

# Function to continuously read from Arduino in a separate thread
def read_from_arduino():
    while True:
        if arduino.in_waiting:  # Check if data is available to read
            data = arduino.readline().decode('utf-8').strip()
            if data:
                print(f"Arduino: {data}")  # Print incoming data

# Function to send variables to the Arduino
def write_read(temp, pH, Stirr_RPM, antifoam, air_RPM, running_signal, sample_signal=0, stop_signal=0):
    output_string = f"{temp},{pH},{Stirr_RPM},{antifoam},{air_RPM},{running_signal},{sample_signal},{stop_signal} \n"
    arduino.write(bytes(output_string, 'utf-8'))
    time.sleep(0.05)
    # Optionally, receive an immediate response after writing
    data = arduino.readline().decode('utf-8').strip()
    return data

# Start a thread for continuous reading from Arduino
read_thread = threading.Thread(target=read_from_arduino, daemon=True)
read_thread.start()

# Main loop to interactively send data to Arduino
try:
    while True:
        # Collect inputs for sending to Arduino
        temp = float(input("Enter Temperature: "))
        pH = float(input("Enter pH: "))
        Stirr_RPM = int(input("Enter Stirrer RPM: "))
        antifoam = int(input("Enter Antifoam (0/1): "))
        air_RPM = int(input("Enter Air RPM: "))
        running_signal = int(input("Enter Running Signal (0/1): "))
        sample_signal = int(input("Enter Sample Signal (0/1): "))
        stop_signal = int(input("Enter Stop Signal (0/1): "))

        # Send the collected data to Arduino
        response = write_read(temp, pH, Stirr_RPM, antifoam, air_RPM, running_signal, sample_signal, stop_signal)
        print(f"Arduino response to the sent data: {response}")

        time.sleep(1)

except KeyboardInterrupt:
    print("Program terminated.")
finally:
    arduino.close()  # Ensure the serial connection is closed when exiting the program

