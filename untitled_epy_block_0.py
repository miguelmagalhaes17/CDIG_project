import numpy as np
import time
from gnuradio import gr
import time

class FrequencySweeper(gr.sync_block):
    """
    Sweeps through frequencies, measures signal strength, 
    and outputs the frequency with strongest signal.
    Requires a callback function to set the SDR frequency.
    """
    def __init__(self, start_freq=400e6, stop_freq=5e9, step=10e6, 
                 dwell_time=0.1, fft_size=1024, set_freq_callback=None):
        gr.sync_block.__init__(
            self,
            name="FrequencySweeper",
            in_sig=[(np.complex64, 256)],  # Expects FFT input
            out_sig=None
        )
        
        self.start_freq = start_freq
        self.stop_freq = stop_freq
        self.step = step
        self.dwell_time = dwell_time
        self.fft_size = fft_size
        self.set_freq_callback = set_freq_callback
        
        # State variables
        self.current_freq = start_freq
        self.max_power = -np.inf
        self.best_freq = start_freq
        self.sweeping = True
        self.sample_count = 0
        self.samples_per_freq = int(dwell_time * 100)  # Adjust based on sample rate
        
      
        # Set initial frequency
        if self.set_freq_callback:
            self.set_freq_callback(self.start_freq)
        
        print(f"Sweeper initialized: {start_freq/1e6:.1f} - {stop_freq/1e6:.1f} MHz")
        print(f"Step: {step/1e6:.1f} MHz, Dwell: {dwell_time}s")
        
    def work(self, input_items, output_items):
        if not self.sweeping:
            return len(input_items[0])
        
        # Get FFT data (magnitude squared)
        fft_data = input_items[0]
        
        # Calculate average power across the band
        power = np.mean(np.abs(fft_data)**2)
        power_db = 10 * np.log10(power + 1e-12)  # Avoid log(0)
        
        # Update if this is the strongest signal
        if power > self.max_power:
            self.max_power = power
            self.best_freq = self.current_freq
            print(f"New max at {self.current_freq/1e6:.1f} MHz: {power_db:.1f} dB")
        
        self.sample_count += len(fft_data)
        
        if self.sample_count >= self.samples_per_freq:
            self.sample_count = 0
            
            # Move to next frequency
            self.current_freq += self.step
            
            if self.current_freq > self.stop_freq:
                # Sweep complete!
                self.sweeping = False
                best_freq_mhz = self.best_freq / 1e6
                max_power_db = 10 * np.log10(self.max_power + 1e-12)
                
                print("\n" + "="*50)
                print(f"SWEEP COMPLETE!")
                print(f"Strongest signal: {best_freq_mhz:.2f} MHz")
                print(f"Power: {max_power_db:.1f} dB")
                print("="*50 + "\n")
                
                # Set SDR to best frequency
                if self.set_freq_callback:
                    self.set_freq_callback(self.best_freq)
                    print(f"SDR tuned to {best_freq_mhz:.2f} MHz")
            else:                # Tune to next frequency
                if self.set_freq_callback:
                    self.set_freq_callback(self.current_freq)
                print(f"Tuning to {self.current_freq/1e6:.1f} MHz...")
        
        return len(input_items[0])
