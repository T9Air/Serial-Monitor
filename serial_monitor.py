import serial
import serial.tools.list_ports
import subprocess
import threading
import time

class SerialMonitor:
    def __init__(self):
        self.serial_port = None
        self.baud_rate = 9600
        self.is_monitoring = False

    def list_ports(self):
        ports = serial.tools.list_ports.comports()
        return [port.device for port in ports]

    def open_port(self, port):
        if self.serial_port:
            self.serial_port.close()
        self.serial_port = serial.Serial(port, self.baud_rate)
        self.is_monitoring = True
        threading.Thread(target=self.read_from_port).start()

    def close_port(self):
        if self.serial_port:
            self.is_monitoring = False
            self.serial_port.close()
            self.serial_port = None

    def set_baud_rate(self, baud_rate):
        self.baud_rate = baud_rate
        if self.serial_port:
            self.serial_port.baudrate = baud_rate

    def read_from_port(self):
        while self.is_monitoring:
            if self.serial_port.in_waiting > 0:
                data = self.serial_port.read(self.serial_port.in_waiting)
                print(data.decode('utf-8'), end='')

    def write_to_port(self, data):
        if self.serial_port:
            self.serial_port.write(data.encode('utf-8'))

    def compile_and_upload(self, sketch_path, board, port):
        self.close_port()
        compile_cmd = f"arduino-cli compile --fqbn {board} {sketch_path}"
        upload_cmd = f"arduino-cli upload -p {port} --fqbn {board} {sketch_path}"
        subprocess.run(compile_cmd, shell=True)
        subprocess.run(upload_cmd, shell=True)
        self.open_port(port)

if __name__ == "__main__":
    monitor = SerialMonitor()
    while True:
        print("Available commands:")
        print("1. List ports")
        print("2. Open port")
        print("3. Close port")
        print("4. Set baud rate")
        print("5. Write to port")
        print("6. Compile and upload")
        print("7. Exit")
        command = input("Enter command: ")
        if command == "1":
            ports = monitor.list_ports()
            print("Available ports:", ports)
        elif command == "2":
            port = input("Enter port: ")
            monitor.open_port(port)
        elif command == "3":
            monitor.close_port()
        elif command == "4":
            baud_rate = int(input("Enter baud rate: "))
            monitor.set_baud_rate(baud_rate)
        elif command == "5":
            data = input("Enter data to write: ")
            monitor.write_to_port(data)
        elif command == "6":
            sketch_path = input("Enter sketch path: ")
            board = input("Enter board: ")
            port = input("Enter port: ")
            monitor.compile_and_upload(sketch_path, board, port)
        elif command == "7":
            monitor.close_port()
            break
        else:
            print("Invalid command")
