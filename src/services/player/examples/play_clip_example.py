import fluidsynth
import json
import os
from time import sleep

from src.services.player.midi_player import play_clip

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
    play_clip(clip_data, sf2_path="/Users/chrislomeli/Source/__DATA__/FluidR3_GM.sf2", bpm=120, loop=False)
