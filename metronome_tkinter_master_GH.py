from metronome_master import Metronome
import tkinter as tk
import numpy as np
import glob
from PIL import Image, ImageTk
from scipy.io import wavfile


class BeatSoundLabel(tk.Label):
    '''
    A subclass of tkinter's Label class, with some additional attributes
    that are used to store values related to the intended appearance of the
    label.
    
    These are index and state values which are used to retrieve images which
    are passed to the "image" parameter of the parent class's "config" method.
    
    '''
    
    def __init__(self, master, label_list_index=None, click_sound_index=0, beat_state="off"):
        super().__init__(master)
        self.label_list_index = label_list_index
        self.click_sound_index = click_sound_index
        self.beat_state = beat_state



class App():
    def __init__(self, metro: Metronome):
        self.metro = metro
        
        self.root = tk.Tk()
        #self.root = tk.Toplevel()
        self.root.title("Metronome")
        self.root.geometry("750x850")
        self.root.configure(background="black")
        
        # Define the paths for images to be loaded
        self.define_image_filepaths()
        # Load the images for the GUI
        self.load_images()
        
        # Create the StringVar that shows the current beat.
        self.beat_string_var = tk.StringVar()
        self.beat_string_var.set("")
        
        # Create these arrays using the maximum allowed beats per bar and update later
        # An array stating which click sound should be used for each beat
        self.index_array = np.concatenate(([2], np.ones(self.metro.max_beats_per_bar-1))).astype(int)
        # An array holding the state (on/off) of the illumination for each beat
        self.beat_state_array = np.array(["off" for i in range(len(self.index_array))])
        
        # Tempo frame config
        self.tempo_canvas_width = 500
        self.tempo_canvas_height = 200
        self.tempo_font_size = 90
        self.time_sig_font_size = 60
        
        # Params for coloured beat indicator labels
        self.labels = []
        self.label_width = 80
        self.label_height = 120
        
        self.beat_currently_shown = 0
        self.make_widgets()
        
        self.create_label_image_dict()
        self.build_label_frame()
        
        
        # Bind the space bar to the ui_start_stop method
        self.root.bind("<space>", self.ui_start_stop)
        # Attach the method for handling window closing
        self.root.protocol("WM_DELETE_WINDOW", self.on_window_closing)
         
        # After everything else is set up, make the displayed labels specific to the beats per bar
        for i in range(len(self.labels)-1, self.metro.beats_per_bar-1, -1):
            self.labels[i].pack_forget()
     
            
    
    def define_image_filepaths(self):
        # Paths with multiple files for use with glob
        self.on_img_fpath = "./images/on/*.jpg"
        self.off_img_fpath = "./images/off/*.jpg"
        # Paths to specific individual images
        self.play_button_path = "./images/play_button.jpg"
        self.stop_button_path = "./images/stop_button.jpg"
        self.plus_button_path = "./images/plus_button.jpg"
        self.minus_button_path = "./images/minus_button.jpg"
    
    
    def load_images(self):
        self.play_button_image = ImageTk.PhotoImage(Image.open(self.play_button_path))
        self.stop_button_image = ImageTk.PhotoImage(Image.open(self.stop_button_path))
        self.plus_button_image = ImageTk.PhotoImage(Image.open(self.plus_button_path))
        self.minus_button_image = ImageTk.PhotoImage(Image.open(self.minus_button_path))
    
    
    def create_label_image_dict(self):
        # Obtain filenames for images showing all possible coloured label states
        self.on_image_filenames = glob.glob(self.on_img_fpath)        
        self.off_image_filenames = glob.glob(self.off_img_fpath)

        # Create lists of PhotoImage objects for use with BeatSoundLabel objects
        self.on_images = [Image.open(path) for path in self.on_image_filenames]
        self.on_photos = [ImageTk.PhotoImage(image.resize((self.label_width, self.label_height), Image.ANTIALIAS)) for image in self.on_images]

        self.off_images = [Image.open(path) for path in self.off_image_filenames]
        self.off_photos = [ImageTk.PhotoImage(image.resize((self.label_width, self.label_height), Image.ANTIALIAS)) for image in self.off_images]

        # Place these lists in a dict
        self.img_dict = {'on': self.on_photos,
                         'off': self.off_photos}
    
    
    def make_widgets(self):
        self.build_tempo_frame()
        self.add_tempo_text()
        self.add_time_sig_text()
                
        self.label_frame = tk.Frame(master=self.root)
        self.label_frame.pack(padx=0, pady=(20,20), fill=None, expand=False)
        
        beat_label = tk.Label(self.root, fg="red", bg="black", textvariable=self.beat_string_var, font=("arkitech", 48))
        beat_label.pack()

        # self.start_stop_btn_frame = tk.Frame(self.root, width=self.tempo_canvas_width)
        # self.start_stop_btn_frame.pack()
        # self.start_stop_button = tk.Button(master=self.start_stop_btn_frame, text="START", width=60, command=self.ui_start_stop)
        # self.start_stop_button.pack()
                
        
        # Add a slider to control tempo
        self.slider_frame = tk.Frame(master=self.root)
        self.slider_frame.pack(pady=(0, 0))
        
        self.tempo_slider = tk.Scale(master=self.slider_frame,
                                     width=50,
                                     length=490,
                                     showvalue=False,
                                     troughcolor="#575757",
                                     from_=self.metro.min_tempo,
                                     to=self.metro.max_tempo,
                                     orient=tk.HORIZONTAL)
        
        
        self.tempo_slider.set(self.metro.tempo)
        self.tempo_slider.pack(side=tk.BOTTOM)
        self.tempo_slider.configure(command=self.set_new_tempo)


        self.start_stop_btn_frame = tk.Frame(self.root, width=self.tempo_canvas_width)
        self.start_stop_btn_frame.pack(pady=(20, 20))
        # self.start_stop_button = tk.Button(master=self.start_stop_btn_frame, text="START", width=60, command=self.ui_start_stop)
        self.start_stop_button = tk.Button(master=self.start_stop_btn_frame, image=self.play_button_image, highlightthickness=0, bd=0, command=self.ui_start_stop)
        self.start_stop_button.pack()
        
        # Add buttons to adjust the time signature
        self.time_sig_button_frame = tk.Frame(master=self.root, width=self.tempo_canvas_width, bg='black')#, highlightbackground="red", highlightthickness=2)
        self.time_sig_button_frame.pack()#, fill='x', expand=True)
        
        time_sig_title = tk.Label(master=self.time_sig_button_frame, text="BEATS PER BAR", fg="white", bg="black")
        time_sig_title.pack()
               
        # Buttons without images
        # self.reduce_time_sig_button = tk.Button(master=self.time_sig_button_frame, text="-", width=10, height=2, command=self.decrement_coloured_beat_labels)
        # self.increase_time_sig_button = tk.Button(master=self.time_sig_button_frame, text="+", width=10, height=2, command=self.increment_coloured_beat_labels)
        
        # Buttons with images
        self.reduce_time_sig_button = tk.Button(master=self.time_sig_button_frame, image=self.minus_button_image, highlightthickness=0, bd=0, command=self.decrement_coloured_beat_labels)
        self.increase_time_sig_button = tk.Button(master=self.time_sig_button_frame, image=self.plus_button_image, highlightthickness=0, bd=0, command=self.increment_coloured_beat_labels)
        
        
        self.reduce_time_sig_button.pack(side=tk.LEFT)#, fill='both', expand=True)
        self.increase_time_sig_button.pack(side=tk.LEFT)#, fill='x', expand=True)

        
        # Add tempo adjustment buttons
        self.minus_10_button = tk.Button(master=self.time_sig_button_frame, width=7, height=2, text="-10", command=lambda:self.adjust_tempo(-10))
        self.minus_5_button = tk.Button(master=self.time_sig_button_frame, width=7, height=2, text="-5", command=lambda:self.adjust_tempo(-5))
        self.plus_5_button = tk.Button(master=self.time_sig_button_frame, width=7, height=2, text="+5", command=lambda:self.adjust_tempo(5))
        self.plus_10_button = tk.Button(master=self.time_sig_button_frame, width=7, height=2, text="+10", command=lambda:self.adjust_tempo(10))
        
        self.minus_10_button.pack(side=tk.LEFT)
        self.minus_5_button.pack(side=tk.LEFT)
        self.plus_5_button.pack(side=tk.LEFT)
        self.plus_10_button.pack(side=tk.LEFT)
        
        
        # Old +/- buttons for updating metro beats per bar without UI updates
        # tk.Button(btn_frame, text="+", command=self.metro.increase_beats_per_bar).pack(side=tk.RIGHT)
        # tk.Button(btn_frame, text="-", command=self.metro.decrease_beats_per_bar).pack(side=tk.LEFT)
    
        
    def build_tempo_frame(self):
        '''
        Build the tkinter Frame that will contain the text showing the tempo
        and time signature. The Frame contains a tkinter Canvas, where the
        text gets placed.
        '''
        self.tempo_frame = tk.Frame(master=self.root)
        self.tempo_frame.pack(anchor='center', fill='y', pady=(20,0))
        
        self.tempo_canvas = tk.Canvas(master=self.tempo_frame,
                                      bg='black',
                                      height=self.tempo_canvas_height,
                                      width=self.tempo_canvas_width)
        
        self.tempo_canvas.pack(side=tk.TOP)
        
        
    def build_label_frame(self):
        # Build the initial set of BeatSoundLabel objects
        for i, click_idx in enumerate(self.index_array):
            l = BeatSoundLabel(self.label_frame,
                                label_list_index=i,
                                click_sound_index=click_idx,
                                beat_state=self.beat_state_array[i])
            
            l.config(image=self.img_dict[self.beat_state_array[i]][self.index_array[i]], bg="#a8a8a8")
            
            self.labels.append(l)
            l.pack(side='left', padx=0)
            l.bind("<Button-1>", self.cycle_beat_click_sound)
    
    
    def add_tempo_text(self):
        # Add "empty" seven segment text underneath the tempo text
        self.tempo_bg_text = self.tempo_canvas.create_text((self.tempo_canvas_width/2)-100,
                                                            10 + (self.tempo_canvas_height/2),
                                                            anchor=tk.CENTER,
                                                            text="888",
                                                            font=("7 Segment", self.tempo_font_size),
                                                            fill="#290c0b")
        
        # Add the text to display the tempo
        self.tempo_main_text = self.tempo_canvas.create_text((self.tempo_canvas_width/2)-100,
                                                                10 + (self.tempo_canvas_height/2),
                                                                anchor=tk.CENTER,
                                                                text=str(self.metro.tempo),
                                                                font=("7 Segment", self.tempo_font_size),
                                                                fill="red")
        
    
    def update_tempo_canvas_text(self, new_val):
        # Add a space to the start of the number if it's only 2 digits long
        if len(str(new_val)) == 2:
            new_val = " " + str(new_val)
        
        # Update the tempo value shown with seven segment font
        self.tempo_canvas.itemconfig(self.tempo_main_text, text=new_val)    
    
    
    def add_time_sig_text(self):        
        self.time_sig_text = self.tempo_canvas.create_text((self.tempo_canvas_width/2)+150,
                                                        (self.tempo_canvas_height/2),
                                                        anchor=tk.CENTER,
                                                        text=f"{self.metro.beats_per_bar}/4",
                                                        font=("Seven Segment", self.time_sig_font_size),
                                                        fill="red")
        
    
    def update_time_sig_text(self, new_val):
        # Update the time signature value shown with seven segment font
        self.tempo_canvas.itemconfig(self.time_sig_text, text=new_val)
    
    
    def decrement_coloured_beat_labels(self):
        self.metro.decrease_beats_per_bar()
        self.update_time_sig_text(new_val=f"{self.metro.beats_per_bar}/4")
        
        # Hide some labels to leave only the required number visible
        for i in range(len(self.labels)-1, self.metro.beats_per_bar-1, -1):
            self.labels[i].pack_forget()
            
            
    def increment_coloured_beat_labels(self):
        self.metro.increase_beats_per_bar()
        self.update_time_sig_text(new_val=f"{self.metro.beats_per_bar}/4")
        
        # Make the requested number of labels visible
        for i in range(self.metro.beats_per_bar):
            self.labels[i].pack(side='left', padx=0)
        

    def cycle_beat_click_sound(self, event):
        '''
        This method is bound to the BeatSoundLabel instances in the GUI via 
        the left mouse click.
        
        When a BeatSoundLabel is clicked, its appearance is changed and
        the click sound associated with that beat number is updated to reflect
        this change in appearance.
        
        '''
        # Cyclically increment the click_sound_index for the label
        event.widget.click_sound_index = (event.widget.click_sound_index + 1) % 3
        # Use the new click_sound_index value to retrieve the new image to be shown
        new_image = self.img_dict[self.beat_state_array[event.widget.label_list_index]][event.widget.click_sound_index]
        event.widget.config(image=new_image)
        
        # Update the index_array so we can instruct the metronome to play the correct sound
        self.index_array[event.widget.label_list_index] = event.widget.click_sound_index
        
        # Update the metronome's dictionary that holds the samples to play on each beat
        self.metro.update_beat_sample_dict(self.index_array)
        
        # Debugging print statements
        # print(f"Widget index: {event.widget.click_sound_index}. Label index: {event.widget.label_list_index}")
        # print(self.beat_state_array)
        # print(self.beat_state_array[event.widget.label_list_index])
    
    
    def blank_out_coloured_beat_labels(self):
        '''
        Reset all of the coloured beat/click sound labels to their "off" state.
        This means that none of them will be coloured blue, for the current beat.
        It should be in this state when the metronome is not running.
        '''
        self.beat_state_array = np.array(["off" for i in range(len(self.index_array))])
            
        for i in range(len(self.labels)):
            self.labels[i].config(image=self.img_dict["off"][self.index_array[i]], bg="#a8a8a8")
            
            
    def set_coloured_beat_labels(self, idx=None):
        '''
        A method used to highlight exactly one of the coloured beat labels 
        to indicate the current beat number of the metronome.
        
        '''
        
        # TODO - We can get rid of the method "blank_out_coloured_beat_labels" (DRY)
        # because we can achieve the same thing by calling set_coloured_beat_labels
        # and passing no argument for idx.
        
        # Set all label beat states to "off"
        self.beat_state_array = np.array(["off" for i in range(len(self.index_array))])
        # Set the beat state of label at idx to "on", if specified
        if idx is not None:
            self.beat_state_array[idx] = "on"
            
        # For each label, obtain the correct image from the dictionary so that 
        # it is either highlighted or not, and it has the correct number of
        # "levels" shown, corresponding to the click sound for that beat
        for i in range(len(self.labels)):
            self.labels[i].config(image=self.img_dict[self.beat_state_array[i]][self.index_array[i]], bg="#a8a8a8")
    
    
    def increment_active_beat_label(self):
        # Update beat labels so the label for the current beat is highlighted
        # First, set them all to be "off"
        self.blank_out_coloured_beat_labels()
        
        # Get the index corresponding to the current beat
        if self.metro.current_beat != 0:
            label_idx = self.metro.current_beat - 1
        else:
            label_idx = 0
        
        # Highlight the correct label
        self.set_coloured_beat_labels(idx=label_idx)
    

    def update_beat_number_from_metro(self):
        
        beat_to_show = self.metro.get_current_beat()
        # This is a bit of a hack. Don't display beat 0 - change it to 1
        if beat_to_show == 0:
            beat_to_show = 1

        if self.beat_currently_shown != beat_to_show:
            #print(f"arr: {self.beat_state_array}")
            #print(beat_to_show)
            self.increment_active_beat_label()
            
        self.beat_string_var.set(beat_to_show)
        self.after_loop = self.root.after(10, self.update_beat_number_from_metro)
        
        # Set this for comparison in the next call to check if we increment blue label
        self.beat_currently_shown = beat_to_show
        
    
    def set_new_tempo(self, new_val):
        self.metro.set_new_tempo(new_val)
        self.update_tempo_canvas_text(new_val)
        # Setting the tempo slider value in this way calls this method I think
        # Could use a tk.DoubleVar to prevent this maybe?
        self.tempo_slider.set(new_val)
        # Debugging print       
        # print(f"In set_new_tempo: {self.metro.tempo}")
    
    
    def adjust_tempo(self, adjustment):
        '''
        Make adjustments to the tempo rather than specifying an actual tempo
        value. This is useful for including buttons to move +/- 10 bpm.
        
        This method may also be useful for a speed trainer.
        '''
        # new_tempo = self.metro.tempo + adjustment
        new_tempo = int(self.tempo_slider.get() + adjustment)
        # Debugging print       
        # print(f"In adjust_tempo: {new_tempo}")
        self.set_new_tempo(new_tempo)
    
    
    def start(self):
        if not self.metro.running:
            #print("STARTING...")
            self.metro.start()
            # Update the coloured thing to show the first beat blue
            self.set_coloured_beat_labels(idx=0)
            self.update_beat_number_from_metro()
    
    
    def stop(self):
        if self.metro.running:
            #print("STOPPING...")
            self.metro.stop()
            #print(f"In App stop() method. Metro current_beat: {self.metro.current_beat}")
            self.root.after_cancel(self.after_loop)
            # Reset the beat number and coloured bars
            self.beat_string_var.set("")
            #print(self.beat_state_array)
            self.blank_out_coloured_beat_labels()
            #print(self.beat_state_array)
    
    
    def ui_start_stop(self, event=None):
        if self.metro.running:
            # Stop the metronome and update the button text
            self.stop()
            #self.start_stop_button.config(text="START")
            self.start_stop_button.config(image=self.play_button_image)
        else:
            # Start the metronome and update the button text
            self.start()
            #self.start_stop_button.config(text="STOP")
            self.start_stop_button.config(image=self.stop_button_image)
    
    
    def on_window_closing(self):
        # Stop the metronome when the user closes the window
        self.stop()
        self.root.destroy()
        

m = Metronome(tempo=180, beats_per_bar=4)
a = App(m)
a.root.mainloop()


#%%
# Write the full metronome output to a wav file for analysis in a DAW
full = np.array(m.full_output).reshape(-1)
wavfile.write("metro_output_217_ts_varying.wav", rate=16000, data=full)


