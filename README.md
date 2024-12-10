# Serial Monitor

This is a serial monitor that allows you to switch baud rates, input to the serial interface, find and switch between open serial ports, and use `arduino-cli` to compile and upload Arduino code with automatic serial monitoring switch-off during upload.

## How to Use the Serial Monitor

1. Install the required `pyserial` package:

    ```sh
    pip install pyserial
    ```

2. Run the serial monitor:

    ```sh
    python serial_monitor.py
    ```

3. Use the graphical interface to interact with the serial monitor:

    - **Select Port:** Click on "Select Port" to choose the serial port connected to your Arduino device.
    - **Baud Rate:** Select the desired baud rate from the dropdown menu (default is 9600).
    - **Auto Detect Board:** Use the "Auto Detect Board" button to automatically detect the connected Arduino board.
    - **Set Baud Rate:** After selecting the baud rate, click "Set Baud Rate" to apply it.
    - **Compile and Upload:**
        - Enter the path to your Arduino sketch in the "Sketch" entry field.
        - Specify the board type if not auto-detected.
        - Click "Compile and Upload" to compile the sketch using `arduino-cli` and upload it to the Arduino board.
    - **Serial Monitor Output:** View incoming serial data in the output text area.
    - **Input to Serial:** Send data to the serial port using the input field.

## Features

- **Auto Board Detection:** Automatically detects the connected Arduino board and updates the board selection.
- **Standard Baud Rates Dropdown:** Easily select standard baud rates from a dropdown menu.
- **GUI Interface:** User-friendly graphical interface built with Tkinter.
- **Compile and Upload Integration:** Compile and upload sketches directly from the interface using `arduino-cli`.

## Prerequisites

- Python 3.x
- `pyserial` package
- `arduino-cli` installed and configured in your system PATH

## Installation

1. Install Python 3.x if not already installed.
2. Install the required Python packages:

    ```sh
    pip install pyserial
    ```

3. Install `arduino-cli` by following the instructions on the [official website](https://arduino.github.io/arduino-cli/installation/).
