from metronome_master_GH import Metronome
from metronome_tkinter_master_GH import App


metronome = Metronome(tempo=180, beats_per_bar=4)
app = App(metronome)
app.root.mainloop()