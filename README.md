# Serial Monitor

This is a serial monitor that allows you to switch baud rates, input to the serial interface, find and switch between open serial ports, and use arduino-cli to compile and upload Arduino code with automatic serial monitoring switch-off during upload.

## How to Use the Serial Monitor

1. Install the required `pyserial` package:

    ```sh
    pip install pyserial
    ```

2. Run the serial monitor:

    ```sh
    python serial_monitor.py
    ```

3. Use the graphical interface to interact with the serial monitor.

### Switching Baud Rates

To switch baud rates, enter the desired baud rate in the "Baud Rate" field and click the "Set Baud Rate" button.

### Input to the Serial Interface

To input to the serial interface, enter the data you want to send in the "Data" field and click the "Write to Port" button.

### Finding and Switching Between Open Serial Ports

To find open serial ports, click the "List Ports" button. To switch between open serial ports, enter the desired port in the "Port" field and click the "Open Port" button.

### Using Arduino-CLI to Compile and Upload Arduino Code

To compile and upload Arduino code, enter the sketch path, board, and port in the respective fields and click the "Compile and Upload" button. The serial monitoring will be automatically switched off during the upload process and will resume once the upload is complete.
