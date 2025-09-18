"""
Light to note mapping system for Light Orchestra
Converts light intensity values to musical notes and parameters
"""
import math

class LightToNoteMapper:
    """
    Maps light intensity to musical notes with configurable scales and ranges
    """
    
    def __init__(self, *, min_note=36, max_note=84, scale="chromatic"):
        """
        Initialize light to note mapper
        
        Args:
            min_note (int): Minimum MIDI note (default: 36, C2)
            max_note (int): Maximum MIDI note (default: 84, C6) 
            scale (str): Musical scale to use (default: "chromatic")
        """
        self.min_note = min_note
        self.max_note = max_note
        self.scale = scale
        
        # Define musical scales as note offsets from root
        self.scales = {
            "chromatic": list(range(12)),  # All semitones
            "major": [0, 2, 4, 5, 7, 9, 11],  # Major scale
            "minor": [0, 2, 3, 5, 7, 8, 10],  # Natural minor
            "pentatonic": [0, 2, 4, 7, 9],  # Major pentatonic
            "blues": [0, 3, 5, 6, 7, 10],  # Blues scale
            "dorian": [0, 2, 3, 5, 7, 9, 10],  # Dorian mode
        }
        
        # Generate note sequence for current scale
        self._generate_note_sequence()
        
        # Velocity and timing parameters
        self.velocity_min = 0.1
        self.velocity_max = 1.0
        self.note_duration_ms = 500  # Default note duration
        
    def _generate_note_sequence(self):
        """Generate sequence of available notes based on scale"""
        if self.scale not in self.scales:
            self.scale = "chromatic"
        
        scale_intervals = self.scales[self.scale]
        self.note_sequence = []
        
        # Generate notes within range using scale intervals
        current_note = self.min_note
        while current_note <= self.max_note:
            # Find which octave and note within scale
            octave_offset = 0
            
            # Add notes for this octave
            for interval in scale_intervals:
                note = current_note + interval + (octave_offset * 12)
                if self.min_note <= note <= self.max_note:
                    self.note_sequence.append(note)
            
            current_note += 12  # Next octave
        
        # Sort and remove duplicates
        self.note_sequence = sorted(list(set(self.note_sequence)))
    
    def set_scale(self, scale):
        """
        Change musical scale
        
        Args:
            scale (str): Scale name (chromatic, major, minor, etc.)
        """
        if scale in self.scales:
            self.scale = scale
            self._generate_note_sequence()
    
    def set_range(self, min_note, max_note):
        """
        Set note range
        
        Args:
            min_note (int): Minimum MIDI note number
            max_note (int): Maximum MIDI note number
        """
        self.min_note = max(0, min(127, min_note))
        self.max_note = max(0, min(127, max_note))
        
        # Ensure min < max
        if self.min_note >= self.max_note:
            self.max_note = self.min_note + 12
            
        self._generate_note_sequence()
    
    def light_to_note(self, light_intensity):
        """
        Convert light intensity to MIDI note
        
        Args:
            light_intensity (float): Light intensity 0.0-100.0
            
        Returns:
            int: MIDI note number
        """
        if not self.note_sequence:
            return 60  # Middle C fallback
        
        # Normalize intensity to 0-1 range
        normalized = max(0.0, min(1.0, light_intensity / 100.0))
        
        # Map to note sequence
        note_index = int(normalized * (len(self.note_sequence) - 1))
        return self.note_sequence[note_index]
    
    def light_to_velocity(self, light_intensity):
        """
        Convert light intensity to note velocity
        
        Args:
            light_intensity (float): Light intensity 0.0-100.0
            
        Returns:
            float: Velocity value 0.0-1.0
        """
        # Normalize intensity
        normalized = max(0.0, min(1.0, light_intensity / 100.0))
        
        # Apply curve for more musical response
        # Square root curve makes low light more responsive
        curved = math.sqrt(normalized)
        
        # Map to velocity range
        return self.velocity_min + (curved * (self.velocity_max - self.velocity_min))
    
    def light_to_duration(self, light_intensity, *, min_duration_ms=100, max_duration_ms=1000):
        """
        Convert light intensity to note duration
        
        Args:
            light_intensity (float): Light intensity 0.0-100.0
            min_duration_ms (int): Minimum note duration
            max_duration_ms (int): Maximum note duration
            
        Returns:
            int: Duration in milliseconds
        """
        normalized = max(0.0, min(1.0, light_intensity / 100.0))
        
        # Brighter light = shorter, more staccato notes
        # Dimmer light = longer, more sustained notes
        duration = max_duration_ms - (normalized * (max_duration_ms - min_duration_ms))
        return int(duration)
    
    def create_note_event(self, light_intensity):
        """
        Create complete note event from light intensity
        
        Args:
            light_intensity (float): Light intensity 0.0-100.0
            
        Returns:
            dict: Note event with pitch, velocity, duration
        """
        return {
            "pitch": self.light_to_note(light_intensity),
            "velocity": self.light_to_velocity(light_intensity),
            "duration_ms": self.light_to_duration(light_intensity),
            "light_intensity": light_intensity
        }
    
    def get_scale_info(self):
        """
        Get information about current scale and mapping
        
        Returns:
            dict: Scale information
        """
        return {
            "scale": self.scale,
            "min_note": self.min_note,
            "max_note": self.max_note,
            "available_notes": len(self.note_sequence),
            "note_range": self.note_sequence[:5] if len(self.note_sequence) >= 5 else self.note_sequence
        }