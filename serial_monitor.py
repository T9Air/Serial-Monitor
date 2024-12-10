import serial
import serial.tools.list_ports
import subprocess
import threading
import time
import tkinter as tk
from tkinter import scrolledtext
from tkinter import ttk
from tkinter import filedialog  # Add this import at the top

class SerialMonitor:
    # Define standard baud rates as a class variable
    STANDARD_BAUD_RATES = [300, 1200, 2400, 4800, 9600, 14400, 19200, 38400, 57600, 115200]

    def __init__(self):
        self.serial_port = None
        self.baud_rate = 9600
        self.is_monitoring = False

    def list_ports(self):
        ports = serial.tools.list_ports.comports()
        return [port.device for port in ports]

    def open_port(self, port):
        try:
            if self.serial_port:
                self.serial_port.close()
            self.serial_port = serial.Serial(port, self.baud_rate, timeout=0.1)
            self.is_monitoring = True
            self.status_label.config(text=f"Status: Connected to {port}", fg="green")
            read_thread = threading.Thread(target=self.read_from_port, daemon=True)
            read_thread.start()
        except Exception as e:
            self.output_text.insert(tk.END, f"Error opening port: {str(e)}\n")
            self.status_label.config(text="Status: Connection Failed", fg="red")

    def close_port(self):
        if self.serial_port:
            self.is_monitoring = False
            self.serial_port.close()
            self.serial_port = None
            self.status_label.config(text="Status: Disconnected", fg="red")

    def set_baud_rate(self, baud_rate):
        self.baud_rate = baud_rate
        if self.serial_port:
            self.serial_port.baudrate = baud_rate

    def read_from_port(self):
        while self.is_monitoring:
            if self.serial_port.in_waiting > 0:
                data = self.serial_port.read(self.serial_port.in_waiting)
                self.display_data(data.decode('utf-8'))

    def write_to_port(self, data):
        if self.serial_port:
            line_ending = self.line_ending_var.get()
            self.serial_port.write((data + line_ending).encode('utf-8'))

    def compile_and_upload(self, sketch_path, board, port):
        self.close_port()
        compile_cmd = f"arduino-cli compile --fqbn {board} {sketch_path}"
        upload_cmd = f"arduino-cli upload -p {port} --fqbn {board} {sketch_path}"
        subprocess.run(compile_cmd, shell=True)
        subprocess.run(upload_cmd, shell=True)
        self.open_port(port)

    def auto_detect_board(self):
        ports = serial.tools.list_ports.comports()
        arduino_ports = [
            port for port in ports 
            if 'Arduino' in port.description or 'Arduino' in port.manufacturer
        ]
        
        if arduino_ports:
            port = arduino_ports[0]  # Take the first Arduino port found
            description = port.description.lower()
            
            # Determine board type based on description
            if 'uno' in description:
                board_type = 'Uno'
            elif 'mega' in description:
                board_type = 'Mega'
            elif 'nano' in description:
                board_type = 'Nano'
            else:
                board_type = 'Unknown'
            
            # Update GUI elements
            self.board_entry.delete(0, tk.END)
            self.board_entry.insert(0, board_type)
            self.selected_port = port.device
            self.port_display_label.config(text=f"Selected Port: {self.selected_port}")
            self.output_text.insert(tk.END, f"Detected Arduino board: {board_type} on port {self.selected_port}\n")
        else:
            self.output_text.insert(tk.END, "No Arduino board detected.\n")

    def create_gui(self):
        self.root = tk.Tk()
        self.root.title("Serial Monitor")
        
        # Configure column weights to make them expandable
        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_columnconfigure(1, weight=1)

        self.selected_port = None  # Variable to store the selected port

        self.select_port_button = tk.Button(self.root, text="Select Port", command=self.select_port_gui)
        self.select_port_button.grid(row=0, column=0)

        self.port_display_label = tk.Label(self.root, text="Selected Port: None")
        self.port_display_label.grid(row=0, column=1)

        self.baud_label = tk.Label(self.root, text="Baud Rate:")
        self.baud_label.grid(row=1, column=0)

        self.baud_combo = ttk.Combobox(self.root, values=self.STANDARD_BAUD_RATES, state='readonly')
        self.baud_combo.grid(row=1, column=1)
        self.baud_combo.set(9600)  # Set default value

        # Add status indicator
        self.status_label = tk.Label(self.root, text="Status: Disconnected", fg="red")
        self.status_label.grid(row=2, column=0, columnspan=2)
        
        # Add line ending options
        self.line_ending_var = tk.StringVar(value="\n")
        self.line_ending_frame = tk.Frame(self.root)
        self.line_ending_frame.grid(row=3, column=0, columnspan=2)
        
        tk.Radiobutton(self.line_ending_frame, text="No Line Ending", 
                      variable=self.line_ending_var, value="").pack(side=tk.LEFT)
        tk.Radiobutton(self.line_ending_frame, text="New Line", 
                      variable=self.line_ending_var, value="\n").pack(side=tk.LEFT)
        tk.Radiobutton(self.line_ending_frame, text="Carriage Return", 
                      variable=self.line_ending_var, value="\r").pack(side=tk.LEFT)
        tk.Radiobutton(self.line_ending_frame, text="Both NL & CR", 
                      variable=self.line_ending_var, value="\r\n").pack(side=tk.LEFT)

        # Create a frame for sketch selection
        self.sketch_frame = tk.Frame(self.root)
        self.sketch_frame.grid(row=4, column=0, columnspan=2, sticky='ew')
        
        self.sketch_label = tk.Label(self.sketch_frame, text="Sketch:")
        self.sketch_label.pack(side=tk.LEFT)
        
        self.sketch_entry = tk.Entry(self.sketch_frame)
        self.sketch_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        self.browse_button = tk.Button(self.sketch_frame, text="Browse", command=self.browse_sketch)
        self.browse_button.pack(side=tk.RIGHT)

        self.board_label = tk.Label(self.root, text="Board:")
        self.board_label.grid(row=5, column=0)
        self.board_entry = tk.Entry(self.root)
        self.board_entry.grid(row=5, column=1)

        self.set_baud_rate_button = tk.Button(self.root, text="Set Baud Rate", command=self.set_baud_rate_gui)
        self.set_baud_rate_button.grid(row=6, column=0)

        self.compile_upload_button = tk.Button(self.root, text="Compile and Upload", command=self.compile_and_upload_gui)
        self.compile_upload_button.grid(row=6, column=1)

        self.data_frame = tk.Frame(self.root)
        self.data_frame.grid(row=7, column=0, columnspan=2, sticky='ew')
        self.root.grid_rowconfigure(7, weight=0)  # Don't expand input row

        self.data_entry = tk.Entry(self.data_frame)
        self.data_entry.pack(fill=tk.X, expand=True, padx=5, pady=2)
        self.data_entry.bind("<Return>", self.write_to_port_gui)
        self.data_entry.focus_set()  # Auto focus on the input field

        # Move output frame to row 8
        self.output_frame = tk.Frame(self.root)
        self.output_frame.grid(row=8, column=0, columnspan=2, sticky='nsew')
        self.root.grid_rowconfigure(8, weight=1)  # Make output frame expandable
        
        self.scrollbar = tk.Scrollbar(self.output_frame)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.output_text = tk.Text(self.output_frame, height=10, width=50, 
                                  yscrollcommand=self.scrollbar.set)
        self.output_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.scrollbar.config(command=self.output_text.yview)

        # Move auto detect board button to row 9
        self.auto_detect_board_button = tk.Button(self.root, text="Auto Detect Board", command=self.auto_detect_board)
        self.auto_detect_board_button.grid(row=9, column=0, columnspan=2)

        # Now safe to call auto_detect_board
        self.auto_detect_board()

        self.root.mainloop()

    def browse_sketch(self):
        filename = filedialog.askopenfilename(
            title="Select Arduino Sketch",
            filetypes=(("Arduino Sketches", "*.ino"), ("All Files", "*.*"))
        )
        if filename:
            self.sketch_entry.delete(0, tk.END)
            self.sketch_entry.insert(0, filename)

    def update_ports(self):
        ports = self.list_ports()
        self.output_text.insert(tk.END, f"Available ports: {ports}\n")

    def list_ports_gui(self):
        ports = self.list_ports()
        self.output_text.insert(tk.END, f"Available ports: {ports}\n")

    def select_port_gui(self):
        ports = self.list_ports()
        if not ports:
            self.output_text.insert(tk.END, "No ports available\n")
            return

        # Create a new window for port selection
        port_window = tk.Toplevel(self.root)
        port_window.title("Select Port")

        tk.Label(port_window, text="Available Ports:").pack()

        port_listbox = tk.Listbox(port_window)
        port_listbox.pack()

        for port in ports:
            port_listbox.insert(tk.END, port)

        def on_select():
            selected_indices = port_listbox.curselection()
            if selected_indices:
                self.selected_port = port_listbox.get(selected_indices[0])
                self.port_display_label.config(text=f"Selected Port: {self.selected_port}")
                port_window.destroy()
                # Auto-open the port when selected
                self.open_port(self.selected_port)
            else:
                self.output_text.insert(tk.END, "No port selected\n")

        select_button = tk.Button(port_window, text="Select", command=on_select)
        select_button.pack()

    def open_port_gui(self):
        if self.selected_port:
            self.open_port(self.selected_port)
            self.output_text.insert(tk.END, f"Opened port: {self.selected_port}\n")
        else:
            self.output_text.insert(tk.END, "No port selected\n")

    def close_port_gui(self):
        if self.serial_port:
            self.close_port()
            self.output_text.insert(tk.END, f"Closed port: {self.selected_port}\n")
        else:
            self.output_text.insert(tk.END, "No port is open\n")

    def set_baud_rate_gui(self):
        try:
            baud_rate = int(self.baud_combo.get())
            self.set_baud_rate(baud_rate)
        except ValueError:
            self.output_text.insert(tk.END, "Invalid baud rate\n")

    def write_to_port_gui(self, event=None):
        if not self.serial_port:
            self.output_text.insert(tk.END, "Port not open\n")
            return
        data = self.data_entry.get()
        if data:  # Only send if there's data
            self.write_to_port(data)
            self.data_entry.delete(0, tk.END)  # Clear the entry after sending
            self.output_text.see(tk.END)  # Scroll to bottom after sending

    def compile_and_upload_gui(self):
        sketch_path = self.sketch_entry.get()
        if not sketch_path:
            self.output_text.insert(tk.END, "Please select a sketch file\n")
            return
        if not sketch_path.endswith('.ino'):
            self.output_text.insert(tk.END, "Selected file is not an Arduino sketch (.ino)\n")
            return
            
        board = self.board_entry.get()
        if not board:
            self.output_text.insert(tk.END, "Please enter a board type\n")
            return
            
        if not self.selected_port:
            self.output_text.insert(tk.END, "Please select a port\n")
            return
            
        self.compile_and_upload(sketch_path, board, self.selected_port)

    def display_data(self, data):
        self.output_text.insert(tk.END, data)
        self.output_text.see(tk.END)  # Auto-scroll to bottom

if __name__ == "__main__":
    monitor = SerialMonitor()
    monitor.create_gui()
