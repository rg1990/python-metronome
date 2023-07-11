# Sample-Accurate Desktop Metronome Application
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

This is a high-precision desktop metronome application developed in Python. The application maintains timing accuracy to within one audio sample and offers a simple, user-friendly graphical interface.

## Features

- High-precision timing: The metronome is accurate to within one audio sample, due to its active drift error compensation.
- Tempo customisation: Users can adjust the tempo of the metronome within the range 10-350 beats per minute.
- Time signature customisation: Users can vary the number of beats per bar, enabling them to practice in different time signatures.
- Adjustments during playback: Adjustments to the tempo and/or time signature during playback are handled smoothly, minimising interruptions.
- Visual and auditory cues: The metronome provides both visual and auditory cues to help users stay on beat. It generates a click sound and also displays an animated visual indicator synchronised with the beat.
- Beat-specific sounds: For every beat in the bar, the click sound can be chosen from **accented**, **regular**, or **silent**, allowing for varied click patterns.

![metronome_example](https://github.com/rg1990/python-metronome/assets/70291897/506adb84-6e0f-4796-afd1-4f124832152b)
(Left: metronome in 'stopped' state. Right: metronome in 'playing' state, with customised beat pattern and visual cue (blue) highlighting current beat.)


![metronome_drift_without_correction](https://github.com/rg1990/python-metronome/assets/70291897/4224202b-bf8b-4d2e-922f-325c4d328a4e)
(Comparison of metronome outputs with and without active drift correction applied, highlighting the drift error that accumulates after a short time. Metronome outputs were examined and verified using the [REAPER DAW](https://www.reaper.fm/).)

## Requirements

- Python 3.x: The application is developed using Python, so ensure you have Python 3.x installed on your system.
- sounddevice library: Install the "sounddevice" library to handle the audio components of the metronome. You can install it using the following command:

  ```bash
  pip install sounddevice
  ```

- tkinter library: The graphical user interface (GUI) components are developed using the "tkinter" library, which is usually included with Python installations.
- Other requirements found in `requirements.txt`

## Getting Started

1. Clone this repository to your local machine or download the source code as a ZIP file.
2. Ensure you have the necessary dependencies installed as mentioned in the Requirements section.
3. Open a terminal or command prompt and navigate to the project directory.
4. Run the following command to start the metronome application:

   ```bash
   python main.py
   ```

5. The metronome application window should open, allowing you to start/stop the metronome, and change the tempo and time signature.

## Usage

- Starting/Stopping: Click the "Play" button to start the metronome. Click the "Stop" button to stop the metronome. The space bar can also be used.
- Tempo control: Adjust the tempo using the slider, the buttons or the arrow keys (left and right).
- Beats per bar control: Set the desired number of beats per bar using the buttons or arrow keys (up and down).
- Customisable beat sounds: Click on the coloured beat indicators to cycle through the click sound options for each beat in the bar.


## To Do / Future Development
To do:
- Decouple the GUI and metronome code. Perhaps create a Controller class and build using a model-view-controller architecture.
- ~~Implement input validation for tempo change buttons to ensure tempo stays within range.~~

Future:
- Speed trainer feature: Schedule tempo increases within a specified tempo range, every user-specified number of bars.
- Randomly silence beats: In each bar, select a random set of beats for which the click be silent. Help develop the user's internal timing.


## Contributing

Contributions to this project are welcome. If you have any suggestions, bug fixes, or new features to add, please follow these steps:

1. Fork the repository.
2. Create a new branch for your feature or bug fix.
3. Make your changes and test thoroughly.
4. Commit your changes and push your branch to your forked repository.
5. Submit a pull request, explaining your changes in detail and providing any necessary documentation.

## Licence

This project is licensed under the [MIT Licence](https://opensource.org/licenses/MIT).


If you encounter any issues or have any questions, please feel free to open an issue in the repository.
