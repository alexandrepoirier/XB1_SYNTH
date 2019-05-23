from pyo import *
import random

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



class Impulse:
    def __init__(self, freqs, mul=1.0):
        self._freqs = freqs

        self._adsr = Adsr(dur=0.5)
        self._osc = LFO(sharp=1, type=0, mul=self._adsr)
        self._lpf = MoogLP(self._osc, res=0.2)
        self._delay = Delay(self._lpf, maxdelay=0.1, mul=mul)

    def play(self, randomize=True):
        if randomize:
            self.randomizeParams()
        self._adsr.play()

    def out(self, chnl=0):
        self._delay.out(chnl=chnl)

        return self

    def stop(self):
        self._adsr.stop()
        self._delay.stop()
        self._osc.stop()
        self._lpf.stop()

    def randomizeParams(self):
        self._adsr.mul = random.random()
        self._osc.freq = self._freqs[random.randint(0, len(self._freqs) - 1)]
        self._lpf.freq = random.uniform(1000, 16000)
        self._delay.delay = random.uniform(0.001, 0.1)
        self._delay.feedback = random.uniform(0.5, 0.9)

    def setMul(self, value):
        self._delay.mul = value


s = Server(sr=48000).boot()

chord = ["Ab", "C", "Eb", "G"] #Ab M7
freq_pool = [midiToHz(freq) for note in chord for freq in MIDI_NOTES_MAPPING[note]]
freq_pool.sort()

num_osc = 50
osc_array = []

for i in range(num_osc):
    osc_array.append(Impulse(freq_pool, mul=0.1))
    osc_array[-1].out(i%2)

def playNote():
    osc_array[int(urn.get())].play()

urn = Urn(num_osc-1, freq=2)
change = Change(urn)
trigfunc = TrigFunc(change, playNote)

s.gui(locals())
