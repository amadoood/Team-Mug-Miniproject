"""
Light sensor interface for Raspberry Pi Pico
Reads analog light values and converts to usable intensity data
"""
from machine import ADC, Pin
import time

class LightSensor:
    """
    Light sensor driver using ADC input
    Can work with photoresistor, LDR, or phototransistor
    """
    
    def __init__(self, adc_pin=28, *, voltage_ref=3.3, samples=10):
        """
        Initialize light sensor
        
        Args:
            adc_pin (int): ADC pin number (26, 27, 28 on Pico)
            voltage_ref (float): Reference voltage (default: 3.3V)
            samples (int): Number of samples to average (default: 10)
        """
        self.adc = ADC(Pin(adc_pin))
        self.voltage_ref = voltage_ref
        self.samples = samples
        
        # Calibration values (to be tuned based on sensor and lighting conditions)
        self.min_reading = 100    # Minimum expected ADC value (dark)
        self.max_reading = 65535  # Maximum expected ADC value (bright)
        
        # Running average filter
        self.reading_history = []
        self.history_size = 5
        
    def read_raw(self):
        """
        Read raw ADC value
        
        Returns:
            int: Raw 16-bit ADC value (0-65535)
        """
        # Take multiple samples and average
        total = 0
        for _ in range(self.samples):
            total += self.adc.read_u16()
            time.sleep_ms(1)  # Small delay between samples
            
        return total // self.samples
    
    def read_voltage(self):
        """
        Read sensor voltage
        
        Returns:
            float: Voltage value (0.0 to voltage_ref)
        """
        raw = self.read_raw()
        return (raw / 65535.0) * self.voltage_ref
    
    def read_intensity(self):
        """
        Read light intensity as percentage
        
        Returns:
            float: Light intensity 0.0-100.0 (0=dark, 100=bright)
        """
        raw = self.read_raw()
        
        # Apply running average filter
        self.reading_history.append(raw)
        if len(self.reading_history) > self.history_size:
            self.reading_history.pop(0)
        
        # Calculate filtered average
        filtered_raw = sum(self.reading_history) // len(self.reading_history)
        
        # Map to 0-100 range with calibrated min/max
        clamped = max(self.min_reading, min(filtered_raw, self.max_reading))
        intensity = ((clamped - self.min_reading) / 
                    (self.max_reading - self.min_reading)) * 100.0
        
        return max(0.0, min(100.0, intensity))
    
    def calibrate(self, dark_samples=20, bright_samples=20):
        """
        Auto-calibrate sensor based on current lighting conditions
        
        Args:
            dark_samples (int): Number of samples to take for dark calibration
            bright_samples (int): Number of samples for bright calibration
        """
        print("Calibrating light sensor...")
        
        print("Cover sensor for dark calibration...")
        time.sleep(3)  # Give user time to cover sensor
        
        # Sample dark condition
        dark_readings = []
        for i in range(dark_samples):
            dark_readings.append(self.read_raw())
            time.sleep_ms(100)
            if i % 5 == 0:
                print(f"Dark sample {i+1}/{dark_samples}")
        
        self.min_reading = sum(dark_readings) // len(dark_readings)
        
        print("Expose sensor to bright light...")
        time.sleep(3)  # Give user time to expose sensor
        
        # Sample bright condition  
        bright_readings = []
        for i in range(bright_samples):
            bright_readings.append(self.read_raw())
            time.sleep_ms(100)
            if i % 5 == 0:
                print(f"Bright sample {i+1}/{bright_samples}")
        
        self.max_reading = sum(bright_readings) // len(bright_readings)
        
        print(f"Calibration complete:")
        print(f"  Dark level: {self.min_reading}")
        print(f"  Bright level: {self.max_reading}")
        print(f"  Range: {self.max_reading - self.min_reading}")
    
    def get_debug_info(self):
        """
        Get debug information about sensor readings
        
        Returns:
            dict: Debug information including raw, voltage, and intensity
        """
        raw = self.read_raw()
        voltage = self.read_voltage()
        intensity = self.read_intensity()
        
        return {
            "raw": raw,
            "voltage": round(voltage, 3),
            "intensity": round(intensity, 1),
            "min_cal": self.min_reading,
            "max_cal": self.max_reading
        }
