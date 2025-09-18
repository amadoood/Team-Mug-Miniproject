"""
Hardware abstraction layer for PWM audio output on Raspberry Pi Pico
Drives a piezo buzzer connected to a GPIO pin
"""
from machine import Pin, PWM
import time

class PWMAudio:
    """PWM audio driver for piezo buzzer"""
    
    def __init__(self, pin_num=15, max_freq=5000):
        """
        Initialize PWM audio driver
        
        Args:
            pin_num (int): GPIO pin number for audio output (default: GP15)
            max_freq (int): Maximum frequency in Hz (default: 5000)
        """
        self.pin = Pin(pin_num, Pin.OUT)
        self.pwm = PWM(self.pin)
        self.max_freq = max_freq
        self.current_freq = 0
        self.active = False
        
        # Initialize to silent state
        self.stop()
        
    def set_freq(self, frequency):
        """
        Set PWM frequency for audio output
        
        Args:
            frequency (float): Frequency in Hz
        """
        if frequency <= 0:
            self.stop()
            return
            
        # Clamp frequency to reasonable range for piezo buzzer
        freq = max(50, min(int(frequency), self.max_freq))
        
        try:
            self.pwm.freq(freq)
            self.current_freq = freq
            if not self.active:
                self.pwm.duty_u16(0)  # Start silent
                self.active = True
        except Exception as e:
            print(f"PWM freq error: {e}")
            self.stop()
    
    def set_duty(self, duty_cycle):
        """
        Set PWM duty cycle (volume)
        
        Args:
            duty_cycle (float): Duty cycle 0.0-1.0 (0=silent, 1=maximum)
        """
        if not self.active or duty_cycle <= 0:
            if self.active:
                self.pwm.duty_u16(0)
            return
            
        # Convert 0.0-1.0 to 16-bit duty value
        # Use square wave (50% max) for better piezo buzzer sound
        duty_16bit = int(min(duty_cycle, 1.0) * 32768)  # Max 50% duty cycle
        
        try:
            self.pwm.duty_u16(duty_16bit)
        except Exception as e:
            print(f"PWM duty error: {e}")
            self.stop()
    
    def stop(self):
        """Stop PWM output and silence buzzer"""
        try:
            self.pwm.duty_u16(0)
            self.current_freq = 0
            self.active = False
        except Exception as e:
            print(f"PWM stop error: {e}")
    
    def deinit(self):
        """Cleanup PWM resources"""
        self.stop()
        try:
            self.pwm.deinit()
        except Exception:
            pass
