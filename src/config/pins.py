"""
pins.py --> central config for pins and HAL tunables.
- A single source of truth for wiring and knobs. no machine imports
   
"""
#execution mode flag


SIMULATION = False  #a flag for top level program to read and decide whether to use
                    #fake drivers on laptop or real drivers on pico.
                    #True = run with fakes on laptop.
                   
                   
#pin map on pico - assignments for light sensor, buzzer, and buttons
"""
HAL drivers read these so no one writes (ADC(28) or PWM(16)
in the codebase. Change values not drivers if wiring changes
"""            
PIN_LDR_ADC = 28   # gp28 (adc2) - light sensor
PIN_BUZZER = 16    # gp16 (pwm) - piezo buzzer
PIN_BTN_A = 14     # gp14 (pull-up)
PIN_BTN_B = 15     # gp15 (pull-up)




#adc tuning (using by adc_reader.py) - noise reduction knobs for the light sensor
"""
(ADC_SAMPLES): more samples = less noise, more cpu. start at 4 for a 10ms loop
(EMA_ALPHA): lower = smoother but slow react; 0.3 is a good starting point
(MEDIAN_WIN): set to 3 if you see spiky readings or mains flicker;
keep at 1 (off) to save cpu
"""
ADC_SAMPLES = 4    #raw reads to average
EMA_ALPHA = 0.3    #smoothing (0<α≤1; lower = smoother/slower)
MEDIAN_WIN = 1     #1=off, 3=enable 3-sample median




#audio defaults (used by pwm_audio.py)
"""
Default PWM duty for the buzzer (rough volume)
Perceived loudness isnt linear; staying <= 0.7 avoids harshness/clipping
"""
TONE_DUTY = 0.5   #O.1 perceived loudness

