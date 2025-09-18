"""
Enhanced Audio Synthesizer for Pico Light Orchestra
Provides ADSR envelope, waveform generation, and musical features
"""
import time
import math
from audio_driver import PWMAudioDriver

class ADSREnvelope:
    """
    ADSR (Attack, Decay, Sustain, Release) envelope generator
    """
    
    def __init__(self, attack_ms=50, decay_ms=100, sustain_level=0.7, release_ms=200):
        """
        Initialize ADSR envelope
        
        Args:
            attack_ms (int): Attack time in milliseconds
            decay_ms (int): Decay time in milliseconds  
            sustain_level (float): Sustain level 0.0-1.0
            release_ms (int): Release time in milliseconds
        """
        self.attack_ms = attack_ms
        self.decay_ms = decay_ms
        self.sustain_level = max(0.0, min(1.0, sustain_level))
        self.release_ms = release_ms
        
        # Envelope state
        self.phase = "off"  # off, attack, decay, sustain, release
        self.start_time = 0
        self.phase_start_time = 0
        self.release_start_time = 0
        self.current_level = 0.0
    
    def trigger(self, now_ms):
        """Start the envelope from attack phase"""
        self.phase = "attack"
        self.start_time = now_ms
        self.phase_start_time = now_ms
        self.current_level = 0.0
    
    def release(self, now_ms):
        """Start release phase"""
        if self.phase != "off":
            self.phase = "release"
            self.release_start_time = now_ms
    
    def get_level(self, now_ms):
        """
        Get current envelope level
        
        Args:
            now_ms (int): Current time in milliseconds
            
        Returns:
            float: Current envelope level 0.0-1.0
        """
        if self.phase == "off":
            return 0.0
        
        elapsed = time.ticks_diff(now_ms, self.phase_start_time)
        
        if self.phase == "attack":
            if elapsed >= self.attack_ms:
                # Move to decay phase
                self.phase = "decay"
                self.phase_start_time = now_ms
                self.current_level = 1.0
            else:
                # Linear attack
                self.current_level = elapsed / self.attack_ms
        
        elif self.phase == "decay":
            if elapsed >= self.decay_ms:
                # Move to sustain phase
                self.phase = "sustain"
                self.phase_start_time = now_ms
                self.current_level = self.sustain_level
            else:
                # Exponential decay
                progress = elapsed / self.decay_ms
                self.current_level = 1.0 - (progress * (1.0 - self.sustain_level))
        
        elif self.phase == "sustain":
            self.current_level = self.sustain_level
        
        elif self.phase == "release":
            elapsed_release = time.ticks_diff(now_ms, self.release_start_time)
            if elapsed_release >= self.release_ms:
                self.phase = "off"
                self.current_level = 0.0
            else:
                # Linear release from current level
                release_progress = elapsed_release / self.release_ms
                release_start_level = self.sustain_level
                self.current_level = release_start_level * (1.0 - release_progress)
        
        return max(0.0, min(1.0, self.current_level))
    
    def is_active(self):
        """Check if envelope is currently active"""
        return self.phase != "off"

class PicoSynth:
    """
    Enhanced synthesizer for Pico Light Orchestra
    """
    
    def __init__(self, audio_driver=None):
        """
        Initialize synthesizer
        
        Args:
            audio_driver: PWMAudioDriver instance, or None to create default
        """
        if audio_driver is not None:
            self.audio = audio_driver
        else:
            self.audio = PWMAudioDriver()
        
        # Synthesis state
        self.current_note = None
        self.envelope = ADSREnvelope()
        self.master_volume = 0.8
        
        # Note tracking
        self.note_start_time = 0
        self.note_duration_ms = 0
        self.auto_release = True
    
    def set_envelope(self, attack_ms=50, decay_ms=100, sustain_level=0.7, release_ms=200):
        """
        Configure ADSR envelope parameters
        
        Args:
            attack_ms (int): Attack time in milliseconds
            decay_ms (int): Decay time in milliseconds
            sustain_level (float): Sustain level 0.0-1.0 
            release_ms (int): Release time in milliseconds
        """
        self.envelope = ADSREnvelope(attack_ms, decay_ms, sustain_level, release_ms)
    
    def play_note(self, frequency, velocity=1.0, duration_ms=None):
        """
        Play a musical note
        
        Args:
            frequency (int): Note frequency in Hz
            velocity (float): Note velocity 0.0-1.0
            duration_ms (int): Note duration, or None for sustained
        """
        now_ms = time.ticks_ms()
        
        # Stop current note if playing
        if self.current_note is not None:
            self.envelope.release(now_ms)
        
        # Start new note
        self.current_note = {
            'frequency': frequency,
            'velocity': max(0.0, min(1.0, velocity)),
            'start_time': now_ms
        }
        
        self.note_start_time = now_ms
        self.note_duration_ms = duration_ms if duration_ms is not None else 0
        
        # Trigger envelope and start audio
        self.envelope.trigger(now_ms)
        self.audio.set_frequency(frequency)
    
    def release_note(self):
        """Manually release current note"""
        if self.current_note is not None:
            self.envelope.release(time.ticks_ms())
    
    def stop_all(self):
        """Stop all audio immediately"""
        self.current_note = None
        self.envelope.phase = "off"
        self.audio.stop()
    
    def update(self):
        """
        Update synthesizer state - call this regularly (every ~10ms)
        """
        now_ms = time.ticks_ms()
        
        if self.current_note is None:
            self.audio.stop()
            return
        
        # Check for auto-release based on duration
        if (self.auto_release and 
            self.note_duration_ms > 0 and 
            time.ticks_diff(now_ms, self.note_start_time) >= self.note_duration_ms):
            self.envelope.release(now_ms)
        
        # Update envelope
        envelope_level = self.envelope.get_level(now_ms)
        
        if envelope_level <= 0.0:
            # Note has finished
            self.current_note = None
            self.audio.stop()
        else:
            # Calculate final volume
            velocity = self.current_note['velocity']
            final_volume = envelope_level * velocity * self.master_volume
            self.audio.set_volume(final_volume)
    
    def is_playing(self):
        """Check if a note is currently playing"""
        return self.current_note is not None and self.envelope.is_active()
    
    def get_status(self):
        """
        Get synthesizer status
        
        Returns:
            dict: Current synthesizer state
        """
        if self.current_note is not None:
            return {
                'playing': True,
                'frequency': self.current_note['frequency'],
                'velocity': self.current_note['velocity'],
                'envelope_phase': self.envelope.phase,
                'envelope_level': self.envelope.get_level(time.ticks_ms()),
                'audio_status': self.audio.get_status()
            }
        else:
            return {
                'playing': False,
                'audio_status': self.audio.get_status()
            }
