import music21 as m21
import mido

score = m21.stream.Score()
part = m21.stream.Part()
bass_part = m21.stream.Part()

voice1 = m21.stream.Voice()
voice2 = m21.stream.Voice()
bass_voice = m21.stream.Voice()

notes = ['C4', 'D4', 'E4', 'F4', 'G4' , 'A4', 'B4', 'C5']
for note in notes:
    melody_note = m21.note.Note(note);
    harmony_note = melody_note.transpose(-8)
    voice1.append(melody_note)
    voice2.append(harmony_note)

    bass_note = m21.note.Note(note);
    bass_note.octave -= 2
    bass_voice.append(bass_note)

# Create a measure and insert both voices at offset 0
measure = m21.stream.Measure()
measure.insert(0, voice1)
measure.insert(0, voice2)

bass_measure = m21.stream.Measure()
bass_measure.insert(0, bass_voice)
bass_part.append(bass_measure)

part.append(measure)
score.insert(0, part)
score.insert(0, bass_part)
score.write('midi', fp='output.mid')

# Play with mido
mid = mido.MidiFile('output.mid')
port = mido.open_output()
for msg in mid.play():
    port.send(msg)