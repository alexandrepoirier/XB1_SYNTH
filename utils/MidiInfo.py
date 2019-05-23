def getOctavesInRange(note, start, stop):
    if note < start or note > stop:
        raise ValueError("'note' must be within specified range")

    res = [note]
    i = 1
    while True:
        oct_up = note + (12 * i)
        if oct_up < stop:
            res.append(oct_up)

        oct_down = note - (12 * i)
        if oct_down > start:
            res.append(oct_down)

        if oct_up > stop and oct_down < start:
            break
        i += 1
    res.sort()
    return res

MIDI_NOTES_MUSICAL_RANGE = (21, 108)
MIDI_NOTES_MAPPING = {"A": getOctavesInRange(21, *MIDI_NOTES_MUSICAL_RANGE),
                      "A#": getOctavesInRange(22, *MIDI_NOTES_MUSICAL_RANGE),
                      "B": getOctavesInRange(23, *MIDI_NOTES_MUSICAL_RANGE),
                      "C": getOctavesInRange(24, *MIDI_NOTES_MUSICAL_RANGE),
                      "C#": getOctavesInRange(25, *MIDI_NOTES_MUSICAL_RANGE),
                      "D": getOctavesInRange(26, *MIDI_NOTES_MUSICAL_RANGE),
                      "D#": getOctavesInRange(27, *MIDI_NOTES_MUSICAL_RANGE),
                      "E": getOctavesInRange(28, *MIDI_NOTES_MUSICAL_RANGE),
                      "F": getOctavesInRange(29, *MIDI_NOTES_MUSICAL_RANGE),
                      "F#": getOctavesInRange(30, *MIDI_NOTES_MUSICAL_RANGE),
                      "G": getOctavesInRange(31, *MIDI_NOTES_MUSICAL_RANGE),
                      "G#": getOctavesInRange(32, *MIDI_NOTES_MUSICAL_RANGE)}

MIDI_NOTES_MAPPING["Bb"] = MIDI_NOTES_MAPPING["A#"]
MIDI_NOTES_MAPPING["Db"] = MIDI_NOTES_MAPPING["C#"]
MIDI_NOTES_MAPPING["Eb"] = MIDI_NOTES_MAPPING["D#"]
MIDI_NOTES_MAPPING["Gb"] = MIDI_NOTES_MAPPING["F#"]
MIDI_NOTES_MAPPING["Ab"] = MIDI_NOTES_MAPPING["G#"]

MIDI_NOTES_ROOTS = {}
for key, item in MIDI_NOTES_MAPPING.items():
    MIDI_NOTES_ROOTS[key] = item[0]
