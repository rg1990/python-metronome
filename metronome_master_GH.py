import sounddevice as sd
import numpy as np
import audiofile
import sys
import queue
import threading


class Metronome():
    def __init__(self, tempo=180, beats_per_bar=4):
        # Define limits for tempo and beats_per_bar
        self.min_tempo = 10
        self.max_tempo = 350
        self.min_beats_per_bar = 1
        self.max_beats_per_bar = 8
        
        # Input validation
        if tempo < self.min_tempo or tempo > self.max_tempo:
            raise Exception(f"Tempo must be between {self.min_tempo} and {self.max_tempo}.")
        
        if beats_per_bar < self.min_beats_per_bar or beats_per_bar > self.max_beats_per_bar:
            raise Exception(f"Value for beats_per_bar must be between {self.min_beats_per_bar} and {self.max_beats_per_bar}.")
        
        
        self.tempo = tempo
        self.beats_per_bar = beats_per_bar
        
        # State attribute
        self.running = False
        
        # Used for changing tempo while playing
        self.new_tempo = None   
        self.tempo_change_pending = False
        
        # Load and define the arrays of samples for different click sounds
        self.fs = 16000     # sample rate of audio, in Hz
        self.hi, _ = audiofile.read("./samples/hi.wav")
        self.lo, _ = audiofile.read("./samples/lo.wav")
        self.empty_click = np.zeros_like(self.lo)
        
        
        # Define attributes for use with audio stream
        self.BLOCKSIZE = 512    # samples per block of audio
        # TODO - write code to pre-fill the queue
        self.BUFFERSIZE = 10    # blocks of audio to pre-fill queue with
        self.TIMEOUT = self.BLOCKSIZE * self.BUFFERSIZE / self.fs
        
        self.q = queue.Queue(maxsize=self.BUFFERSIZE)
        self.event = threading.Event()
        self.stream = self.create_stream()
        
        
        # Instantiate attributes related to click timing
        self.num_samples_until_next_click = 0
        self.float_interval = self.fs * 60.0 / self.tempo
        self.interval = int(self.fs * 60.0 / self.tempo)
        self.interval_samples_elapsed = 0
        
        # Create a block of zeros to deliver to the stream between clicks
        self.zero_array = np.zeros(self.BLOCKSIZE)
        
        # Instantiate some counters
        self.total_samples_delivered = 0
        self.current_beat = 0
        self.beat_to_show = 0
        self.beats_at_tempo = 0
        self.bars_to_play_at_tempo = None   # for playing a specific number of bars
        
        # Set up the array that determines which click sound to use for each beat
        self.beat_click_indices = self.create_beat_click_index_array()
        self.click_sounds = np.array([self.empty_click, self.lo, self.hi])
        # Initialise a dictionary with click sound choice for each beat, using default values
        self.update_beat_sample_dict(self.beat_click_indices)
        # bool for improved code readability
        self.click_is_due_in_this_block = False  
        
        # Drift error compensation
        self.accumulated_drift_error = 0.0
        self.drift_error_per_block = self.compute_drift_error_per_block()
        self.samples_to_shift = 0
        
        # For plotting and saving to WAV for analysis
        self.full_output = []
        # Store the "tail" of a click that spans 2 adjacent arrays of size self.BLOCKSIZE
        self.tail_array = None  
        
        
    # TODO - Speed trainer is in development
    # def enable_trainer(self, start_tempo, bars_at_tempo, bpm_increase, num_increases):
    #     self.trainer_enabled = True
    #     self.trainer_start_tempo = start_tempo
    #     self.trainer_bars_at_tempo = bars_at_tempo
    #     self.trainer_bpm_increase = bpm_increase
    #     self.trainer_num_increases = num_increases
        
    #     self.trainer_end_tempo = self.trainer_start_tempo + (self.trainer_num_increases * self.trainer_bpm_increase)
        

    # def disable_trainer(self):
    #     self.trainer_active = False
        
        
    
    def pre_fill_queue(self):
        # Range is (BUFFERSIZE-1) because the first callback will add a block too
        # and otherwise we get an exception because the queue is already full.
        for _ in range(self.BUFFERSIZE-1):
            next_audio_block, beat = self.get_next_audio_block()
            # Debugging print statements to check output
            # print(f"Mean: {np.mean(next_audio_block)}")
            # print(f"Queue size before putting: {self.q.qsize()}")
            if not len(next_audio_block):
                break
            self.q.put_nowait([next_audio_block, beat])
            # Append the new audio block to full_output for later examination
            self.full_output.append(next_audio_block)
    
    
    def create_stream(self):        
        # Create an OutputStream instance
        return sd.OutputStream(samplerate=self.fs,
                                     blocksize=self.BLOCKSIZE,
                                     channels=1,
                                     callback=self.callback,
                                     finished_callback=self.event.set)
    
    
    # TODO - these increase and decrease methods may be combined (DRY)
    # and would just require an additional parameter
    def increase_beats_per_bar(self):
        if self.beats_per_bar < self.max_beats_per_bar:
            self.beats_per_bar += 1
            new_click_indices = np.append(self.beat_click_indices, [1])
            self.update_beat_sample_dict(new_click_indices)
        
    
    def decrease_beats_per_bar(self):
        if self.beats_per_bar > 1:
            self.beats_per_bar -= 1
            new_click_indices = self.beat_click_indices[:-1]
            self.update_beat_sample_dict(new_click_indices)
            
            # Handle quick consecutive calls. If beats_per_bar is reduced below
            # the current beat while playing, reset the current beat to 1.
            if self.current_beat > self.beats_per_bar:
                self.current_beat = 1
    
    
    def set_new_tempo(self, new_tempo_value):
        # This would be called by a Controller after the View has been updated
        # by the user to select a new tempo value using the Scale widget
        new_tempo_value = int(new_tempo_value)
        
        # Check new tempo is in valid range
        if new_tempo_value >= self.min_tempo and new_tempo_value <= self.max_tempo:
            # If not running, recompute values and reset counters for updated tempo
            if self.running == False:
                self.tempo = new_tempo_value
                self.update_values_for_new_tempo()
            
            # If running, instruct a tempo change to occur at next beat
            else:
                if new_tempo_value != self.tempo:    
                    self.new_tempo = new_tempo_value
                    self.tempo_change_pending = True
    
    
    def create_beat_click_index_array(self):
        '''
        Create the default array defining the click sounds to use. The default
        is "hi" on the first beat, followed by "lo" for every other beat in the bar.
        
        The sounds are (0: no sound, 1: lo, 2: hi)
        '''
        # Set up the default to be one hi followed by the rest lo
        return np.concatenate(([2], [1 for i in range(self.beats_per_bar - 1)])).astype(int)
    
    
    def update_beat_sample_dict(self, new_click_indices):
        '''
        Create a dictionary containing click sample audio data (zeros, lo, hi).
        This allows us to obtain the correct samples for the sound which
        should be played at each beat in a bar.
        '''
        # Update the beat_click_indices attribute 
        self.beat_click_indices = new_click_indices
        # Get a list that contains the click sound we want to use for every beat
        samples = [self.click_sounds[idx] for idx in self.beat_click_indices]
        # Create a dictionary whose keys are the beat numbers
        self.beat_sample_dict = {i+1: samples[i] for i in range(self.beats_per_bar)}
    
    
    def start(self):
        # Prevent multiple starts
        if self.running:
            return
        else:
            #print(f"Queue is empty?: {self.q.empty()}")
            # TODO - pre-fill the queue with some audio blocks
            try:
                # New - fill the queue with BUFFERSIZE blocks before playing
                self.pre_fill_queue()
                self.stream.start()
                self.running = True
            except:
                print("Error starting stream")
            
            
    def stop(self):
        if not self.running:
            return
        else:
            #print("Stopping...")
            self.running = False
            self.stream.abort()     # ends the stream quicker than stream.stop()
            self.stream.stop()      # sets the stream's active attribute to False (abort does not do this)
            self.current_beat = 0
            self.beats_at_tempo = 0
            self.bars_to_play_at_tempo = None
            self.total_samples_delivered = 0
            self.num_samples_until_next_click = 0
            # Delete the queue and make a new one to clear out the contents
            del self.q
            self.q = queue.Queue(self.BUFFERSIZE)
       
            
    def compute_drift_error_per_block(self):
        '''
        For the current tempo, calculate the drift error that occurs for every
        audio block of size self.BLOCKSIZE that is passed to the output stream.
        
        The drift error per sample is first calculated, then multiplied by
        self.BLOCKSIZE to get the total drift error for the whole audio block.
        '''
        
        samples_per_beat, decimal_component = divmod(self.fs * 60.0 / self.tempo, 1)
        error_per_sample = decimal_component / samples_per_beat
        return self.BLOCKSIZE * error_per_sample
    
        
    def update_values_for_new_tempo(self):
        '''
        Call this whenever the tempo is changed. A number of tempo-specific
        values are recalculated, and tempo-specific counters are reset.
        '''
        if self.new_tempo is not None:
            self.tempo = self.new_tempo
        self.total_samples_delivered = 0
        self.drift_error_per_block = self.compute_drift_error_per_block()
        self.beats_at_tempo = 0
        self.float_interval = self.fs * 60.0 / self.tempo
        self.interval = int(self.fs * 60.0 / self.tempo)
    
    
    def callback(self, outdata, frames, time, status):
        '''
        This is called repeatedly by the sounddevice OutputStream.
        See sounddevice docs for specifics.
        
        Blocks of audio are generated and passed to the queue, to later be
        removed from the queue as required by the OutputStream. The same data
        that is sent to the queue is also appended to self.full_output in order
        to allow analysis of the output.
        
        '''

        next_audio_block, beat = self.get_next_audio_block()
        # If the next_audio_block array contains all -1 values, we don't want
        # to actually output this one. So don't add it to the queue, and abort the callback
        # to avoid queue.Empty
        if np.all(next_audio_block==-1):
            raise sd.CallbackAbort()
        else:
            self.q.put_nowait([next_audio_block, beat])
            # Append the new audio block to full_output for later examination
            self.full_output.append(next_audio_block)
        
        assert frames == self.BLOCKSIZE
        if status.output_underflow:
            print('Output underflow: increase blocksize?', file=sys.stderr)
            raise sd.CallbackAbort
        assert not status
        try:
            # Set the beat_to_show attribute here so UI matches audio output
            data, self.beat_to_show = self.q.get_nowait()
        except queue.Empty:
            print('Buffer is empty: increase buffersize?', file=sys.stderr)
            raise sd.CallbackAbort
        if len(data) < len(outdata):
            outdata[:len(data)] = data.reshape((-1, 1))
            outdata[len(data):].fill(0)
            raise sd.CallbackStop
        else:
            outdata[:] = data.reshape((-1, 1))
        
    
    def get_current_beat(self):
        return self.current_beat


    def create_click_data_arrays(self, click_data):
        '''
        It is quite likely that the samples of a click sound (length 400 samples)
        will span more than one audio block of size 512 (self.BLOCKSIZE),
        depending on which index within a block of 512 the click sound begins.
        
        For this reason, we create a "big_arr" array of zeros and place the
        click samples at the correct indices, then chop big_arr in two so we
        can first deliver the start of the click sound, and then the "tail"
        of the click sound, in consecutive audio blocks sent to the stream.
        
        '''
        # Build the array of zeros spanning two BLOCKSIZE windows
        big_arr = np.zeros(2 * self.BLOCKSIZE)
        # Place the click data at the correct place in the big array
        big_arr[self.num_samples_until_next_click : self.num_samples_until_next_click + len(click_data)] = click_data
        # Chop big_arr in half to obtain data and tail_array
        data = big_arr[:self.BLOCKSIZE]
        tail_array = big_arr[self.BLOCKSIZE:]
        
        return data, tail_array
    
    
    def get_num_samples_until_next_click(self):
        '''
        Determine how many samples there should be between "now" and the start
        of the next click sound.
        '''
        
        # Find out how far through an interval we are
        # (how far through the space between the start of clicks)
        self.interval_samples_elapsed = self.total_samples_delivered % self.interval
        num_samples_until_next_click = self.interval - self.interval_samples_elapsed
        
        # Compensate for drift error (shift future samples to the right)
        num_samples_until_next_click += self.samples_to_shift
        
        # If this exceeds the interval size, we miss clicks. Compensate.
        if num_samples_until_next_click > self.interval:
            num_samples_until_next_click -= self.interval
        
        return int(num_samples_until_next_click)
    
    
    # New version created on 28th June
    def get_next_audio_block(self):
        '''
        This is where most of the heavy lifting is done. 
        
        '''
        # If we do not have a tail array to deliver
        # (true at first call and whenever we deliver zeros)
        if self.tail_array is None:           
            
            # Make sure we deliver a click when we first start
            if self.total_samples_delivered == 0:
                self.click_is_due_in_this_block = True
            
            # Find out how long until the next click
            if self.total_samples_delivered > 0:
                
                # Get num samples until next click scheduled to start
                self.num_samples_until_next_click = self.get_num_samples_until_next_click()
                
                # Determine if a click is needed in the audio block being constructed
                if self.num_samples_until_next_click <= self.BLOCKSIZE:
                    self.click_is_due_in_this_block = True
                else:
                    self.click_is_due_in_this_block = False
            
            
            if self.click_is_due_in_this_block:
                # If we have asked for a specific number of bars, stop when finished
                if self.bars_to_play_at_tempo is not None:                
                    if self.beats_at_tempo == self.beats_to_play_at_tempo:
                        self.stop()
                        # Once we have reached the end of our desired number of bars,
                        # return an array of all -1 values so our callback knows to abort
                        return [np.array([-1] * self.BLOCKSIZE), self.current_beat]

                
                # We can start current_beat at zero and increment at exactly 
                # the same time as the new click data being created.
                # Also means the beat number matches what we hear.
                self.current_beat = (self.current_beat % self.beats_per_bar) + 1
                self.beats_at_tempo += 1

                # Determine which sample (hi, lo, or zeros) we should hear for this beat    
                click = self.beat_sample_dict[self.current_beat]
                
                # Create the arrays containing click samples
                data, self.tail_array = self.create_click_data_arrays(click_data=click)

            else:
                # Click doesn't start in next block, so deliver a block of zeros instead
                data = self.zero_array

        
        # This means tail array is not None. Deliver the tail of the click samples
        else:
            # Assign the tail_array to the data to be returned 
            data = self.tail_array
            # Reset the attribute for the next call
            self.tail_array = None
            
            # Set and reset some things if a new tempo has been instructed
            # so we can start the new tempo immediately after this beat is
            # finished being delivered
            if self.tempo_change_pending:
                #print("Tempo change should happen now")
                self.tempo_change_pending = False
                self.update_values_for_new_tempo()
            
        # Once we get here, we have decided what the "data" array should contain
        # Update counters etc here before the next call
        self.total_samples_delivered += self.BLOCKSIZE
        self.accumulated_drift_error += self.drift_error_per_block
        
        # Compare the current accumulated drift error value to that from the previous
        # call. If the integer part of the number has changed, increment self.samples_to_shift
        prev_drift_int, _ = divmod(self.accumulated_drift_error-self.drift_error_per_block, 1)
        current_drift_int, _ = divmod(self.accumulated_drift_error, 1)
        
        if current_drift_int > prev_drift_int:
            self.samples_to_shift += 1
        
        # Add the current beat to the data array so we know which beat we
        # are actually hearing when the data is taken from queue -> speakers
        data = [data, self.current_beat]
                
        return data
        
    
    def play_for_num_bars(self, num_bars):
        # Play the click for the specified number of bars
        print(f"Number of beats required for {num_bars} bar(s) is: {num_bars * self.beats_per_bar}")
        self.bars_to_play_at_tempo = num_bars
        self.beats_to_play_at_tempo = num_bars * self.beats_per_bar
        self.start()
            
        
    def print_info(self):        
        print(f"The click sound contains {self.num_samples_in_click} samples.")
        print(f"There are {self.num_samples_until_next_click} samples until the next click should start.")
        print(f"The integer number of samples per beat is {self.interval}.")
        
        