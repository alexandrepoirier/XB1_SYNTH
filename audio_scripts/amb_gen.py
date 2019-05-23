if False:
    from pyo import *
    from controller import *
    import effects
    xb1_controller = Controller()
    import utils

# commencer à penser à un facteur CHAOS qui agirait sur le noise et sur le LFO

# BASE SYNTH
# frequency control
rand_freq_lfo = Randi(0.1, 0.5, freq=1)
freq_lfo = Sine(rand_freq_lfo, mul=0.02, add=1)
freq = Sig(xb1_controller.scrub['LX'], mul=1000*freq_lfo, add=30)
spread = Sig(xb1_controller.scrub['LY'], mul=[2, 2.1, 3, 3.1], add=1)

# oscillators
mul_noise = Noise(mul=0.001, add=0.2)
osc1 = LFO(freq=freq*spread, sharp=1, mul=mul_noise)
osc2 = LFO(freq=freq/spread, sharp=1, mul=mul_noise)

# EFFECTS
# random lowpasses
rand_cutoff1 = Randi(min=650, max=[800, 1800, 15000, 12000], freq=[0.3, 0.2])
rand_cutoff2 = Randi(min=650, max=[12000, 800, 15000, 18000], freq=[0.2, 0.3])
moogLP1 = MoogLP(osc1, rand_cutoff1, 0.3)
moogLP2 = MoogLP(osc2, rand_cutoff2, 0.3)

# phaser
delay_time_lfo1 = Sine([0.2, 0.4, 0.3, 0.2]).range(0.001, 0.1)
delay1 = SmoothDelay(moogLP1, delay=delay_time_lfo1, feedback=0.5, mul=0.8)
phase_mix1 = Selector([moogLP1, delay1], voice=xb1_controller.scrub['RX'])
delay_time_lfo2 = Sine([0.4, 0.2, 0.2, 0.3]).range(0.001, 0.1)
delay2 = SmoothDelay(moogLP2, delay=delay_time_lfo2, feedback=0.5, mul=0.8)
phase_mix2 = Selector([moogLP2, delay2], voice=xb1_controller.scrub['RX'])

# oscillator mixdown
osc_mix = Mix([phase_mix1, phase_mix2], voices=2)

# overdrive
overdrive = effects.Waveshaper(osc_mix, gain=2, mul=0.4)

# resonator
roots = [utils.MIDI_NOTES_MAPPING['A'][3], utils.MIDI_NOTES_MAPPING['D'][3], utils.MIDI_NOTES_MAPPING['G'][3],
         utils.MIDI_NOTES_MAPPING['C'][3], utils.MIDI_NOTES_MAPPING['F'][3]]
roots_freqs = [midiToHz(note) for note in roots]
scaleFactor = lambda x:2.**(x/12.)
root_sig = SigTo(roots_freqs[0], time=0.5)
reson_freqs = [root_sig, root_sig*scaleFactor(7), root_sig*scaleFactor(12), root_sig*scaleFactor(16),
               root_sig*scaleFactor(23), root_sig*scaleFactor(28), root_sig*scaleFactor(36)]
reson_freqs += [f*1.02 for f in reson_freqs]

resonator = Resonx(overdrive, freq=reson_freqs, q=9, mul=[0.2, 0.3, 0.4, 0.6, 0.7, 0.9, 1])
resonator_mix = Mix(resonator, voices=2)

# resonator post-fx
resonator_comp = Compress(resonator_mix, thresh=-18, ratio=8)
resonator_drive = effects.Waveshaper(resonator_comp, gain=3)
# resonator verb
#reson_split = BandSplit(resonator_drive, num=4)
reson_verb = WGVerb(resonator_drive, feedback=0.9, cutoff=8000, mul=0.4)

resonator_postfx_mix = Mix([resonator_drive, reson_verb], voices=2)

reson_bal = Selector([overdrive, resonator_postfx_mix], voice=xb1_controller.scrub['RY'])

# FINAL MIX TO OUTPUT
main_out = Mix([reson_bal], voices=2).out()

osc_type_map = {0: "Saw up", 1: "Saw down", 2: "Square", 3: "Triangle", 4: "Pulse", 5: "Bipolar pulse",
                6: "Sample and hold", 7: "Modulated Sine"}

wave_type = 0
def cycleWaveShape():
    global wave_type
    wave_type = (wave_type + 1) % 8
    osc1.setType(wave_type)
    osc2.setType(wave_type)
    logAndPrint("Osc Waveform Type : ", osc_type_map[wave_type])

root_index = 0
def cycleRoots():
    global root_index
    root_index = (root_index + 1) % len(roots)
    root_sig.value = roots_freqs[root_index]
    logAndPrint("Changing resonator's base frequency : {:.2f}".format(roots_freqs[root_index]))

def onDPad(value):
    # value is a list of two ints that can be -1, 0 or 1
    # -1 means left/down and 1 means right/up. 0 is when nothing is pressed
    # value[0] is horizontal axis, value[1] is the vertical axis
    if value[0] == -1: # left
        cycleWaveShape()
    elif value[0] == 1: # right
        cycleRoots()
    if value[1] == -1: # down
        pass
    elif value[1] == 1: # up
        pass
xb1_controller.dpad.setCallback(onDPad)
