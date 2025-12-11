import fluidsynth
import json
import os
from time import sleep

from src.services.player.midi_builder import MidiClipPlayer


#from midi_clip_player import MidiClipPlayer  # assuming you saved the class above


def play_clip(clip_data, sf2_path=None, bpm=120, loop=False):
    """
    Play a DSL clip using pyFluidSynth in one call.

    clip_data: dict loaded from your DSL JSON
    sf2_path: path to .sf2 SoundFont file; defaults to FluidR3 GM if None
    bpm: tempo
    loop: whether to loop the clip
    test = fluidsynth.__file__"""

    test = fluidsynth.__file__
    # Default SoundFont path
    if sf2_path is None:
        sf2_path = "FluidR3_GM.sf2"  # adjust this path to wherever your SF2 is
        if not os.path.isfile(sf2_path):
            raise FileNotFoundError(f"SoundFont not found: {sf2_path}")

    # Start pyFluidSynth
    fs = fluidsynth.Synth()
    fs.start(driver="coreaudio")  # Mac: "coreaudio"; Windows: "dsound"; Linux: "alsa"
    sfid = fs.sfload(sf2_path)
    fs.program_select(0, sfid, 0, 0)  # channel 0, bank 0, preset 0

    try:
        # Create MidiClipPlayer
        player = MidiClipPlayer(fluidsynth=fs, bpm=bpm, loop=loop)
        player.play_dsl_clip(clip_data)
    finally:
        # Cleanup/Users/chrislomeli/Source/PycharmProjects/OSC/src/services/player
        fs.delete()


