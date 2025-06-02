import serial
import serial.tools.list_ports
import datetime
from datetime import datetime, timezone
import pandas as pd
import time
import matplotlib.pyplot as plt
from enum import Enum
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import firebase_admin
from firebase_admin import credentials, firestore
from google.cloud.firestore_v1.base_query import FieldFilter

class LightState(Enum):
    GREEN = 1
    YELLOW = 2
    RED = 3

class Lane:
    def __init__(self, name, csv_file=None):
        self.name = name
        self.csv_file = csv_file
        self.data = None
        self.vehicle_queue = {'car': 0, 'bus': 0, 'truck': 0}
        self.history = []
        self.current_state = LightState.RED
        self.state_start_time = 0
        self.state_duration = 0  # Track how long in current state (in seconds)
        self.time_remaining = 0  # Time until next state change (in seconds)
        self.vehicles_passed = 0
        self.last_processed_time = 0  # in seconds

    def load_data(self, csv_file=None):
        if csv_file:
            self.csv_file = csv_file
        try:
            if self.csv_file:
                self.data = pd.read_csv(self.csv_file)
                if 'Timestamp (s)' not in self.data.columns:
                    if 'Timestamp (min)' in self.data.columns:
                        self.data['Timestamp (s)'] = self.data['Timestamp (min)'] * 60
                    else:
                        raise ValueError("CSV must contain either 'Timestamp (min)' or 'Timestamp (s)' column")

                required_cols = ['Car', 'Bus', 'Truck', 'Total']
                for col in required_cols:
                    if col not in self.data.columns:
                        raise ValueError(f"CSV must contain '{col}' column")
                return True
            return False
        except Exception as e:
            messagebox.showerror("Error", f"Error loading {self.name} data: {e}")
            return False

    def add_vehicles(self, timestamp):
        if self.data is None:
            return 0

        # Only process new arrivals since last processed time
        arrivals = self.data[(self.data['Timestamp (s)'] > self.last_processed_time) &
                           (self.data['Timestamp (s)'] <= timestamp)]

        if not arrivals.empty:
            cars = arrivals['Car'].sum()
            buses = arrivals['Bus'].sum()
            trucks = arrivals['Truck'].sum()

            self.vehicle_queue['car'] += cars
            self.vehicle_queue['bus'] += buses
            self.vehicle_queue['truck'] += trucks

            self.last_processed_time = timestamp
            return arrivals['Total'].sum()
        return 0

    def process_green_light(self, current_time, passing_rate):
        time_in_state = current_time - self.state_start_time
        total_vehicles = sum(self.vehicle_queue.values())

        if total_vehicles == 0:
            return 0

        # Calculate how many vehicles can pass based on time in green state
        vehicles_able_to_pass = min(
            int(passing_rate * time_in_state),
            total_vehicles
        )

        # Calculate proportions for each vehicle type
        if total_vehicles > 0:
            car_pct = self.vehicle_queue['car'] / total_vehicles
            bus_pct = self.vehicle_queue['bus'] / total_vehicles
            truck_pct = self.vehicle_queue['truck'] / total_vehicles
        else:
            car_pct = bus_pct = truck_pct = 0

        # Calculate vehicles to pass for each type
        cars_passed = min(int(vehicles_able_to_pass * car_pct), self.vehicle_queue['car'])
        buses_passed = min(int(vehicles_able_to_pass * bus_pct), self.vehicle_queue['bus'])
        trucks_passed = min(int(vehicles_able_to_pass * truck_pct), self.vehicle_queue['truck'])

        # Distribute any remaining vehicles due to rounding
        remaining = vehicles_able_to_pass - (cars_passed + buses_passed + trucks_passed)
        while remaining > 0 and total_vehicles > 0:
            if self.vehicle_queue['car'] > cars_passed:
                cars_passed += 1
            elif self.vehicle_queue['bus'] > buses_passed:
                buses_passed += 1
            elif self.vehicle_queue['truck'] > trucks_passed:
                trucks_passed += 1
            else:
                break
            remaining -= 1

        # Update queues
        self.vehicle_queue['car'] = max(0, self.vehicle_queue['car'] - cars_passed)
        self.vehicle_queue['bus'] = max(0, self.vehicle_queue['bus'] - buses_passed)
        self.vehicle_queue['truck'] = max(0, self.vehicle_queue['truck'] - trucks_passed)

        self.vehicles_passed = cars_passed + buses_passed + trucks_passed
        return self.vehicles_passed

class IntersectionController:
    def __init__(self):
        # Configuration (in seconds)
        self.base_green_duration = 60.0  # 60 seconds = 1 min
        self.yellow_duration = 12.0  # 12 seconds
        self.all_red_duration = 6.0  # 6 seconds
        self.phase_transition_buffer = 3.0  # 3 seconds buffer
        self.passing_rate = 0.25  # vehicles per second (15 veh/min = 0.25 veh/sec)

        # Threshold for dynamic adjustment
        self.queue_threshold = 35  # vehicles

        # Minimum and maximum green durations
        self.min_green_duration = 30.0  # 30 seconds minimum
        self.max_green_duration = 120.0  # 120 seconds maximum

        # Create lanes
        self.lanes = {
            'north': Lane('North'),
            'south': Lane('South'),
            'east': Lane('East'),
            'west': Lane('West')
        }

        # Phases (opposite directions go together)
        self.phases = [
            ['north', 'south'],  # Phase 1: North-South green
            ['east', 'west']     # Phase 2: East-West green
        ]
        self.current_phase = 0
        self.cycle_start_time = 0
        self.green_duration = self.base_green_duration
        self.in_yellow = False
        self.in_all_red = False
        self.phase_transition_start = 0

    def load_all_data(self):
        return all(lane.load_data() for lane in self.lanes.values() if lane.csv_file)

    def set_phase(self, phase_index, current_time):
        """Set a new phase with proper state transitions"""
        # If we're not in transition, start yellow phase
        if not self.in_yellow and not self.in_all_red:
            self.in_yellow = True
            self.phase_transition_start = current_time
            for name in self.phases[self.current_phase]:
                self.lanes[name].current_state = LightState.YELLOW
                self.lanes[name].state_start_time = current_time
                self.lanes[name].time_remaining = self.yellow_duration
            return

        # If we're in yellow, transition to all-red
        if self.in_yellow and not self.in_all_red:
            self.in_yellow = False
            self.in_all_red = True
            self.phase_transition_start = current_time
            for name in self.lanes:
                self.lanes[name].current_state = LightState.RED
                self.lanes[name].state_start_time = current_time
                self.lanes[name].time_remaining = self.all_red_duration
            return

        # After all-red, switch to new phase
        self.in_yellow = False
        self.in_all_red = False
        self.current_phase = phase_index
        self.cycle_start_time = current_time

        # Set states for all lanes
        for name, lane in self.lanes.items():
            if name in self.phases[phase_index]:
                lane.current_state = LightState.GREEN
                lane.time_remaining = self.green_duration
            else:
                lane.current_state = LightState.RED
                # Calculate time until next green for this lane
                lane.time_remaining = self.green_duration + self.yellow_duration + self.all_red_duration
            lane.state_start_time = current_time

        # Update Firestore with phase change
        if hasattr(self, 'session_ref') and self.session_ref:
            try:
                self.session_ref.update({
                    'current_phase': phase_index,
                    **{
                        f'lanes.{name}.time_remaining': lane.time_remaining
                        for name, lane in self.lanes.items()
                    }
                })
            except Exception as e:
                print(f"Error updating phase in Firestore: {e}")

    def update_intersection(self, current_time, db=None, session_ref=None):
        # Update all lanes with their individual timings
        timestep_data = {
            'time': current_time,
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'current_phase': self.current_phase,
            'lanes': {}
        }

        for name, lane in self.lanes.items():
            # Update state duration and time remaining
            lane.state_duration = current_time - lane.state_start_time

            # Calculate time remaining based on current state
            if lane.current_state == LightState.GREEN:
                lane.time_remaining = max(0, self.green_duration - lane.state_duration)
            elif lane.current_state == LightState.YELLOW:
                lane.time_remaining = max(0, self.yellow_duration - lane.state_duration)
            else:  # RED
                # For red lights, calculate time until next green
                if name in self.phases[self.current_phase]:
                    # In active phase but currently red (during yellow/all-red transition)
                    if self.in_all_red:
                        lane.time_remaining = max(0, self.all_red_duration )
                    elif self.in_yellow:
                        lane.time_remaining = max(0, ( self.all_red_duration))
                else:
                    # In inactive phase - time until next green phase
                    phase_time_remaining = self.green_duration - (current_time - self.cycle_start_time)
                    lane.time_remaining = max(0, phase_time_remaining + self.all_red_duration)

            # Add arriving vehicles
            arrivals = lane.add_vehicles(current_time)

            # Process vehicles based on light state
            if lane.current_state == LightState.GREEN:
                passed = lane.process_green_light(current_time, self.passing_rate)

            # Record lane data with timing information
            lane_data = {
                'state': lane.current_state.name,
                'state_duration': lane.state_duration,
                'time_remaining': lane.time_remaining,
                'queue': int(sum(lane.vehicle_queue.values())),
                'arrivals': int(arrivals),
                'departures': int(lane.vehicles_passed),
                'vehicle_counts': {
                    'car': int(lane.vehicle_queue['car']),
                    'bus': int(lane.vehicle_queue['bus']),
                    'truck': int(lane.vehicle_queue['truck'])
                }
            }

            lane.history.append({
                'time': current_time,
                **lane_data
            })

            timestep_data['lanes'][name] = lane_data
            lane.vehicles_passed = 0

        # Send data to Firestore if available
        if db and session_ref:
            try:
                session_ref.update({
                    'timesteps': firestore.ArrayUnion([timestep_data]),
                    'current_phase': self.current_phase
                })
            except Exception as e:
                print(f"Error writing to Firestore: {e}")

    def check_phase_change(self, current_time):
        time_in_phase = current_time - self.cycle_start_time

        # Calculate queue sizes for active lanes
        active_lanes = [self.lanes[name] for name in self.phases[self.current_phase]]
        max_queue = max(sum(lane.vehicle_queue.values()) for lane in active_lanes)

        # Dynamic green duration calculation
        if max_queue > self.queue_threshold:
            # Increase green time proportionally to queue size, but within limits
            queue_excess = max_queue - self.queue_threshold
            self.green_duration = min(
                self.base_green_duration + (queue_excess * 3),  # 3 sec per extra vehicle
                self.max_green_duration
            )
        else:
            # Use base duration if queue is below threshold
            self.green_duration = self.base_green_duration

        # Ensure we don't go below minimum duration
        self.green_duration = max(self.green_duration, self.min_green_duration)

        # Check if we're in transition
        if self.in_yellow or self.in_all_red:
            transition_time = current_time - self.phase_transition_start
            if self.in_yellow and transition_time >= self.yellow_duration:
                self.set_phase((self.current_phase + 1) % len(self.phases), current_time)
            elif self.in_all_red and transition_time >= self.all_red_duration:
                self.set_phase((self.current_phase + 1) % len(self.phases), current_time)
            return

        # Check if any non-active lane has queue exceeding threshold
        for name, lane in self.lanes.items():
            if name not in self.phases[self.current_phase] and sum(lane.vehicle_queue.values()) > self.queue_threshold:
                # Only switch if current phase has been active for at least minimum duration
                if time_in_phase >= self.min_green_duration:
                    self.set_phase((self.current_phase + 1) % len(self.phases), current_time)
                    return

        # Check if current phase should end normally
        if time_in_phase >= self.green_duration:
            self.set_phase((self.current_phase + 1) % len(self.phases), current_time)

    def generate_report(self):
        plt.figure(figsize=(15, 10))

        # Plot queues for each lane
        for i, (name, lane) in enumerate(self.lanes.items()):
            df = pd.DataFrame(lane.history)

            plt.subplot(2, 2, i+1)
            plt.plot(df['time'], df['queue'], 'b-', label='Queue')
            plt.plot(df['time'], df['arrivals'], 'g--', label='Arrivals', alpha=0.5)
            plt.plot(df['time'], df['departures'], 'r:', label='Departures', alpha=0.5)

            # Add light state background colors
            prev_time = 0
            prev_state = None
            for _, row in df.iterrows():
                if row['state'] != prev_state:
                    if prev_state is not None:
                        color = {'GREEN': 'lightgreen', 'YELLOW': 'yellow', 'RED': 'lightcoral'}[prev_state]
                        plt.axvspan(prev_time, row['time'], facecolor=color, alpha=0.3)
                    prev_state = row['state']
                    prev_time = row['time']

            if prev_state is not None:
                color = {'GREEN': 'lightgreen', 'YELLOW': 'yellow', 'RED': 'lightcoral'}[prev_state]
                plt.axvspan(prev_time, df['time'].max(), facecolor=color, alpha=0.3)

            plt.title(f"{name.capitalize()} Lane Traffic")
            plt.xlabel('Time (sec)')
            plt.ylabel('Vehicles')
            plt.legend()
            plt.grid(True)

        plt.tight_layout()
        plt.savefig("4way_intersection_simulation.png")
        print("\nReport generated: 4way_intersection_simulation.png")

# [Rest of the TrafficLightSimulatorUI class remains the same]

class TrafficLightSimulatorUI:
    def __init__(self, root):
        self.root = root
        self.root.title("4-Way Intersection Traffic Light Simulator")
        self.root.geometry("1200x900")

        self.init_serial_connection()

        # Initialize Firestore
        self.init_firestore()

        # Simulation control variables
        self.sim_running = False
        self.sim_paused = False
        self.sim_time = 0  # now in seconds
        self.sim_duration = 900  # 15 min = 900 sec
        self.time_step = 6  # 0.1 min = 6 sec
        self.plot_update_interval = 5  # Update plots every 5 steps
        self.step_count = 0

        # Create controller
        self.controller = IntersectionController()

        # Setup UI
        self.create_widgets()

    def init_firestore(self):
        try:
            if not firebase_admin._apps:
                cred = credentials.Certificate("serviceAccountKey.json")
                firebase_admin.initialize_app(cred)

            self.db = firestore.client()
            self.session_ref = None  # Will hold reference to current session document
            self.sessions_collection = self.db.collection('traffic_sessions')
        except Exception as e:
            messagebox.showerror("Firestore Error", f"Failed to initialize Firestore: {e}")
            self.db = None

    def create_widgets(self):
        # Control frame
        control_frame = ttk.LabelFrame(self.root, text="Simulation Controls", padding=10)
        control_frame.pack(fill=tk.X, padx=10, pady=5)

        # File selection
        file_frame = ttk.Frame(control_frame)
        file_frame.pack(fill=tk.X, pady=5)

        ttk.Label(file_frame, text="Lane Data Files:").pack(side=tk.LEFT)

        lanes = ['north', 'south', 'east', 'west']
        self.file_entries = {}
        self.file_buttons = {}

        for lane in lanes:
            lane_frame = ttk.Frame(file_frame)
            lane_frame.pack(fill=tk.X, pady=2)

            ttk.Label(lane_frame, text=f"{lane.capitalize()}:").pack(side=tk.LEFT)
            self.file_entries[lane] = ttk.Entry(lane_frame, width=40)
            self.file_entries[lane].pack(side=tk.LEFT, padx=5)
            self.file_buttons[lane] = ttk.Button(lane_frame, text="Browse",
                                               command=lambda l=lane: self.browse_file(l))
            self.file_buttons[lane].pack(side=tk.LEFT)

        # Parameters frame
        param_frame = ttk.Frame(control_frame)
        param_frame.pack(fill=tk.X, pady=5)

        # First row of parameters
        param_row1 = ttk.Frame(param_frame)
        param_row1.pack(fill=tk.X)

        ttk.Label(param_row1, text="Base Green Duration (min):").pack(side=tk.LEFT)
        self.green_duration_entry = ttk.Entry(param_row1, width=8)
        self.green_duration_entry.insert(0, "1.0")
        self.green_duration_entry.pack(side=tk.LEFT, padx=5)

        ttk.Label(param_row1, text="Yellow Duration (min):").pack(side=tk.LEFT, padx=10)
        self.yellow_duration_entry = ttk.Entry(param_row1, width=8)
        self.yellow_duration_entry.insert(0, "0.2")
        self.yellow_duration_entry.pack(side=tk.LEFT)

        ttk.Label(param_row1, text="All-Red Duration (min):").pack(side=tk.LEFT, padx=10)
        self.all_red_entry = ttk.Entry(param_row1, width=8)
        self.all_red_entry.insert(0, "0.1")
        self.all_red_entry.pack(side=tk.LEFT)

        # Second row of parameters
        param_row2 = ttk.Frame(param_frame)
        param_row2.pack(fill=tk.X)

        ttk.Label(param_row2, text="Passing Rate (veh/min):").pack(side=tk.LEFT)
        self.passing_rate_entry = ttk.Entry(param_row2, width=8)
        self.passing_rate_entry.insert(0, "15")
        self.passing_rate_entry.pack(side=tk.LEFT, padx=5)

        ttk.Label(param_row2, text="Sim Duration (min):").pack(side=tk.LEFT, padx=10)
        self.duration_entry = ttk.Entry(param_row2, width=8)
        self.duration_entry.insert(0, "15")
        self.duration_entry.pack(side=tk.LEFT)

        ttk.Label(param_row2, text="Transition Buffer (min):").pack(side=tk.LEFT, padx=10)
        self.transition_buffer_entry = ttk.Entry(param_row2, width=8)
        self.transition_buffer_entry.insert(0, "0.05")
        self.transition_buffer_entry.pack(side=tk.LEFT)

        # Button frame
        button_frame = ttk.Frame(control_frame)
        button_frame.pack(fill=tk.X, pady=5)

        self.start_button = ttk.Button(button_frame, text="Start", command=self.start_simulation)
        self.start_button.pack(side=tk.LEFT, padx=5)

        self.pause_button = ttk.Button(button_frame, text="Pause", command=self.pause_simulation, state=tk.DISABLED)
        self.pause_button.pack(side=tk.LEFT, padx=5)

        self.stop_button = ttk.Button(button_frame, text="Stop", command=self.stop_simulation, state=tk.DISABLED)
        self.stop_button.pack(side=tk.LEFT, padx=5)

        self.step_button = ttk.Button(button_frame, text="Step", command=self.step_simulation, state=tk.DISABLED)
        self.step_button.pack(side=tk.LEFT, padx=5)

        # Speed control
        speed_frame = ttk.Frame(control_frame)
        speed_frame.pack(fill=tk.X, pady=5)

        ttk.Label(speed_frame, text="Simulation Speed:").pack(side=tk.LEFT)
        self.speed_scale = ttk.Scale(speed_frame, from_=1, to=10, orient=tk.HORIZONTAL, length=200)
        self.speed_scale.set(5)
        self.speed_scale.pack(side=tk.LEFT, padx=5)

        self.speed_label = ttk.Label(speed_frame, text="5x")
        self.speed_label.pack(side=tk.LEFT)

        self.speed_scale.bind("<Motion>", self.update_speed_label)

        # Status frame
        status_frame = ttk.LabelFrame(self.root, text="Simulation Status", padding=10)
        status_frame.pack(fill=tk.X, padx=10, pady=5)

        self.time_label = ttk.Label(status_frame, text="Time: 0.0 min")
        self.time_label.pack(anchor=tk.W)

        self.phase_label = ttk.Label(status_frame, text="Current Phase: Not started")
        self.phase_label.pack(anchor=tk.W)

        # Phase timer label
        self.phase_timer_label = ttk.Label(status_frame, text="Phase Time Remaining: --")
        self.phase_timer_label.pack(anchor=tk.W)

        # Traffic light visualization frame
        light_frame = ttk.Frame(status_frame)
        light_frame.pack(fill=tk.X, pady=10)

        ttk.Label(light_frame, text="Traffic Lights:").pack(anchor=tk.W)

        # Create a canvas for traffic lights
        self.light_canvas = tk.Canvas(light_frame, height=100, bg='white')
        self.light_canvas.pack(fill=tk.X, pady=5)

        # Draw the intersection with traffic lights
        self.draw_intersection()

        # Lane status frame
        lane_status_frame = ttk.Frame(status_frame)
        lane_status_frame.pack(fill=tk.X, pady=5)

        self.lane_labels = {}
        for lane in ['north', 'south', 'east', 'west']:
            frame = ttk.Frame(lane_status_frame)
            frame.pack(side=tk.LEFT, padx=10)

            ttk.Label(frame, text=f"{lane.capitalize()}:").pack()
            self.lane_labels[lane] = ttk.Label(frame, text="RED | Queue: 0")
            self.lane_labels[lane].pack()

        # Visualization frame
        vis_frame = ttk.LabelFrame(self.root, text="Visualization", padding=10)
        vis_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        self.fig, self.axs = plt.subplots(2, 2, figsize=(10, 8))
        self.canvas = FigureCanvasTkAgg(self.fig, master=vis_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        # Initialize plots
        self.initialize_plots()

    def update_speed_label(self, event=None):
        speed = int(self.speed_scale.get())
        self.speed_label.config(text=f"{speed}x")

    def init_serial_connection(self):
        try:
            # List all available serial ports
            ports = serial.tools.list_ports.comports()
            if not ports:
                messagebox.showwarning("Warning", "No serial ports found. Using simulation only.")
                self.serial_conn = None
                return False

            # Print available ports for debugging
            print("Available ports:")
            for p in ports:
                print(f"- {p.device} (Desc: {p.description})")

            # Try to find Arduino (common descriptors include 'Arduino' or 'USB Serial')
            arduino_port = None
            for p in ports:
                if 'Arduino' in p.description or 'USB Serial' in p.description or 'CH340' in p.description:
                    arduino_port = p.device
                    break

            if not arduino_port:
                # If no Arduino found, try the first available port (you can manually override)
                arduino_port = ports[0].device
                messagebox.showwarning("Warning", f"Arduino not detected. Trying {arduino_port}")

            # Attempt connection
            self.serial_conn = serial.Serial(arduino_port, 9600, timeout=1)
            time.sleep(2)  # Wait for connection
            print(f"Connected to Arduino on {arduino_port}")
            return True
        except Exception as e:
            messagebox.showerror("Error", f"Failed to connect to Arduino: {e}")
            self.serial_conn = None
            return False

    def update_arduino_lights(self):
        if not hasattr(self, 'serial_conn') or not self.serial_conn:
            return

        try:
            for name, lane in self.controller.lanes.items():
                # Map lane name to direction character
                direction = name[0].upper()

                # Get current state (0=RED, 1=YELLOW, 2=GREEN)
                state = lane.current_state.value - 1  # Convert from Enum (1-3) to 0-2

                # Send command to Arduino
                command = f"{direction}:{state}\n"
                self.serial_conn.write(command.encode())
        except Exception as e:
            print(f"Error updating Arduino: {e}")
            # Try to reconnect
            self.init_serial_connection()

    def draw_intersection(self):
        self.light_canvas.delete("all")
        width = self.light_canvas.winfo_width()
        height = self.light_canvas.winfo_height()

        if width < 10 or height < 10:  # Canvas not yet visible
            return

        center_x = width // 2
        center_y = height // 2
        light_radius = 15
        road_width = 80

        # Draw roads
        self.light_canvas.create_line(center_x, 0, center_x, height, width=road_width, fill='gray', tags='road')
        self.light_canvas.create_line(0, center_y, width, center_y, width=road_width, fill='gray', tags='road')

        # Draw traffic lights for each direction
        self.traffic_lights = {}

        # North light (top center, facing south)
        north_x = center_x
        north_y = center_y - road_width//2 - 40
        self.draw_traffic_light(north_x, north_y, 'north', 'south')

        # South light (bottom center, facing north)
        south_x = center_x
        south_y = center_y + road_width//2 + 40
        self.draw_traffic_light(south_x, south_y, 'south', 'north')

        # East light (right center, facing west)
        east_x = center_x + road_width//2 + 40
        east_y = center_y
        self.draw_traffic_light(east_x, east_y, 'east', 'west')

        # West light (left center, facing east)
        west_x = center_x - road_width//2 - 40
        west_y = center_y
        self.draw_traffic_light(west_x, west_y, 'west', 'east')

    def draw_traffic_light(self, x, y, lane_name, direction):
        # Draw light housing
        light_width = 30
        light_height = 80
        self.light_canvas.create_rectangle(
            x - light_width//2, y - light_height//2,
            x + light_width//2, y + light_height//2,
            fill='black', outline='gray', width=2
        )

        # Draw pole
        pole_height = 20
        if direction in ['north', 'south']:
            pole_y = y + light_height//2 if direction == 'north' else y - light_height//2
            self.light_canvas.create_line(
                x, y + (light_height//2 if direction == 'north' else -light_height//2),
                x, pole_y + (pole_height if direction == 'north' else -pole_height),
                width=8, fill='black'
            )
        else:
            pole_x = x + light_width//2 if direction == 'west' else x - light_width//2
            self.light_canvas.create_line(
                x + (light_width//2 if direction == 'west' else -light_width//2), y,
                pole_x + (pole_height if direction == 'west' else -pole_height), y,
                width=8, fill='black'
            )

        # Draw lights (initially all off)
        red_light = self.light_canvas.create_oval(
            x - 10, y - 30,
            x + 10, y - 10,
            fill='gray', outline='white'
        )

        yellow_light = self.light_canvas.create_oval(
            x - 10, y - 10,
            x + 10, y + 10,
            fill='gray', outline='white'
        )

        green_light = self.light_canvas.create_oval(
            x - 10, y + 10,
            x + 10, y + 30,
            fill='gray', outline='white'
        )

        self.traffic_lights[lane_name] = {
            'red': red_light,
            'yellow': yellow_light,
            'green': green_light
        }

        # Draw lane label
        label_y = y - 50 if direction in ['north', 'south'] else y
        label_x = x - 50 if direction in ['east', 'west'] else x
        self.light_canvas.create_text(
            label_x, label_y,
            text=lane_name.capitalize(),
            fill='black', font=('Arial', 10)
        )

    def toggle_disco_mode(self, enable):
        if not hasattr(self, 'serial_conn') or not self.serial_conn:
            print("Arduino not connected - disco mode unavailable")
            return

        try:
            command = "DISCO:ON" if enable else "DISCO:OFF"
            self.serial_conn.write((command + "\n").encode())
            print(f"Disco mode {'activated' if enable else 'deactivated'}")
        except Exception as e:
            print(f"Error toggling disco mode: {e}")
            # Try to reconnect
            self.init_serial_connection()

    def update_traffic_lights(self):
        for lane_name, light_ids in self.traffic_lights.items():
            lane = self.controller.lanes[lane_name]

            # Turn all lights off first
            self.light_canvas.itemconfig(light_ids['red'], fill='gray')
            self.light_canvas.itemconfig(light_ids['yellow'], fill='gray')
            self.light_canvas.itemconfig(light_ids['green'], fill='gray')

            # Turn on the active light
            if lane.current_state == LightState.RED:
                self.light_canvas.itemconfig(light_ids['red'], fill='red')
            elif lane.current_state == LightState.YELLOW:
                # Make yellow light blink during transitions
                if int(self.sim_time * 10) % 2 == 0:  # Blink every 0.2 minutes
                    self.light_canvas.itemconfig(light_ids['yellow'], fill='yellow')
                else:
                    self.light_canvas.itemconfig(light_ids['yellow'], fill='gray')
            elif lane.current_state == LightState.GREEN:
                self.light_canvas.itemconfig(light_ids['green'], fill='green')

    def browse_file(self, lane):
        filename = filedialog.askopenfilename(title=f"Select {lane} lane data file",
                                            filetypes=(("CSV files", "*.csv"), ("All files", "*.*")))
        if filename:
            self.file_entries[lane].delete(0, tk.END)
            self.file_entries[lane].insert(0, filename)

    def initialize_plots(self):
        for ax in self.axs.flat:
            ax.clear()
            ax.set_title('')
            ax.set_xlabel('Time (min)')
            ax.set_ylabel('Vehicles')
            ax.grid(True)
        self.canvas.draw()

    def update_plots(self):
        for i, (name, lane) in enumerate(self.controller.lanes.items()):
            ax = self.axs[i//2, i%2]
            ax.clear()

            if lane.history:
                df = pd.DataFrame(lane.history)
                ax.plot(df['time'], df['queue'], 'b-', label='Queue')
                ax.plot(df['time'], df['arrivals'], 'g--', label='Arrivals', alpha=0.5)
                ax.plot(df['time'], df['departures'], 'r:', label='Departures', alpha=0.5)

                # Add light state background colors
                prev_time = 0
                prev_state = None
                for _, row in df.iterrows():
                    if row['state'] != prev_state:
                        if prev_state is not None:
                            color = {'GREEN': 'lightgreen', 'YELLOW': 'yellow', 'RED': 'lightcoral'}[prev_state]
                            ax.axvspan(prev_time, row['time'], facecolor=color, alpha=0.3)
                        prev_state = row['state']
                        prev_time = row['time']

                if prev_state is not None:
                    color = {'GREEN': 'lightgreen', 'YELLOW': 'yellow', 'RED': 'lightcoral'}[prev_state]
                    ax.axvspan(prev_time, df['time'].max(), facecolor=color, alpha=0.3)

            ax.set_title(f"{name.capitalize()} Lane Traffic")
            ax.set_xlabel('Time (sec)')  # Changed from 'Time (min)'
            ax.legend()
            ax.grid(True)

        self.canvas.draw()

    def update_ui(self):
        # Update time and phase labels - show both seconds and minutes
        minutes = self.sim_time / 60
        self.time_label.config(text=f"Time: {self.sim_time:.0f} sec ({minutes:.1f} min)")

        self.update_arduino_lights()

        phase_names = ["North-South", "East-West"]
        phase_idx = self.controller.current_phase
        self.phase_label.config(text=f"Current Phase: {phase_names[phase_idx]}")

        # Update phase timer
        if self.controller.in_yellow:
            time_remaining = max(0, self.controller.yellow_duration - (self.sim_time - self.controller.cycle_start_time))
            self.phase_timer_label.config(text=f"Phase Time Remaining: YELLOW {time_remaining:.0f} sec ({time_remaining/60:.1f} min)")
        else:
            time_remaining = max(0, self.controller.green_duration - (self.sim_time - self.controller.cycle_start_time))
            self.phase_timer_label.config(text=f"Phase Time Remaining: GREEN {time_remaining:.0f} sec ({time_remaining/60:.1f} min)")
        # ... rest of the method ...

        # Update lane status
        for name, lane in self.controller.lanes.items():
            state = lane.current_state.name
            queue = sum(lane.vehicle_queue.values())
            self.lane_labels[name].config(text=f"{state} | Queue: {queue}")

            # Update colors based on state
            color = {'GREEN': 'green', 'YELLOW': 'yellow', 'RED': 'red'}[state]
            self.lane_labels[name].config(foreground=color)

        # Update traffic lights visualization
        self.update_traffic_lights()

        # Update plots periodically
        self.step_count += 1
        if self.step_count % self.plot_update_interval == 0:
            self.update_plots()
            self.step_count = 0

    def load_simulation_parameters(self):
        try:
            # Load lane data files
            for lane in ['north', 'south', 'east', 'west']:
                file_path = self.file_entries[lane].get()
                if file_path:
                    self.controller.lanes[lane].load_data(file_path)
                else:
                    messagebox.showwarning("Warning", f"No file selected for {lane} lane. Using empty data.")

            # Set parameters
            self.controller.base_green_duration = float(self.green_duration_entry.get()) * 60
            self.controller.yellow_duration = float(self.yellow_duration_entry.get()) * 60
            self.controller.all_red_duration = float(self.all_red_entry.get()) * 60
            self.controller.phase_transition_buffer = float(self.transition_buffer_entry.get()) * 60
            self.controller.passing_rate = float(self.passing_rate_entry.get()) / 60  # convert veh/min to veh/sec
            self.sim_duration = float(self.duration_entry.get()) * 60  # convert min to sec

            return True
        except ValueError as e:
            messagebox.showerror("Error", f"Invalid parameter value: {e}")
            return False

    def start_simulation(self):
        if not self.sim_running:
            if self.load_simulation_parameters():
                # Create a new session document in Firestore
                if self.db:
                    from datetime import datetime, timezone
                    import uuid

                    session_id = str(uuid.uuid4())[:8]
                    session_data = {
                        'session_id': session_id,
                        'parameters': {
                            'base_green_duration': float(self.controller.base_green_duration),
                            'yellow_duration': float(self.controller.yellow_duration),
                            'all_red_duration': float(self.controller.all_red_duration),
                            'passing_rate': float(self.controller.passing_rate),
                            'sim_duration': float(self.sim_duration)
                        },
                        'start_time': datetime.now(timezone.utc).isoformat(),
                        'status': 'running',
                        'timesteps': []
                    }

                    doc_ref = self.sessions_collection.document(session_id)
                    doc_ref.set(session_data)
                    self.session_ref = doc_ref

                self.sim_running = True
                self.sim_paused = False
                self.sim_time = 0
                self.step_count = 0

                # Reset controller
                self.controller = IntersectionController()
                self.load_simulation_parameters()

                # Set initial phase
                self.controller.set_phase(0, 0)

                # Update UI controls
                self.start_button.config(state=tk.DISABLED)
                self.pause_button.config(state=tk.NORMAL, text="Pause")
                self.stop_button.config(state=tk.NORMAL)
                self.step_button.config(state=tk.NORMAL)

                # Initialize plots
                self.initialize_plots()

                # Draw intersection
                self.draw_intersection()

                # Start simulation loop
                self.run_simulation_step()

    def pause_simulation(self):
        if self.sim_running:
            self.sim_paused = not self.sim_paused
            self.pause_button.config(text="Resume" if self.sim_paused else "Pause")

            if not self.sim_paused:
                self.run_simulation_step()

    def stop_simulation(self):
        self.sim_running = False
        self.sim_paused = False

        # Update simulation status in Firestore
        if hasattr(self, 'simulation_ref') and self.simulation_ref:
            try:
                self.simulation_ref.update({
                    'end_time': firestore.SERVER_TIMESTAMP,
                    'status': 'completed',
                    'total_vehicles': {
                        lane_name: int(sum(lane.vehicle_queue.values()))  # Convert to native int
                        for lane_name, lane in self.controller.lanes.items()
                    }
                })
            except Exception as e:
                print(f"Error updating Firestore: {e}")

        # Update UI controls
        self.start_button.config(state=tk.NORMAL)
        self.pause_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.DISABLED)
        self.step_button.config(state=tk.DISABLED)

        # Generate final report
        self.controller.generate_report()
        messagebox.showinfo("Simulation Complete", "Simulation finished. Report generated.")

    def step_simulation(self):
        if self.sim_running and self.sim_paused:
            self.run_simulation_step(single_step=True)

    def run_simulation_step(self, single_step=False):
        if not self.sim_running or self.sim_paused and not single_step:
            return

        if self.sim_time <= self.sim_duration:
            # Run simulation step with Firestore references
            self.controller.update_intersection(
                self.sim_time,
                self.db,
                self.session_ref if hasattr(self, 'session_ref') else None
            )
            self.controller.check_phase_change(self.sim_time)

            # Update UI
            self.update_ui()

            # Increment time
            self.sim_time += self.time_step

            # Schedule next step or stop simulation
            if not single_step:
                speed = int(self.speed_scale.get())
                delay = max(50, 500 // speed)  # Adjust delay based on speed (50-500ms)
                self.root.after(delay, self.run_simulation_step)
            else:
                self.stop_simulation()

    def show_about(self):
        messagebox.showinfo("About",
                           "4-Way Intersection Traffic Light Simulator\n\n"
                           "This simulator models traffic flow through a 4-way intersection\n"
                           "with adaptive traffic light control based on vehicle queues.\n\n"
                           "Features:\n"
                           "- Real-time visualization of traffic lights and queues\n"
                           "- Adjustable simulation parameters\n"
                           "- Firestore integration for data logging\n"
                           "- Dynamic traffic light timing based on queue sizes")

    def on_closing(self):
        if messagebox.askokcancel("Quit", "Do you want to quit the simulation?"):
            if self.sim_running:
                self.stop_simulation()
            if hasattr(self, 'serial_conn') and self.serial_conn:
                self.serial_conn.close()
            self.root.destroy()

# Main application
if __name__ == "__main__":
    root = tk.Tk()
    app = TrafficLightSimulatorUI(root)

    # Add menu bar
    menubar = tk.Menu(root)
    filemenu = tk.Menu(menubar, tearoff=0)
    filemenu.add_command(label="Exit", command=app.on_closing)
    menubar.add_cascade(label="File", menu=filemenu)

    helpmenu = tk.Menu(menubar, tearoff=0)
    helpmenu.add_command(label="About", command=app.show_about)
    menubar.add_cascade(label="Help", menu=helpmenu)

    root.config(menu=menubar)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)

    # Handle window resizing
    def on_resize(event):
        app.draw_intersection()
    root.bind("<Configure>", on_resize)

    # Start a thread to monitor console commands
    import threading
    def console_command_handler():
        while True:
            cmd = input("Enter command (disco/stop): ").strip().lower()
            if cmd == "disco":
                app.toggle_disco_mode(True)
            elif cmd == "stop":
                app.toggle_disco_mode(False)

    console_thread = threading.Thread(target=console_command_handler, daemon=True)
    console_thread.start()

    root.mainloop()