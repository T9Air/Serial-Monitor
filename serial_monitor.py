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
            self.port_display_label.config(text="Selected Port: None")  # Clear port display
            self.selected_port = None  # Reset selected port

    def disconnect_connection(self):
        self.close_port()
        self.output_text.insert(tk.END, "Disconnected from port\n")

    def set_baud_rate(self, baud_rate):
        self.baud_rate = baud_rate
        if self.serial_port:
            self.serial_port.baudrate = baud_rate

    def read_from_port(self):
        while self.is_monitoring:
            try:
                if self.serial_port and self.serial_port.is_open:
                    if self.serial_port.in_waiting > 0:
                        data = self.serial_port.read(self.serial_port.in_waiting)
                        self.root.after(0, self.display_data, data.decode('utf-8'))
                time.sleep(0.1)  # Add small delay to prevent CPU hogging
            except serial.SerialException:
                # Port disconnected or error occurred
                self.root.after(0, self.handle_disconnect)
                break
            except Exception as e:
                self.root.after(0, self.display_data, f"Error reading from port: {str(e)}\n")
                break

    def handle_disconnect(self):
        """Handle unexpected port disconnection"""
        self.close_port()
        self.output_text.insert(tk.END, "Port disconnected unexpectedly\n")

    def write_to_port(self, data):
        if self.serial_port:
            line_ending = self.line_ending_var.get()
            self.serial_port.write((data + line_ending).encode('utf-8'))

    def compile_and_upload(self, sketch_path, board, port):
        # Run compile and upload in a separate thread to keep GUI responsive
        threading.Thread(
            target=self.run_compile_and_upload, args=(sketch_path, board, port), daemon=True
        ).start()

    def run_compile_and_upload(self, sketch_path, board, port):
        self.close_port()
        compile_cmd = ["arduino-cli", "compile", "--fqbn", board, sketch_path]
        upload_cmd = ["arduino-cli", "upload", "-p", port, "--fqbn", board, sketch_path]

        for cmd_name, cmd in [("Compilation", compile_cmd), ("Upload", upload_cmd)]:
            process = subprocess.Popen(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True
            )
            while True:
                output = process.stdout.readline()
                if output == '' and process.poll() is not None:
                    break
                if output:
                    # Use after() to safely update GUI from another thread
                    self.root.after(0, self.append_to_upload_output, output)
            if process.returncode != 0:
                self.root.after(0, self.append_to_upload_output, f"{cmd_name} failed.\n")
                return

        self.root.after(0, self.append_to_upload_output, "Compile and upload successful.\n")
        # Re-open the port after upload
        self.root.after(0, self.open_port, port)

    def append_to_upload_output(self, text):
        self.upload_output_text.insert(tk.END, text)
        self.upload_output_text.see(tk.END)

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
            
            # Map board_type to FQBN
            board_fqbn_map = {
                'uno': 'arduino:avr:uno',
                'mega': 'arduino:avr:mega',
                'nano': 'arduino:avr:nano',
                'leonardo': 'arduino:avr:leonardo',
                # Add more mappings as needed
            }
            
            fqbn = board_fqbn_map.get(board_type.lower(), None)
            if fqbn:
                # Update the board selection
                self.board_combo.set(fqbn)
                self.output_text.insert(tk.END, f"Detected Arduino board: {board_type} on port {self.selected_port}\n")
            else:
                self.output_text.insert(tk.END, f"Board type '{board_type}' not recognized.\n")
        else:
            self.output_text.insert(tk.END, "No Arduino board detected.\n")

    def auto_connect_first_port(self):
        ports = self.list_ports()
        if ports:
            self.selected_port = ports[0]
            self.port_display_label.config(text=f"Selected Port: {self.selected_port}")
            self.open_port(self.selected_port)
            return True
        return False

    def create_gui(self):
        self.root = tk.Tk()
        self.root.title("Serial Monitor")

        # Create a notebook (tabs)
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill='both', expand=True)

        # Create frames for each tab
        monitor_frame = ttk.Frame(notebook)
        upload_frame = ttk.Frame(notebook)

        notebook.add(monitor_frame, text='Serial Monitor')
        notebook.add(upload_frame, text='Upload Sketch')

        # --- Serial Monitor Tab ---
        # Configure column weights
        monitor_frame.columnconfigure(0, weight=1)
        monitor_frame.columnconfigure(1, weight=1)

        self.selected_port = None  # Variable to store the selected port

        self.select_port_button = tk.Button(monitor_frame, text="Select Port", command=self.select_port_gui)
        self.select_port_button.grid(row=0, column=0)

        self.port_display_label = tk.Label(monitor_frame, text="Selected Port: None")
        self.port_display_label.grid(row=0, column=1)

        self.baud_label = tk.Label(monitor_frame, text="Baud Rate:")
        self.baud_label.grid(row=1, column=0)

        self.baud_combo = ttk.Combobox(monitor_frame, values=self.STANDARD_BAUD_RATES, state='readonly')
        self.baud_combo.grid(row=1, column=1)
        self.baud_combo.set(9600)  # Set default value

        # Move disconnect button to new row
        self.disconnect_button = tk.Button(monitor_frame, text="Disconnect", command=self.disconnect_connection)
        self.disconnect_button.grid(row=2, column=0, columnspan=2)  # New row with column span

        # Shift status indicator down
        self.status_label = tk.Label(monitor_frame, text="Status: Disconnected", fg="red")
        self.status_label.grid(row=3, column=0, columnspan=2)

        # Shift line ending options down
        self.line_ending_var = tk.StringVar(value="\n")
        self.line_ending_frame = tk.Frame(monitor_frame)
        self.line_ending_frame.grid(row=4, column=0, columnspan=2)

        tk.Radiobutton(self.line_ending_frame, text="No Line Ending",
                       variable=self.line_ending_var, value="").pack(side=tk.LEFT)
        tk.Radiobutton(self.line_ending_frame, text="New Line",
                       variable=self.line_ending_var, value="\n").pack(side=tk.LEFT)
        tk.Radiobutton(self.line_ending_frame, text="Carriage Return",
                       variable=self.line_ending_var, value="\r").pack(side=tk.LEFT)
        tk.Radiobutton(self.line_ending_frame, text="Both NL & CR",
                       variable=self.line_ending_var, value="\r\n").pack(side=tk.LEFT)

        # Data input field
        self.data_frame = tk.Frame(monitor_frame)
        self.data_frame.grid(row=5, column=0, columnspan=2, sticky='ew')
        monitor_frame.rowconfigure(5, weight=0)  # Don't expand input row

        self.data_entry = tk.Entry(self.data_frame)
        self.data_entry.pack(fill=tk.X, expand=True, padx=5, pady=2)
        self.data_entry.bind("<Return>", self.write_to_port_gui)
        self.data_entry.focus_set()  # Auto focus on the input field

        # Output frame
        self.output_frame = tk.Frame(monitor_frame)
        self.output_frame.grid(row=6, column=0, columnspan=2, sticky='nsew')
        monitor_frame.rowconfigure(6, weight=1)  # Make output frame expandable

        self.scrollbar = tk.Scrollbar(self.output_frame)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.output_text = tk.Text(self.output_frame, height=10, width=50, yscrollcommand=self.scrollbar.set)
        self.output_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.scrollbar.config(command=self.output_text.yview)

        # --- Upload Sketch Tab ---
        # Configure column weights
        upload_frame.columnconfigure(0, weight=1)
        upload_frame.columnconfigure(1, weight=1)

        # Sketch selection
        self.sketch_frame = tk.Frame(upload_frame)
        self.sketch_frame.grid(row=0, column=0, columnspan=2, sticky='ew')

        self.sketch_label = tk.Label(self.sketch_frame, text="Sketch:")
        self.sketch_label.pack(side=tk.LEFT)

        self.sketch_entry = tk.Entry(self.sketch_frame)
        self.sketch_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)

        self.browse_button = tk.Button(self.sketch_frame, text="Browse", command=self.browse_sketch)
        self.browse_button.pack(side=tk.RIGHT)

        self.board_label = tk.Label(upload_frame, text="Board:")
        self.board_label.grid(row=1, column=0)

        # Create a list of available FQBNs
        self.board_options = [
            "arduino:avr:uno",
            "arduino:avr:mega",
            "arduino:avr:nano",
            "arduino:avr:leonardo",
            "arduino:samd:mkr1000",
            # Add more FQBNs as needed
        ]

        self.board_var = tk.StringVar()
        self.board_combo = ttk.Combobox(upload_frame, values=self.board_options, textvariable=self.board_var, state='readonly')
        self.board_combo.grid(row=1, column=1)
        self.board_combo.set(self.board_options[0])  # Set default value

        self.compile_upload_button = tk.Button(upload_frame, text="Compile and Upload",
                                               command=self.compile_and_upload_gui)
        self.compile_upload_button.grid(row=2, column=0, columnspan=2)

        self.auto_detect_board_button = tk.Button(upload_frame, text="Auto Detect Board",
                                                  command=self.auto_detect_board)
        self.auto_detect_board_button.grid(row=3, column=0, columnspan=2)

        # Add output text area to the Upload Sketch tab
        self.upload_output_frame = tk.Frame(upload_frame)
        self.upload_output_frame.grid(row=4, column=0, columnspan=2, sticky='nsew')
        upload_frame.rowconfigure(4, weight=1)

        self.upload_scrollbar = tk.Scrollbar(self.upload_output_frame)
        self.upload_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.upload_output_text = tk.Text(
            self.upload_output_frame, height=10, width=50, yscrollcommand=self.upload_scrollbar.set
        )
        self.upload_output_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.upload_scrollbar.config(command=self.upload_output_text.yview)

        # Auto-detect board and connect to first port
        self.auto_detect_board()
        if not self.selected_port:  # If auto-detect didn't find a port
            self.auto_connect_first_port()

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
            
        board = self.board_var.get()
        if not board:
            self.upload_output_text.insert(tk.END, "Please select a board\n")
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
