from metronome_master_GH import Metronome
from metronome_tkinter_master_GH import App


if __name__ == "__main__":
    metronome = Metronome(tempo=150, beats_per_bar=4)
    app = App(metronome)
    app.root.mainloop()