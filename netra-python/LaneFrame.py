from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.widget import Widget
from kivy.uix.video import Video
from kivy.uix.button import Button
from kivy.graphics import Color, Rectangle, Ellipse
from kivy.properties import ListProperty
from kivy.core.window import Window
from kivy.logger import Logger

# Set window size to 1500x800
Window.size = (1500, 800)

class TrafficSignal(Widget):
    signal_color = ListProperty([1, 0, 0])  # Default: Red (RGB)

    def __init__(self, label_text, lanename, **kwargs):
        super().__init__(**kwargs)
        self.size_hint_y = None
        self.height = 50
        self.lanename = lanename
        self.label_text = label_text
        self.bind(pos=self.update_signal, size=self.update_signal)
        
        # Create label widgets
        self.lane_label = Label(
            text=self.lanename, 
            size_hint=(None, None), 
            size=(self.width, 30),
            color=[0, 0, 0, 1]  # Black text
        )
        self.text_label = Label(
            text=self.label_text,
            size_hint=(None, None),
            size=(100, 30),
            color=[0, 0, 0, 1]  # Black text
        )
        self.add_widget(self.lane_label)
        self.add_widget(self.text_label)
        
        self.draw_signal()

    def draw_signal(self):
        self.canvas.clear()
        with self.canvas:
            # Draw rectangle (match video width)
            Color(1, 1, 1, 1)  # White border
            Rectangle(pos=self.pos, size=self.size)
            
            # Draw colored circle
            Color(*self.signal_color)
            circle_diameter = min(self.width, self.height) * 0.6
            circle_pos = (self.pos[0] + (self.width - circle_diameter) / 2,
                          self.pos[1] + (self.height - circle_diameter) / 2)
            Ellipse(pos=circle_pos, size=(circle_diameter, circle_diameter))
        
        # Update label positions
        self.lane_label.pos = (self.pos[0], self.pos[1] + self.height - 30)
        self.lane_label.size = (self.width, 30)
        self.text_label.pos = (self.pos[0] - 110, self.pos[1] + (self.height - 30) / 2)

    def update_signal(self, *args):
        self.draw_signal()

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            # Toggle color: Red -> Green -> Yellow -> Red
            if self.signal_color == [1, 0, 0]:  # Red
                self.signal_color = [0, 1, 0]  # Green
            elif self.signal_color == [0, 1, 0]:  # Green
                self.signal_color = [1, 1, 0]  # Yellow
            else:  # Yellow
                self.signal_color = [1, 0, 0]  # Red
            return True
        return super().on_touch_down(touch)

class LaneWidget(BoxLayout):
    def __init__(self, lane_name, **kwargs):
        super().__init__(orientation='vertical', **kwargs)
        self.size_hint_x = None
        self.width = 600  # Fixed width to match video
        
        # Traffic signal
        self.signal = TrafficSignal(lanename=lane_name, label_text='Signal1')
        self.signal.size_hint_x = 1
        self.add_widget(self.signal)
        
        # Video widget
        self.video = Video(
            source=r"C:\Users\Aditya\Documents\netra\resources\8x_traffic.mp4",
            size_hint_y=None,
            height=300,
            state='play',
            allow_stretch=True,
            eos="loop"
        )
        self.video.bind(on_error=self.on_video_error, on_load=self.on_video_load)
        self.add_widget(self.video)
        
        # Placeholder widget
        self.placeholder = Widget(size_hint_y=None, height=300)
        with self.placeholder.canvas:
            Color(0.2, 0.2, 0.2)
            Rectangle(pos=self.placeholder.pos, size=self.placeholder.size)
        self.placeholder.bind(pos=self.update_placeholder, size=self.update_placeholder)

    def on_video_load(self, instance):
        Logger.info(f"Video loaded successfully")
        if self.placeholder in self.children:
            self.remove_widget(self.placeholder)

    def on_video_error(self, instance, error):
        Logger.error(f"Failed to load video: {error}")
        if self.placeholder not in self.children:
            self.add_widget(self.placeholder, index=self.children.index(self.video))
        self.remove_widget(self.video)

    def update_placeholder(self, instance, value):
        instance.canvas.clear()
        with instance.canvas:
            Color(0.2, 0.2, 0.2)
            Rectangle(pos=instance.pos, size=instance.size)

class TrafficApp(App):
    def build(self):
        root = BoxLayout(orientation='horizontal', padding=10, spacing=10)
        
        # Lanes in a 2x2 grid
        lanes_grid = GridLayout(cols=2, spacing=10, size_hint_x=0.8)
        lanes_grid.add_widget(LaneWidget("Lane 1"))
        lanes_grid.add_widget(LaneWidget("Lane 2"))
        lanes_grid.add_widget(LaneWidget("Lane 3"))
        lanes_grid.add_widget(LaneWidget("Lane 4"))
        root.add_widget(lanes_grid)

        # Accident panel
        accident_panel = BoxLayout(orientation='vertical', size_hint_x=0.2)
        with accident_panel.canvas.before:
            Color(0, 0, 0, 1)  # Black background
            Rectangle(pos=accident_panel.pos, size=accident_panel.size)
        accident_label = Label(text="Accident", color=[1, 1, 1, 1])  # White text
        accident_panel.add_widget(accident_label)
        root.add_widget(accident_panel)

        return root

if __name__ == '__main__':
    TrafficApp().run()