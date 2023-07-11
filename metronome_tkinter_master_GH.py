from metronome_master_GH import Metronome
import tkinter as tk
import numpy as np
import glob
from PIL import Image, ImageTk


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
        
        # Define the main window properties
        self.root = tk.Tk()
        #self.root = tk.Toplevel()
        self.root.title("Metronome")
        main_width = 750
        main_height = 650
        self.root.geometry(f"{main_width}x{main_height}")
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
        self.tempo_canvas_height = 160
        self.tempo_font_size = 60
        self.time_sig_font_size = 60
        
        # Params for coloured beat indicator labels
        self.labels = []
        self.label_width = 80
        self.label_height = 120
        
        self.beat_currently_shown = 0
        self.make_widgets()
        
        self.create_label_image_dict()
        self.populate_label_frame()
        self.set_up_keyboard_bindings()
        
        # Attach the method for handling window closing
        self.root.protocol("WM_DELETE_WINDOW", self.on_window_closing)
         
        # After everything else is set up, make the displayed labels specific to the beats per bar
        for i in range(len(self.labels)-1, self.metro.beats_per_bar-1, -1):
            self.labels[i].pack_forget()
     
        
    
    def set_up_keyboard_bindings(self):
        # Bind the space bar to the ui_start_stop method
        self.root.bind("<space>", self.ui_start_stop)
        # Bind the arrow keys to adjusting the tempo
        self.root.bind("<Left>", lambda event: self.adjust_tempo(-10))
        self.root.bind("<Right>", lambda event: self.adjust_tempo(+10))
        self.root.bind("<Shift-Left>", lambda event: self.adjust_tempo(-5))
        self.root.bind("<Shift-Right>", lambda event: self.adjust_tempo(+5))
        
        self.root.bind("<Up>", lambda event: self.increment_coloured_beat_labels())
        self.root.bind("<Down>", lambda event: self.decrement_coloured_beat_labels())
    
    
    def define_image_filepaths(self):
        # Paths with multiple files for use with glob
        self.on_img_fpath = "./images/on/*.jpg"
        self.off_img_fpath = "./images/off/*.jpg"
        # Paths to specific individual images
        self.play_button_path = "./images/play_button.jpg"
        self.stop_button_path = "./images/stop_button.jpg"
        self.plus_button_path = "./images/plus_button.jpg"
        self.minus_button_path = "./images/minus_button.jpg"
        
        self.minus_5_button_path = "./images/minus_5_button.jpg"
        self.minus_10_button_path = "./images/minus_10_button.jpg"
        self.plus_5_button_path = "./images/plus_5_button.jpg"
        self.plus_10_button_path = "./images/plus_10_button.jpg"
    
    
    def load_images(self):
        self.play_button_image = ImageTk.PhotoImage(Image.open(self.play_button_path))
        self.stop_button_image = ImageTk.PhotoImage(Image.open(self.stop_button_path))
        
        # Values for resizing buttons
        new_width = 80
        new_height = int(0.676 * new_width)
        self.plus_button_image = ImageTk.PhotoImage(Image.open(self.plus_button_path).resize((new_width, new_height), Image.ANTIALIAS))
        self.minus_button_image = ImageTk.PhotoImage(Image.open(self.minus_button_path).resize((new_width, new_height), Image.ANTIALIAS))
        self.minus_5_button_image = ImageTk.PhotoImage(Image.open(self.minus_5_button_path).resize((new_width, new_height), Image.ANTIALIAS))
        self.minus_10_button_image = ImageTk.PhotoImage(Image.open(self.minus_10_button_path).resize((new_width, new_height), Image.ANTIALIAS))
        self.plus_5_button_image = ImageTk.PhotoImage(Image.open(self.plus_5_button_path).resize((new_width, new_height), Image.ANTIALIAS))
        self.plus_10_button_image = ImageTk.PhotoImage(Image.open(self.plus_10_button_path).resize((new_width, new_height), Image.ANTIALIAS))
    
    
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
        self.add_canvas_text()
                
        self.label_frame = tk.Frame(master=self.root)
        self.label_frame.pack(padx=0, pady=(20,20), fill=None, expand=False)
        
        # Add the text label that will show the current beat
        # beat_label = tk.Label(self.root, fg="red", bg="black", textvariable=self.beat_string_var, font=("arkitech", 48))
        # beat_label.pack()
        
        # Add a slider to control tempo, placed inside its own frame
        self.slider_frame = tk.Frame(master=self.root)
        self.slider_frame.pack()
        
        self.tempo_slider = tk.Scale(master=self.slider_frame,
                                     width=50,
                                     length=490,
                                     showvalue=False,
                                     troughcolor="#575757",
                                     from_=self.metro.min_tempo,
                                     to=self.metro.max_tempo,
                                     orient=tk.HORIZONTAL)
        
        self.tempo_slider.set(self.metro.tempo)
        self.tempo_slider.pack()
        # Attach the command separately to avoid the method getting called
        self.tempo_slider.configure(command=self.set_new_tempo)

        # Put a start/stop button inside a frame. Set image to a play symbol
        self.start_stop_btn_frame = tk.Frame(self.root)
        self.start_stop_btn_frame.pack(pady=(20, 20))
        self.start_stop_button = tk.Button(master=self.start_stop_btn_frame, image=self.play_button_image, highlightthickness=0, bd=0, command=self.ui_start_stop)
        self.start_stop_button.pack()
        
        # Create a frame to pack the tempo/time sig adjustment frames into
        self.adjust_button_frame = tk.Frame(master=self.root, bg='black')
        # Create a frame for each of tempo and time sig adjustment buttons
        self.tempo_adjustment_frame = tk.Frame(master=self.adjust_button_frame, bg='black')
        self.time_sig_adjustment_frame = tk.Frame(master=self.adjust_button_frame, bg='black')
        
        self.adjust_button_frame.pack()
        self.time_sig_adjustment_frame.pack(side=tk.LEFT, padx=(0, 13))
        self.tempo_adjustment_frame.pack(side=tk.LEFT, padx=(13, 0))
                
        time_sig_adjust_title = tk.Label(master=self.time_sig_adjustment_frame, text="BEATS PER BAR", fg="white", bg="black")
        tempo_adjust_title = tk.Label(master=self.tempo_adjustment_frame, text="BEATS PER MINUTE", fg="white", bg="black")
        time_sig_adjust_title.pack()
        tempo_adjust_title.pack()

        # Tempo/time sig adjustment buttons WITH images
        reduce_time_sig_button = tk.Button(master=self.time_sig_adjustment_frame, image=self.minus_button_image, highlightthickness=0, bd=0, command=self.decrement_coloured_beat_labels)
        increase_time_sig_button = tk.Button(master=self.time_sig_adjustment_frame, image=self.plus_button_image, highlightthickness=0, bd=0, command=self.increment_coloured_beat_labels)
        reduce_time_sig_button.pack(side=tk.LEFT)
        increase_time_sig_button.pack(side=tk.LEFT)

        # Add tempo adjustment buttons with images instead of text
        minus_10_button = tk.Button(master=self.tempo_adjustment_frame, image=self.minus_10_button_image, highlightthickness=0, bd=0, command=lambda:self.adjust_tempo(-10))
        minus_5_button = tk.Button(master=self.tempo_adjustment_frame, image=self.minus_5_button_image, highlightthickness=0, bd=0, command=lambda:self.adjust_tempo(-5))
        plus_5_button = tk.Button(master=self.tempo_adjustment_frame, image=self.plus_5_button_image, highlightthickness=0, bd=0, command=lambda:self.adjust_tempo(5))
        plus_10_button = tk.Button(master=self.tempo_adjustment_frame, image=self.plus_10_button_image, highlightthickness=0, bd=0, command=lambda:self.adjust_tempo(10))
        
        minus_10_button.pack(side=tk.LEFT)
        minus_5_button.pack(side=tk.LEFT)
        plus_5_button.pack(side=tk.LEFT)
        plus_10_button.pack(side=tk.LEFT)
        
        
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
        
        
    def populate_label_frame(self):
        '''
        Create a number of BeatSoundLabel objects (as many as self.max_beats_per_bar)
        and add them to a list self.labels. This list will later be used to
        show or hide the appropriate number of BeatSoundLabel objects in the
        GUI, according to self.beats_per_bar.
        '''
        # Build the initial set of BeatSoundLabel objects
        for i, click_idx in enumerate(self.index_array):
            l = BeatSoundLabel(self.label_frame,
                                label_list_index=i,
                                click_sound_index=click_idx,
                                beat_state=self.beat_state_array[i])
            
            l.config(image=self.img_dict[self.beat_state_array[i]][self.index_array[i]], bg="#a8a8a8")
            
            self.labels.append(l)
            l.pack(side='left', padx=0)
            # Bind left mouse click to cycle through sound options for this beat
            l.bind("<Button-1>", self.cycle_beat_click_sound)
    
    
    def add_canvas_text(self):
        '''
        Add text to the canvas to display information about the current tempo
        and time signature.
        '''
        # Display "tempo" title
        self.tempo_title_text = self.tempo_canvas.create_text((50, 30),
                                                              text="Tempo",
                                                                font=("Seven Segment", 14),
                                                                fill="red")
        
        # Display "time signature" title
        self.time_sig_title_text = self.tempo_canvas.create_text((400, 30),
                                                              text="Time Signature",
                                                                font=("Seven Segment", 14),
                                                                fill="red")
        
        
        # Add "empty" seven segment text underneath the tempo text
        self.tempo_bg_text = self.tempo_canvas.create_text((105, 100),
                                                            text="888",
                                                            font=("7 Segment", self.tempo_font_size),
                                                            fill="#3b110f")
        
        # Add the text to display the tempo
        self.tempo_main_text = self.tempo_canvas.create_text((105, 100),
                                                                text=str(self.metro.tempo),
                                                                font=("7 Segment", self.tempo_font_size),
                                                                fill="red")
        
        
        # Time signature background empty text
        time_sig_x_coord = 390
        self.time_sig_text = self.tempo_canvas.create_text((time_sig_x_coord, 100),
                                                        text="8 8",
                                                        font=("7 Segment", self.time_sig_font_size),
                                                        fill="#3b110f")
        
        # Time signature numerical text
        self.time_sig_text = self.tempo_canvas.create_text((time_sig_x_coord, 100),
                                                        text=f"{self.metro.beats_per_bar} 4",
                                                        font=("7 Segment", self.time_sig_font_size),
                                                        fill="red")
        
        # Time sig seven segment slash text
        self.time_sig_slash = self.tempo_canvas.create_text((time_sig_x_coord, 90),
                                                        text="/",
                                                        font=("Seven Segment", self.time_sig_font_size+10),
                                                        fill="red")
        

    def update_tempo_canvas_text(self, new_val):
        '''
        Update the tempo value shown on the canvas. Called when the tempo 
        value is updated.
        '''
        # Add a space to the start of the number if it's only 2 digits long
        if len(str(new_val)) == 2:
            new_val = " " + str(new_val)
        
        # Update the tempo value shown with seven segment font
        self.tempo_canvas.itemconfig(self.tempo_main_text, text=new_val)    
            
    
    def update_time_sig_canvas_text(self, new_val):
        '''
        Update the time signature shown on the canvas. Called when the time
        signature is updated. Note only the top number changes, as the
        note durations are always considered to be quarter notes.
        '''
        # Update the time signature value shown with seven segment font
        self.tempo_canvas.itemconfig(self.time_sig_text, text=new_val)
    
    
    def decrement_coloured_beat_labels(self):
        '''
        TODO - The GUI and metronome should not be coupled like this.
        '''
        self.metro.decrease_beats_per_bar()
        self.update_time_sig_canvas_text(new_val=f"{self.metro.beats_per_bar} 4")
        
        # Hide some labels to leave only the required number visible
        for i in range(len(self.labels)-1, self.metro.beats_per_bar-1, -1):
            self.labels[i].pack_forget()
            
            
    def increment_coloured_beat_labels(self):
        '''
        TODO - The GUI and metronome should not be coupled like this.
        '''
        self.metro.increase_beats_per_bar()
        self.update_time_sig_canvas_text(new_val=f"{self.metro.beats_per_bar} 4")
        
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
        
        The GUI and metronome shouldn't be coupled like this. Have a separate
        Controller class. (to do).
        
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
                    
            
    def set_coloured_beat_labels(self, idx=None):
        '''
        A method used to highlight exactly one of the coloured beat labels 
        to indicate the current beat number of the metronome.
        
        If idx is None, all of the labels are set to the "off" state. This is
        useful for when the metronome is not running.
        
        '''
        
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
        self.set_coloured_beat_labels(idx=None)
        
        # Get the index corresponding to the current beat
        if self.metro.get_current_beat() != 0:
            label_idx = self.metro.get_current_beat() - 1
        else:
            label_idx = 0
        
        # Highlight the correct label
        self.set_coloured_beat_labels(idx=label_idx)
    

    def update_beat_number_from_metro(self):
        '''
        Use the current beat number from the Metronome object to update the
        text label that shows the current beat in the GUI. tkinter's "after"
        method is used here to check for an updated beat number every 10ms.
        There's nothing special about this duration, it just seems to work nicely.
        '''
        
        beat_to_show = self.metro.get_current_beat()
        # This is a bit of a hack. Don't display beat 0 - change it to 1
        if beat_to_show == 0:
            beat_to_show = 1

        if self.beat_currently_shown != beat_to_show:
            self.increment_active_beat_label()
            
        self.beat_string_var.set(beat_to_show)
        self.after_loop = self.root.after(10, self.update_beat_number_from_metro)
        
        # Set this for comparison in the next call to check if we increment blue label
        self.beat_currently_shown = beat_to_show
        
    
    def set_new_tempo(self, new_val):
        # TODO - input validation & decouple GUI from metronome
        
        self.metro.set_new_tempo(new_val)
        self.update_tempo_canvas_text(new_val)
        # Setting the tempo slider value in this way calls this method I think
        # Could use a tk.DoubleVar to prevent this?
        self.tempo_slider.set(new_val)
        # Debugging print       
        # print(f"In set_new_tempo: {self.metro.tempo}")
    
    
    def adjust_tempo(self, adjustment):
        '''
        Make adjustments to the tempo rather than specifying an absolute tempo
        value. This is connected to the buttons to move +/- N bpm.
        '''
        new_tempo = int(self.tempo_slider.get() + adjustment)  
        self.set_new_tempo(new_tempo)
    
    
    def start(self):
        if not self.metro.running:
            self.metro.start()
            # Update the coloured labels to show the first beat blue
            self.set_coloured_beat_labels(idx=0)
            self.update_beat_number_from_metro()
    
    
    def stop(self):
        if self.metro.running:
            self.metro.stop()
            self.root.after_cancel(self.after_loop)
            # Blank out the displayed beat number and the coloured labels
            self.beat_string_var.set("")
            self.set_coloured_beat_labels(idx=None)
    
    
    def ui_start_stop(self, event=None):
        if self.metro.running:
            # Stop the metronome and update the button image
            self.stop()
            self.start_stop_button.config(image=self.play_button_image)
        else:
            # Start the metronome and update the button image
            self.start()
            self.start_stop_button.config(image=self.stop_button_image)
    
    
    def on_window_closing(self):
        # Stop the metronome when the user closes the window
        self.stop()
        self.root.destroy()