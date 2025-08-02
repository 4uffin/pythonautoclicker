# **Python Auto Clicker**

A powerful and easy-to-use auto-clicker application built with Python and Tkinter. This tool allows you to automate mouse clicks with a variety of customizable settings, including adjustable speed, click type, and hotkey controls. The application is inspired by the popular **OP Auto Clicker**.

## **Features**

* **Configurable Click Speed**: Set your desired click rate in seconds, milliseconds, Clicks Per Second (CPS), or Clicks Per Minute (CPM).  
* **Randomized Intervals**: Mimic human behavior by enabling a random delay between clicks within a specified range.  
* **Mouse Button & Click Type**: Choose between single or double clicks and select the left or right mouse button.  
* **Fixed Location Clicks**: Pick a specific location on the screen to perform all clicks, or use the cursor's current position.  
* **Hotkey Support**: Control the application with global hotkeys to start/stop, pause/resume, or pick a fixed location without interacting with the GUI.  
* **Persistent Settings**: All your preferences are saved automatically to a configuration file (auto\_clicker\_settings.cfg) and loaded on startup.  
* **Customizable Themes**: Toggle between a **Dark** and **Light** theme for a comfortable user experience.  
* **Real-time Status Updates**: The application provides live feedback on its current status, including the approximate CPS when clicking.

## **Installation**

This application requires Python 3 and a few external libraries.

### **Prerequisites**

* Python 3.6+  
* pynput library for mouse and keyboard control.  
* tkinter (usually included with Python installations).

### **Steps**

1. Clone the repository or download the autoclicker.py file.  
2. Install the required pynput library using pip:  
   pip install pynput

3. Run the application from your terminal:  
   python3 autoclicker.py

## **Usage**

### **Settings Tab**

* **Click Speed**: Enter a numeric value and select a unit from the dropdown menu.  
* **Random Interval**: Check the box to enable random delays, then set the minimum and maximum delay in seconds.  
* **Pre-start Delay**: Set a delay (in seconds) to give yourself time to position the cursor before the clicking begins.  
* **Click Type**: Choose between a "Single" or "Double" click.  
* **Mouse Button**: Select the "Left" or "Right" button.  
* **Click Location**: Choose "Current" to click wherever your cursor is, or "Fixed" to click at a saved location.  
* **Repeat**: Set the click action to run "Infinite" times or a specific "Count".

### **Hotkeys Tab**

Use the "Record Hotkey" buttons to assign a new hotkey to each function. Simply click the button and press the key you want to use.

* **Start/Stop Hotkey**: Toggles the clicking process on and off.  
* **Pick Location Hotkey**: Captures the mouse cursor's current position for a fixed-location click.  
* **Pause/Resume Hotkey**: Temporarily pauses or resumes the clicking loop.

## **Configuration**

The application automatically saves your settings to a file named auto\_clicker\_settings.cfg in the same directory as the script. You can manually edit this file to pre-configure your settings if needed.

\[SETTINGS\]  
start\_stop\_hotkey \= F6  
pick\_location\_hotkey \= F7  
pause\_resume\_hotkey \= F8  
interval \= 1.0  
interval\_unit \= seconds  
click\_type \= single  
mouse\_button \= left  
location \= current  
repeat \= infinite  
repeat\_count \= 100  
pre\_start\_delay \= 0  
random\_interval\_enabled \= False  
random\_interval\_min \= 0.1  
random\_interval\_max \= 0.5  
theme \= dark

