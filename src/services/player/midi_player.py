import fluidsynth
import json
import os
from time import sleep
from midi_clip_player import MidiClipPlayer  # assuming you saved the class above


def play_clip(clip_data, sf2_path=None, bpm=120, loop=False):
    """
    Play a DSL clip using pyFluidSynth in one call.

    clip_data: dict loaded from your DSL JSON
    sf2_path: path to .sf2 SoundFont file; defaults to FluidR3 GM if None
    bpm: tempo
    loop: whether to loop the clip
    """
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
        # Cleanup
        fs.delete()


# === Example usage ===
if __name__ == "__main__":
    # Load a DSL clip JSON
    clip_json = """
    {
      "id":1,"name":"test-clip","track_name":"lead",
      "bars":[{"id":1,"clip_id":1,"bar_index":0,
        "velocity_curve":[{"time":0,"value":90},{"time":4,"value":100}],
        "cc":null,"pitch_bend_curve":null,"aftertouch_curve":null,"pedal_events":null,
        "metadata":null,
        "notes":[
          {"id":1,"clip_bar_id":1,"pitch":60,"start_beat":0.0,"duration_beats":1.0,"is_rest":false},
          {"id":2,"clip_bar_id":1,"pitch":64,"start_beat":1.0,"duration_beats":1.0,"is_rest":false}
        ]
      }]
    }
    """
    clip_data = json.loads(clip_json)

    # Play the clip
    play_clip(clip_data, sf2_path="FluidR3_GM.sf2", bpm=120, loop=False)
