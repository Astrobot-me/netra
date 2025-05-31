import customtkinter as ctk
import tkinter as tk
from PIL import Image, ImageTk

class TrafficSignal(ctk.CTkCanvas):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self.width = 50
        self.height = 50
        self.configure(width=self.width, height=self.height, highlightthickness=0)
        self.color = "red"  # Initial color: Red
        self.draw_signal()
        self.bind("<Button-1>", self.toggle_color)

    def draw_signal(self):
        self.delete("all")
        # Draw rectangle
        self.create_rectangle(5, 5, self.width-5, self.height-5, outline="white", fill="black")
        # Draw circle
        circle_size = min(self.width, self.height) * 0.6
        circle_x = (self.width - circle_size) / 2
        circle_y = (self.height - circle_size) / 2
        self.create_oval(circle_x, circle_y, circle_x + circle_size, circle_y + circle_size, fill=self.color)

    def toggle_color(self, event):
        if self.color == "red":
            self.color = "green"
        elif self.color == "green":
            self.color = "yellow"
        else:
            self.color = "red"
        self.draw_signal()

class LaneWidget(ctk.CTkFrame):
    def __init__(self, parent, lane_name, **kwargs):
        super().__init__(parent, **kwargs)
        self.configure(fg_color="#333333", corner_radius=10)

        # Traffic signal
        self.signal = TrafficSignal(self)
        self.signal.pack(pady=5)

        # Lane label
        label = ctk.CTkLabel(self, text=lane_name, font=("Arial", 16))
        label.pack()

        # Video placeholder (CustomTkinter doesn't support video natively)
        video_frame = ctk.CTkFrame(self, width=300, height=200, fg_color="#555555")
        video_frame.pack(pady=5)
        video_label = ctk.CTkLabel(video_frame, text="Video Placeholder\n(Autoplay not supported in Pyodide)", font=("Arial", 12))
        video_label.pack(expand=True)

        # Play/Pause button (for future video integration)
        self.play_pause_btn = ctk.CTkButton(self, text="Pause", command=self.toggle_video)
        self.play_pause_btn.pack(pady=5)

    def toggle_video(self):
        # Placeholder for video control (not functional in Pyodide)
        if self.play_pause_btn.cget("text") == "Pause":
            self.play_pause_btn.configure(text="Play")
        else:
            self.play_pause_btn.configure(text="Pause")

class TrafficApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Traffic Signal UI")
        self.geometry("1500x800")

        # Main layout
        main_frame = ctk.CTkFrame(self, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Lanes grid (2x2)
        lanes_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        lanes_frame.grid(row=0, column=0, sticky="nsew", padx=5)

        # Configure grid
        lanes_frame.grid_columnconfigure((0, 1), weight=1)
        lanes_frame.grid_rowconfigure((0, 1), weight=1)

        # Add lanes
        LaneWidget(lanes_frame, "Lane 1").grid(row=0, column=0, padx=5, pady=5, sticky="nsew")
        LaneWidget(lanes_frame, "Lane 2").grid(row=0, column=1, padx=5, pady=5, sticky="nsew")
        LaneWidget(lanes_frame, "Lane 3").grid(row=1, column=0, padx=5, pady=5, sticky="nsew")
        LaneWidget(lanes_frame, "Lane 4").grid(row=1, column=1, padx=5, pady=5, sticky="nsew")

        # Accident panel
        accident_frame = ctk.CTkFrame(main_frame, width=150, fg_color="#222222")
        accident_frame.grid(row=0, column=1, sticky="nsew", padx=5)
        accident_label = ctk.CTkLabel(accident_frame, text="Accident", font=("Arial", 16))
        accident_label.pack(pady=10)

        # Configure main frame grid
        main_frame.grid_columnconfigure(0, weight=4)
        main_frame.grid_columnconfigure(1, weight=1)
        main_frame.grid_rowconfigure(0, weight=1)

if __name__ == "__main__":
    app = TrafficApp()
    app.mainloop()