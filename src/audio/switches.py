"""
Tactile switch interface for user controls
Handles button presses with debouncing and event detection
"""
from machine import Pin
import time

class TactileSwitch:
    """
    Individual tactile switch with debouncing
    """
    
    def __init__(self, pin_num, *, pull_up=True, debounce_ms=50):
        """
        Initialize tactile switch
        
        Args:
            pin_num (int): GPIO pin number
            pull_up (bool): Use internal pull-up resistor (default: True)
            debounce_ms (int): Debounce time in milliseconds (default: 50)
        """
        self.pin = Pin(pin_num, Pin.IN, Pin.PULL_UP if pull_up else None)
        self.debounce_ms = debounce_ms
        self.pull_up = pull_up
        
        # State tracking
        self.last_state = self.pin.value()
        self.current_state = self.last_state
        self.last_change_time = time.ticks_ms()
        
        # Event flags
        self.pressed = False
        self.released = False
        self.held = False
        self.hold_threshold_ms = 1000  # 1 second for long press
        self.press_start_time = 0
        
    def update(self):
        """
        Update switch state and detect events
        Must be called regularly (every few ms) in main loop
        """
        now = time.ticks_ms()
        raw_state = self.pin.value()
        
        # Active low for pull-up configuration
        active_state = 0 if self.pull_up else 1
        
        # Reset event flags
        self.pressed = False
        self.released = False
        
        # Debouncing
        if raw_state != self.last_state:
            self.last_change_time = now
            self.last_state = raw_state
        
        # Update current state after debounce period
        if time.ticks_diff(now, self.last_change_time) >= self.debounce_ms:
            if raw_state != self.current_state:
                # State changed after debounce
                if raw_state == active_state:
                    # Button pressed
                    self.pressed = True
                    self.press_start_time = now
                    self.held = False
                else:
                    # Button released
                    self.released = True
                    self.held = False
                
                self.current_state = raw_state
        
        # Check for held state
        if self.current_state == active_state and not self.held:
            if time.ticks_diff(now, self.press_start_time) >= self.hold_threshold_ms:
                self.held = True
    
    def is_pressed(self):
        """Check if button is currently pressed"""
        active_state = 0 if self.pull_up else 1
        return self.current_state == active_state
    
    def was_pressed(self):
        """Check if button was just pressed this update cycle"""
        return self.pressed
    
    def was_released(self):
        """Check if button was just released this update cycle"""
        return self.released
    
    def is_held(self):
        """Check if button is being held (long press)"""
        return self.held

class SwitchController:
    """
    Controller for multiple tactile switches
    """
    
    def __init__(self, switch_pins):
        """
        Initialize switch controller
        
        Args:
            switch_pins (list): List of GPIO pin numbers for switches
        """
        self.switches = {}
        
        for i, pin_num in enumerate(switch_pins):
            switch_name = f"sw_{i+1}"
            self.switches[switch_name] = TactileSwitch(pin_num)
    
    def update(self):
        """Update all switches"""
        for switch in self.switches.values():
            switch.update()
    
    def get_switch(self, name):
        """
        Get switch by name
        
        Args:
            name (str): Switch name (e.g., 'sw_1', 'sw_2')
            
        Returns:
            TactileSwitch: Switch object or None if not found
        """
        return self.switches.get(name)
    
    def any_pressed(self):
        """Check if any switch was just pressed"""
        return any(sw.was_pressed() for sw in self.switches.values())
    
    def any_released(self):
        """Check if any switch was just released"""
        return any(sw.was_released() for sw in self.switches.values())
    
    def get_pressed_switches(self):
        """
        Get list of currently pressed switches
        
        Returns:
            list: Names of pressed switches
        """
        return [name for name, sw in self.switches.items() if sw.is_pressed()]
    
    def get_events(self):
        """
        Get all switch events this update cycle
        
        Returns:
            dict: Dictionary with event information
        """
        events = {
            'pressed': [],
            'released': [],
            'held': [],
            'active': []
        }
        
        for name, switch in self.switches.items():
            if switch.was_pressed():
                events['pressed'].append(name)
            if switch.was_released():
                events['released'].append(name)
            if switch.is_held():
                events['held'].append(name)
            if switch.is_pressed():
                events['active'].append(name)
        
        return events
