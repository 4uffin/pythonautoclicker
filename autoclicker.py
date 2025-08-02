import tkinter as tk
from tkinter import ttk, messagebox
import threading
import time
import configparser
import random
from pynput.mouse import Button, Controller
from pynput.keyboard import Key, Listener, KeyCode

# --- Tooltip Class for enhanced GUI ---
class Tooltip:
    """
    Helper class to create tooltips for widgets.
    This provides a better user experience by giving context to each input field.
    """
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tooltip = None
        # Bind events to show and hide the tooltip
        self.widget.bind("<Enter>", self.show_tooltip)
        self.widget.bind("<Leave>", self.hide_tooltip)

    def show_tooltip(self, event=None):
        """Displays the tooltip near the widget."""
        x, y, _, _ = self.widget.bbox("insert")
        x += self.widget.winfo_rootx() + 25
        y += self.widget.winfo_rooty() + 25
        
        self.tooltip = tk.Toplevel(self.widget)
        # Removes window decorations (title bar, border)
        self.tooltip.wm_overrideredirect(True)
        self.tooltip.wm_geometry(f"+{x}+{y}")
        
        label = ttk.Label(self.tooltip, text=self.text, background="#ffffe0", relief="solid", borderwidth=1,
                         font=("Helvetica", 10, "normal"))
        label.pack(ipadx=1)

    def hide_tooltip(self, event=None):
        """Destroys the tooltip when the cursor leaves the widget."""
        if self.tooltip:
            self.tooltip.destroy()
        self.tooltip = None

# --- Main AutoClicker Class ---
class AutoClickerApp:
    """
    Main application class that encapsulates all GUI elements and
    the auto-clicking logic.
    """
    def __init__(self, master):
        self.master = master
        master.title("Python Auto Clicker")
        master.geometry("500x630")
        
        # Initialize the pynput mouse controller
        self.mouse = Controller()

        # State variables to manage the clicking loop and hotkeys
        self.clicking = False
        self.paused = False
        self.click_thread = None
        self.keyboard_listener = None
        
        # Default hotkeys
        self.start_stop_hotkey = Key.f6
        self.pick_location_hotkey = Key.f7
        self.pause_resume_hotkey = Key.f8
        self.picking_location_mode = False
        self.recording_hotkey_mode = None # 'start_stop', 'pick_location', 'pause_resume'
        
        # Default click settings
        self.picked_location = None
        self.start_stop_hotkey_str = 'F6'
        self.pick_location_hotkey_str = 'F7'
        self.pause_resume_hotkey_str = 'F8'
        self.interval_value = '1.0'
        self.interval_unit = 'seconds'
        self.click_type_value = 'single'
        self.mouse_button_value = 'left'
        self.location_value = 'current'
        self.repeat_value = 'infinite'
        self.repeat_count_value = '100'
        self.pre_start_delay_value = '0'
        self.random_interval_enabled = False
        self.random_interval_min = '0.1'
        self.random_interval_max = '0.5'
        
        # Theme setting
        self.theme = 'dark'
        self.colors = {}

        # Configuration file handler for saving/loading settings
        self.config = configparser.ConfigParser()
        self.config_file = 'auto_clicker_settings.cfg'

        # --- GUI Setup ---
        self.load_settings()
        self.create_widgets()
        self.setup_hotkey_listener()
        self.set_theme(self.theme)
        
    def load_settings(self):
        """Loads settings from a configuration file, if it exists."""
        self.config.read(self.config_file)
        if 'SETTINGS' in self.config:
            settings = self.config['SETTINGS']
            self.start_stop_hotkey_str = settings.get('start_stop_hotkey', 'F6')
            self.start_stop_hotkey = self.get_key_from_string(self.start_stop_hotkey_str)
            self.pick_location_hotkey_str = settings.get('pick_location_hotkey', 'F7')
            self.pick_location_hotkey = self.get_key_from_string(self.pick_location_hotkey_str)
            self.pause_resume_hotkey_str = settings.get('pause_resume_hotkey', 'F8')
            self.pause_resume_hotkey = self.get_key_from_string(self.pause_resume_hotkey_str)
            self.interval_value = settings.get('interval', '1.0')
            self.interval_unit = settings.get('interval_unit', 'seconds')
            self.click_type_value = settings.get('click_type', 'single')
            self.mouse_button_value = settings.get('mouse_button', 'left')
            self.location_value = settings.get('location', 'current')
            self.repeat_value = settings.get('repeat', 'infinite')
            self.repeat_count_value = settings.get('repeat_count', '100')
            self.pre_start_delay_value = settings.get('pre_start_delay', '0')
            self.random_interval_enabled = settings.getboolean('random_interval_enabled', False)
            self.random_interval_min = settings.get('random_interval_min', '0.1')
            self.random_interval_max = settings.get('random_interval_max', '0.5')
            self.theme = settings.get('theme', 'dark')
            if 'fixed_location_x' in settings and 'fixed_location_y' in settings:
                try:
                    x = int(settings['fixed_location_x'])
                    y = int(settings['fixed_location_y'])
                    self.picked_location = (x, y)
                except (ValueError, KeyError):
                    self.picked_location = None

    def save_settings(self):
        """Saves current settings to a configuration file."""
        if not self.config.has_section('SETTINGS'):
            self.config.add_section('SETTINGS')
        
        # Save all current settings from the GUI widgets
        self.config['SETTINGS']['start_stop_hotkey'] = self.start_stop_hotkey_str
        self.config['SETTINGS']['pick_location_hotkey'] = self.pick_location_hotkey_str
        self.config['SETTINGS']['pause_resume_hotkey'] = self.pause_resume_hotkey_str
        self.config['SETTINGS']['interval'] = self.interval_entry.get()
        self.config['SETTINGS']['interval_unit'] = self.interval_unit_var.get()
        self.config['SETTINGS']['click_type'] = self.click_type_var.get()
        self.config['SETTINGS']['mouse_button'] = self.mouse_button_var.get()
        self.config['SETTINGS']['location'] = self.location_var.get()
        self.config['SETTINGS']['repeat'] = self.repeat_var.get()
        self.config['SETTINGS']['repeat_count'] = self.repeat_count_entry.get()
        self.config['SETTINGS']['pre_start_delay'] = self.pre_start_delay_entry.get()
        self.config['SETTINGS']['random_interval_enabled'] = 'True' if self.random_interval_enabled_var.get() else 'False'
        self.config['SETTINGS']['random_interval_min'] = self.random_interval_min_entry.get()
        self.config['SETTINGS']['random_interval_max'] = self.random_interval_max_entry.get()
        self.config['SETTINGS']['theme'] = self.theme
        if self.picked_location:
            self.config['SETTINGS']['fixed_location_x'] = str(self.picked_location[0])
            self.config['SETTINGS']['fixed_location_y'] = str(self.picked_location[1])
        
        with open(self.config_file, 'w') as configfile:
            self.config.write(configfile)

    def set_theme(self, theme_name):
        """Applies the selected theme to all widgets for a consistent look."""
        self.theme = theme_name
        if self.theme == 'dark':
            self.colors = {
                'bg_primary': '#2c3e50', 'bg_secondary': '#34495e', 'fg_primary': '#ecf0f1',
                'fg_accent': '#f1c40f', 'button_bg_start': '#27ae60', 'button_bg_stop': '#c0392b',
                'button_active_start': '#2ecc71', 'button_active_stop': '#e74c3c',
                'button_record': '#3498db', 'button_active_record': '#2980b9'
            }
        else: # light theme
            self.colors = {
                'bg_primary': '#f0f0f0', 'bg_secondary': '#ffffff', 'fg_primary': '#333333',
                'fg_accent': '#00509d', 'button_bg_start': '#5cb85c', 'button_bg_stop': '#d9534f',
                'button_active_start': '#4cae4c', 'button_active_stop': '#c9302c',
                'button_record': '#337ab7', 'button_active_record': '#286090'
            }
        
        self.master.configure(bg=self.colors['bg_primary'])
        style = ttk.Style(self.master)
        style.theme_use('clam' if 'clam' in style.theme_names() else 'alt')
        
        # Configure styling for all ttk widgets
        style.configure('TFrame', background=self.colors['bg_secondary'])
        style.configure('TLabel', background=self.colors['bg_secondary'], foreground=self.colors['fg_primary'])
        style.configure('TNotebook', background=self.colors['bg_primary'])
        style.configure('TNotebook.Tab', background=self.colors['bg_secondary'], foreground=self.colors['fg_primary'])
        style.map('TNotebook.Tab', background=[('selected', self.colors['bg_primary'])])
        style.configure('TCheckbutton', background=self.colors['bg_secondary'], foreground=self.colors['fg_primary'])
        style.configure('TRadiobutton', background=self.colors['bg_secondary'], foreground=self.colors['fg_primary'])
        style.configure('TCombobox', fieldbackground=self.colors['bg_secondary'], foreground=self.colors['fg_primary'])
        style.configure('TEntry', fieldbackground=self.colors['bg_secondary'], foreground=self.colors['fg_primary'], insertcolor=self.colors['fg_primary'])
        style.configure('TButton', background=self.colors['button_record'], foreground=self.colors['fg_primary'])
        style.map('TButton', background=[('active', self.colors['button_active_record'])])
        
        # Apply theme to top-level widgets
        self.title_label.config(background=self.colors['bg_primary'], foreground=self.colors['fg_primary'])
        self.status_label.config(background=self.colors['bg_primary'], foreground=self.colors['fg_accent'])
        
        self.start_button.config(style='Start.TButton')
        self.stop_button.config(style='Stop.TButton')
        self.record_start_stop_hotkey_button.config(style='Record.TButton')
        self.record_pick_location_hotkey_button.config(style='Record.TButton')
        self.record_pause_resume_hotkey_button.config(style='Record.TButton')
        
        # Specific button styles for the main control buttons
        style.configure('Start.TButton', background=self.colors['button_bg_start'])
        style.map('Start.TButton', background=[('active', self.colors['button_active_start'])])
        style.configure('Stop.TButton', background=self.colors['button_bg_stop'])
        style.map('Stop.TButton', background=[('active', self.colors['button_active_stop'])])
        style.configure('Record.TButton', background=self.colors['button_record'])
        style.map('Record.TButton', background=[('active', self.colors['button_active_record'])])
        
        # The labels inside the ttk.Frames need to be styled manually since they are ttk.Labels
        for frame in [self.settings_frame, self.hotkeys_frame, self.appearance_frame, self.interval_frame, self.random_frame, self.delay_frame, self.click_type_frame, self.button_frame, self.location_frame, self.repeat_frame, self.hotkeys_container, self.start_stop_hotkey_frame, self.pick_location_hotkey_frame, self.pause_resume_hotkey_frame, self.appearance_container]:
            for child in frame.winfo_children():
                if isinstance(child, ttk.Label):
                    child.config(background=self.colors['bg_secondary'], foreground=self.colors['fg_primary'])
        
        # Update the theme toggle button's text
        if self.theme == 'light':
            self.theme_toggle_var.set('light')
            self.theme_toggle.config(text="Dark Mode")
        else:
            self.theme_toggle_var.set('dark')
            self.theme_toggle.config(text="Light Mode")

    def toggle_theme(self):
        """Switches between light and dark themes."""
        self.set_theme('light' if self.theme == 'dark' else 'dark')

    def create_widgets(self):
        """Builds all the GUI elements for the application."""
        
        self.title_label = ttk.Label(self.master, text="Python Auto Clicker", font=("Helvetica", 24, "bold"))
        self.title_label.pack(pady=(20, 10))

        self.notebook = ttk.Notebook(self.master)
        self.notebook.pack(pady=10, padx=20, expand=True, fill="both")
        
        # Tabs for settings, hotkeys, and appearance
        self.settings_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.settings_frame, text='Settings')
        self.hotkeys_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.hotkeys_frame, text='Hotkeys')
        self.appearance_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.appearance_frame, text='Appearance')

        # --- Settings Tab Widgets ---
        self.interval_frame = ttk.Frame(self.settings_frame)
        self.interval_frame.pack(fill="x", pady=5, padx=5)
        ttk.Label(self.interval_frame, text="Click Speed:", font=("Helvetica", 12)).pack(side="left")
        self.interval_entry = ttk.Entry(self.interval_frame, width=10, font=("Helvetica", 12))
        self.interval_entry.insert(0, self.interval_value)
        self.interval_entry.pack(side="left", padx=(5, 0))
        Tooltip(self.interval_entry, "Enter the numeric value for the click speed.")
        
        self.interval_unit_var = tk.StringVar(value=self.interval_unit)
        self.interval_unit_dropdown = ttk.Combobox(self.interval_frame, textvariable=self.interval_unit_var, font=("Helvetica", 12), state='readonly', values=['seconds', 'ms', 'CPS', 'CPM'])
        self.interval_unit_dropdown.pack(side="left", padx=(5, 0))
        Tooltip(self.interval_unit_dropdown, "Select the unit for the click speed.")

        self.random_interval_enabled_var = tk.BooleanVar(value=self.random_interval_enabled)
        random_check = ttk.Checkbutton(self.settings_frame, text="Random Interval", variable=self.random_interval_enabled_var)
        random_check.pack(anchor="w", pady=(10, 0), padx=5)
        Tooltip(random_check, "Enable a random delay between clicks to mimic human behavior.")
        
        self.random_frame = ttk.Frame(self.settings_frame)
        self.random_frame.pack(fill="x", pady=5, padx=5)
        ttk.Label(self.random_frame, text="Min Delay (s):", font=("Helvetica", 12)).pack(side="left")
        self.random_interval_min_entry = ttk.Entry(self.random_frame, width=8, font=("Helvetica", 12))
        self.random_interval_min_entry.insert(0, self.random_interval_min)
        self.random_interval_min_entry.pack(side="left", padx=5)
        Tooltip(self.random_interval_min_entry, "Minimum random delay in seconds.")
        ttk.Label(self.random_frame, text="Max Delay (s):", font=("Helvetica", 12)).pack(side="left")
        self.random_interval_max_entry = ttk.Entry(self.random_frame, width=8, font=("Helvetica", 12))
        self.random_interval_max_entry.insert(0, self.random_interval_max)
        self.random_interval_max_entry.pack(side="left", padx=5)
        Tooltip(self.random_interval_max_entry, "Maximum random delay in seconds.")

        self.delay_frame = ttk.Frame(self.settings_frame)
        self.delay_frame.pack(fill="x", pady=5, padx=5)
        ttk.Label(self.delay_frame, text="Pre-start Delay (seconds):", font=("Helvetica", 12)).pack(side="left")
        self.pre_start_delay_entry = ttk.Entry(self.delay_frame, width=10, font=("Helvetica", 12))
        self.pre_start_delay_entry.insert(0, self.pre_start_delay_value)
        self.pre_start_delay_entry.pack(side="right")
        Tooltip(self.pre_start_delay_entry, "Delay before clicking starts to let you move the cursor.")
        
        self.click_type_frame = ttk.Frame(self.settings_frame)
        self.click_type_frame.pack(fill="x", pady=5, padx=5)
        ttk.Label(self.click_type_frame, text="Click Type:", font=("Helvetica", 12)).pack(side="left")
        self.click_type_var = tk.StringVar(value=self.click_type_value)
        ttk.Radiobutton(self.click_type_frame, text="Single", variable=self.click_type_var, value="single").pack(side="left", padx=5)
        ttk.Radiobutton(self.click_type_frame, text="Double", variable=self.click_type_var, value="double").pack(side="left", padx=5)

        self.button_frame = ttk.Frame(self.settings_frame)
        self.button_frame.pack(fill="x", pady=5, padx=5)
        ttk.Label(self.button_frame, text="Mouse Button:", font=("Helvetica", 12)).pack(side="left")
        self.mouse_button_var = tk.StringVar(value=self.mouse_button_value)
        ttk.Radiobutton(self.button_frame, text="Left", variable=self.mouse_button_var, value="left").pack(side="left", padx=5)
        ttk.Radiobutton(self.button_frame, text="Right", variable=self.mouse_button_var, value="right").pack(side="left", padx=5)
        
        self.location_frame = ttk.Frame(self.settings_frame)
        self.location_frame.pack(fill="x", pady=5, padx=5)
        ttk.Label(self.location_frame, text="Click Location:", font=("Helvetica", 12)).pack(side="left")
        self.location_var = tk.StringVar(value=self.location_value)
        ttk.Radiobutton(self.location_frame, text="Current", variable=self.location_var, value="current").pack(side="left", padx=5)
        ttk.Radiobutton(self.location_frame, text="Fixed", variable=self.location_var, value="fixed").pack(side="left", padx=5)
        self.location_display_label = ttk.Label(self.location_frame, text=f" ({self.picked_location[0]}, {self.picked_location[1]})" if self.picked_location else " (Not set)", font=("Helvetica", 10, "italic"))
        self.location_display_label.pack(side="left")
        Tooltip(self.location_display_label, "The coordinates of the fixed location to click.")
        
        self.repeat_frame = ttk.Frame(self.settings_frame)
        self.repeat_frame.pack(fill="x", pady=5, padx=5)
        ttk.Label(self.repeat_frame, text="Repeat:", font=("Helvetica", 12)).pack(side="left")
        self.repeat_var = tk.StringVar(value=self.repeat_value)
        ttk.Radiobutton(self.repeat_frame, text="Infinite", variable=self.repeat_var, value="infinite").pack(side="left", padx=5)
        ttk.Radiobutton(self.repeat_frame, text="Count:", variable=self.repeat_var, value="count").pack(side="left", padx=5)
        self.repeat_count_entry = ttk.Entry(self.repeat_frame, width=10, font=("Helvetica", 12))
        self.repeat_count_entry.insert(0, self.repeat_count_value)
        self.repeat_count_entry.pack(side="left")
        Tooltip(self.repeat_count_entry, "The number of times to click before stopping.")
        
        # --- Hotkeys Tab Widgets ---
        self.hotkeys_container = ttk.Frame(self.hotkeys_frame)
        self.hotkeys_container.pack(fill='both', expand=True, padx=10, pady=10)

        # Start/Stop Hotkey section
        self.start_stop_hotkey_frame = ttk.Frame(self.hotkeys_container)
        self.start_stop_hotkey_frame.pack(fill="x", pady=5)
        ttk.Label(self.start_stop_hotkey_frame, text="Start/Stop Hotkey:", font=("Helvetica", 12)).pack(side="left")
        self.start_stop_hotkey_label = ttk.Label(self.start_stop_hotkey_frame, text=self.start_stop_hotkey_str, font=("Helvetica", 12, "bold"))
        self.start_stop_hotkey_label.pack(side="left", padx=5)
        self.record_start_stop_hotkey_button = ttk.Button(self.start_stop_hotkey_frame, text="Record Hotkey", command=lambda: self.record_hotkey(hotkey_type='start_stop'))
        self.record_start_stop_hotkey_button.pack(side="right", padx=5)

        # Pick Location Hotkey section
        self.pick_location_hotkey_frame = ttk.Frame(self.hotkeys_container)
        self.pick_location_hotkey_frame.pack(fill="x", pady=5)
        ttk.Label(self.pick_location_hotkey_frame, text="Pick Location Hotkey:", font=("Helvetica", 12)).pack(side="left")
        self.pick_location_hotkey_label = ttk.Label(self.pick_location_hotkey_frame, text=self.pick_location_hotkey_str, font=("Helvetica", 12, "bold"))
        self.pick_location_hotkey_label.pack(side="left", padx=5)
        self.record_pick_location_hotkey_button = ttk.Button(self.pick_location_hotkey_frame, text="Record Hotkey", command=lambda: self.record_hotkey(hotkey_type='pick_location'))
        self.record_pick_location_hotkey_button.pack(side="right", padx=5)

        # Pause/Resume Hotkey section
        self.pause_resume_hotkey_frame = ttk.Frame(self.hotkeys_container)
        self.pause_resume_hotkey_frame.pack(fill="x", pady=5)
        ttk.Label(self.pause_resume_hotkey_frame, text="Pause/Resume Hotkey:", font=("Helvetica", 12)).pack(side="left")
        self.pause_resume_hotkey_label = ttk.Label(self.pause_resume_hotkey_frame, text=self.pause_resume_hotkey_str, font=("Helvetica", 12, "bold"))
        self.pause_resume_hotkey_label.pack(side="left", padx=5)
        self.record_pause_resume_hotkey_button = ttk.Button(self.pause_resume_hotkey_frame, text="Record Hotkey", command=lambda: self.record_hotkey(hotkey_type='pause_resume'))
        self.record_pause_resume_hotkey_button.pack(side="right", padx=5)
        
        # --- Appearance Tab Widgets ---
        self.appearance_container = ttk.Frame(self.appearance_frame)
        self.appearance_container.pack(fill='both', expand=True, padx=10, pady=10)
        
        self.theme_toggle_var = tk.StringVar(value=self.theme)
        self.theme_toggle = ttk.Checkbutton(self.appearance_container, text="Light Mode", variable=self.theme_toggle_var, onvalue='light', offvalue='dark', command=self.toggle_theme)
        self.theme_toggle.pack(anchor="w", pady=5, padx=5)

        # Status Label for real-time feedback
        self.status_label = ttk.Label(self.master, text=f"Status: Ready (Hotkey: {self.start_stop_hotkey_str})", font=("Helvetica", 12, "italic"))
        self.status_label.pack(pady=10)

        # Control Buttons
        self.control_frame = ttk.Frame(self.master)
        self.control_frame.pack(pady=10)
        self.start_button = ttk.Button(self.control_frame, text="Start Clicking", command=self.start_clicking_wrapper, style='Start.TButton')
        self.start_button.pack(side="left", padx=10, ipady=5)
        self.stop_button = ttk.Button(self.control_frame, text="Stop Clicking", command=self.stop_clicking, style='Stop.TButton', state=tk.DISABLED)
        self.stop_button.pack(side="left", padx=10, ipady=5)
        
    def get_key_from_string(self, key_str):
        """
        Helper to convert a string representation of a key (e.g., 'F6')
        to a pynput Key or KeyCode object.
        """
        if not key_str: return None
        try:
            return Key[key_str.lower()]
        except KeyError:
            try:
                # Handle single characters
                return KeyCode.from_char(key_str.lower())
            except (KeyError, AttributeError):
                return None
    
    def setup_hotkey_listener(self):
        """Initializes the keyboard listener to detect hotkey presses."""
        if self.keyboard_listener and self.keyboard_listener.is_alive():
            self.keyboard_listener.stop()
        self.keyboard_listener = Listener(on_press=self.on_key_press)
        self.keyboard_listener.start()
    
    def record_hotkey(self, hotkey_type):
        """Starts a temporary keyboard listener to capture the next key press as a new hotkey."""
        if self.recording_hotkey_mode: return
        
        self.recording_hotkey_mode = hotkey_type
        # Reset colors of all hotkey labels before highlighting the active one
        self.start_stop_hotkey_label.config(foreground=self.colors['fg_primary'])
        self.pick_location_hotkey_label.config(foreground=self.colors['fg_primary'])
        self.pause_resume_hotkey_label.config(foreground=self.colors['fg_primary'])

        if hotkey_type == 'start_stop':
            self.status_label.config(text="Status: Press a key for Start/Stop hotkey...", foreground=self.colors['fg_accent'])
            self.start_stop_hotkey_label.config(foreground=self.colors['fg_accent'])
        elif hotkey_type == 'pick_location':
            self.status_label.config(text="Status: Press a key for Pick Location hotkey...", foreground=self.colors['fg_accent'])
            self.pick_location_hotkey_label.config(foreground=self.colors['fg_accent'])
        else: # pause_resume
            self.status_label.config(text="Status: Press a key for Pause/Resume hotkey...", foreground=self.colors['fg_accent'])
            self.pause_resume_hotkey_label.config(foreground=self.colors['fg_accent'])

        def on_key_capture(key):
            """Callback function to capture the key press."""
            try:
                key_name = key.name if hasattr(key, 'name') else key.char.upper()
                if self.recording_hotkey_mode == 'start_stop':
                    self.start_stop_hotkey_str = key_name
                    self.start_stop_hotkey = key
                    self.start_stop_hotkey_label.config(text=self.start_stop_hotkey_str)
                elif self.recording_hotkey_mode == 'pick_location':
                    self.pick_location_hotkey_str = key_name
                    self.pick_location_hotkey = key
                    self.pick_location_hotkey_label.config(text=self.pick_location_hotkey_str)
                else:
                    self.pause_resume_hotkey_str = key_name
                    self.pause_resume_hotkey = key
                    self.pause_resume_hotkey_label.config(text=self.pause_resume_hotkey_str)
                self.status_label.config(text=f"Status: Hotkey set to {key_name}", foreground=self.colors['fg_accent'])
            except (AttributeError, KeyError):
                self.status_label.config(text="Status: Invalid key.", foreground=self.colors['fg_accent'])
            
            self.recording_hotkey_mode = None
            self.set_theme(self.theme) # Re-apply theme to reset colors
            return False # Stop the listener after the first key press
        
        temp_listener = Listener(on_press=on_key_capture)
        temp_listener.start()

    def on_key_press(self, key):
        """Callback for the main keyboard listener to detect hotkeys."""
        # Ignore key presses if the app is in a special mode
        if self.recording_hotkey_mode or self.picking_location_mode:
            return
        
        if key == self.start_stop_hotkey:
            if not self.clicking:
                self.start_clicking_wrapper()
            else:
                self.stop_clicking()
        elif key == self.pick_location_hotkey:
            self.pick_location()
        elif key == self.pause_resume_hotkey and self.clicking:
            self.toggle_pause()
    
    def toggle_pause(self):
        """Toggles the paused state of the clicking loop."""
        self.paused = not self.paused
        if self.paused:
            self.status_label.config(text=f"Status: Paused (Hotkey: {self.pause_resume_hotkey_str})", foreground=self.colors['fg_accent'])
        else:
            self.status_label.config(text=f"Status: Resuming... (Hotkey: {self.start_stop_hotkey_str})", foreground=self.colors['fg_accent'])
    
    def pick_location(self):
        """Starts a temporary mouse listener to capture the click position."""
        if self.picking_location_mode:
            return

        self.picking_location_mode = True
        self.status_label.config(text="Status: Click on the desired fixed location...", foreground=self.colors['fg_accent'])
        
        def on_click(x, y, button, pressed):
            """Callback for the mouse click to save the coordinates."""
            if pressed:
                self.picked_location = (x, y)
                self.location_display_label.config(text=f" ({self.picked_location[0]}, {self.picked_location[1]})")
                self.status_label.config(text="Status: Fixed location saved.", foreground=self.colors['fg_accent'])
                self.picking_location_mode = False
                return False # Stop the listener
        
        temp_listener = Listener(on_click=on_click)
        temp_listener.start()

    def get_click_interval(self):
        """Calculates the click interval in seconds based on user input and unit."""
        try:
            value_str = self.interval_entry.get()
            if not value_str:
                raise ValueError("Click speed value cannot be empty.")
            value = float(value_str)
            unit = self.interval_unit_var.get()
            if value <= 0: raise ValueError("Click speed value must be a positive number.")
            
            if unit == 'seconds':
                return value
            elif unit == 'ms':
                return value / 1000.0
            elif unit == 'cps':
                return 1.0 / value
            elif unit == 'cpm':
                return 60.0 / value
        except ValueError as e:
            messagebox.showerror("Error", f"Invalid click speed: {e}")
            return None

    def clicking_loop(self, interval, button, click_type, repeat_count, fixed_position, pre_start_delay, random_enabled, random_min, random_max):
        """
        The main loop that runs in a separate thread to perform the clicks.
        This is where the clicking magic happens.
        """
        # Initial delay before starting to click
        if pre_start_delay > 0:
            self.status_label.config(text=f"Status: Starting in {pre_start_delay}s...", foreground=self.colors['fg_accent'])
            time.sleep(pre_start_delay)

        self.status_label.config(text=f"Status: Clicking... (Hotkey: {self.start_stop_hotkey_str})", foreground=self.colors['fg_accent'])
        clicks_done = 0
        start_time = time.time()
        
        while self.clicking:
            # Check for pause state
            while self.paused:
                time.sleep(0.1)
                
            if repeat_count is not None and clicks_done >= repeat_count:
                break
                
            if fixed_position:
                self.mouse.position = fixed_position
                
            if click_type == "single":
                self.mouse.click(button)
            elif click_type == "double":
                # Correct way to perform a double-click with pynput
                self.mouse.click(button, 2)
                
            clicks_done += 1
            
            # Update the clicks per second (CPS) in the status bar
            elapsed_time = time.time() - start_time
            if elapsed_time > 0 and clicks_done % 10 == 0:
                cps = clicks_done / elapsed_time
                self.master.after(0, lambda: self.status_label.config(text=f"Status: Clicking... (~{cps:.2f} CPS)", foreground=self.colors['fg_accent']))
            
            # Determine the sleep time based on user settings
            if random_enabled:
                sleep_time = random.uniform(random_min, random_max)
            else:
                sleep_time = interval
            
            time.sleep(sleep_time)
        
        # Stop the loop and update the GUI
        self.clicking = False
        self.master.after(0, self.update_gui_after_stop)

    def update_gui_after_stop(self):
        """Updates the GUI state after the clicking thread has stopped."""
        self.status_label.config(text=f"Status: Stopped. (Hotkey: {self.start_stop_hotkey_str})", foreground=self.colors['fg_accent'])
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)

    def start_clicking_wrapper(self):
        """Starts the auto-clicking process in a new thread after validation."""
        self.save_settings()
        try:
            # Validate all user inputs before starting the thread
            interval = self.get_click_interval()
            if interval is None: return
            
            pre_start_delay_str = self.pre_start_delay_entry.get()
            if not pre_start_delay_str: raise ValueError("Pre-start delay cannot be empty.")
            pre_start_delay = float(pre_start_delay_str)
            if pre_start_delay < 0: raise ValueError("Pre-start delay cannot be negative.")

            random_enabled = self.random_interval_enabled_var.get()
            random_min, random_max = 0, 0
            if random_enabled:
                random_min_str = self.random_interval_min_entry.get()
                random_max_str = self.random_interval_max_entry.get()
                if not random_min_str or not random_max_str:
                    raise ValueError("Random interval values cannot be empty.")
                random_min = float(random_min_str)
                random_max = float(random_max_str)
                if random_min <= 0 or random_max <= 0 or random_min > random_max:
                    raise ValueError("Invalid random interval range.")

            mouse_button_name = self.mouse_button_var.get()
            button = Button.left if mouse_button_name == "left" else Button.right
            click_type = self.click_type_var.get()
            
            fixed_position = None
            if self.location_var.get() == "fixed":
                if self.picked_location is None:
                    messagebox.showerror("Error", "Please pick a fixed location first.")
                    return
                fixed_position = self.picked_location
            
            repeat_count = None
            if self.repeat_var.get() == "count":
                repeat_count_str = self.repeat_count_entry.get()
                if not repeat_count_str: raise ValueError("Repeat count cannot be empty.")
                repeat_count = int(repeat_count_str)
                if repeat_count <= 0: raise ValueError("Repeat count must be a positive integer.")
            
            # Start the clicking thread
            if not self.clicking:
                self.clicking = True
                self.paused = False
                self.click_thread = threading.Thread(target=self.clicking_loop, args=(interval, button, click_type, repeat_count, fixed_position, pre_start_delay, random_enabled, random_min, random_max), daemon=True)
                self.click_thread.start()
                self.start_button.config(state=tk.DISABLED)
                self.stop_button.config(state=tk.NORMAL)
                self.status_label.config(text=f"Status: Starting... (Hotkey: {self.start_stop_hotkey_str})", foreground=self.colors['fg_accent'])
        except ValueError as e:
            messagebox.showerror("Error", f"Invalid input: {e}")
            self.status_label.config(text=f"Status: Ready (Hotkey: {self.start_stop_hotkey_str})", foreground=self.colors['fg_accent'])

    def stop_clicking(self):
        """Stops the auto-clicking process."""
        if self.clicking:
            self.clicking = False
            self.paused = False
            # Wait for the thread to finish if it's still running
            if self.click_thread and self.click_thread.is_alive():
                self.click_thread.join(timeout=1)
            self.update_gui_after_stop()

    def on_close(self):
        """Handles cleanup when the main window is closed."""
        self.save_settings()
        self.clicking = False
        self.paused = False
        if self.keyboard_listener and self.keyboard_listener.is_alive():
            self.keyboard_listener.stop()
        if self.click_thread and self.click_thread.is_alive():
            self.click_thread.join(timeout=1)
        self.master.destroy()

# --- Application Entry Point ---
if __name__ == "__main__":
    root = tk.Tk()
    app = AutoClickerApp(root)
    # Ensure cleanup on window close
    root.protocol("WM_DELETE_WINDOW", app.on_close)
    root.mainloop()