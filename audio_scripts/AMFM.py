#/////////////////////////////
# AUDIO OBJECTS SETUP
#/////////////////////////////

midi_notes = [i for i in range(128)]

# LY -> modulator ; RY -> carrier
snap_LY = Snap(xb1_controller.sticks['LY'], midi_notes, scale=1)
snap_RY = Snap(xb1_controller.sticks['RY'], midi_notes, scale=1)
# [end AUDIO OBJECTS SETUP]



#/////////////////////////////
# ARPEGGIATOR
#/////////////////////////////

# 12 note/oct. factor calculation
scaleFactor = lambda x:2.**(x/12.)
arp_scale = [1, scaleFactor(7), scaleFactor(12), scaleFactor(19), scaleFactor(24), scaleFactor(31)]

# enveloppe table for everyone
env_table = LinTable([(0, 0.0), (820, 1.0), (1600, 0.8), (7300, 0.8), (8192, 0.0)], size=8192)

# periodic impulses
tempo = Sig(1, mul=140, add=20)
tempo_time = 1 / (tempo / 60) / 4
periodic_trigger = Metro(tempo_time).play()
note_length = Sig(0.5, mul=.7, add=0.01)
periodic_env = TrigEnv(periodic_trigger, env_table, dur=note_length)

# random impulses
cloud_density = Sig(0.5, mul=49, add=1)
cloud_trigger = Cloud(density=cloud_density, poly=1).play()
cloud_env = TrigEnv(cloud_trigger, env_table, dur=note_length)

# scattered impulses
scatter_speed = Sig(0.5, mul=-4, add=5)
scatter_metro = Metro(scatter_speed).play()
burst_trigger = TrigBurst(scatter_metro, time=0.2, count=50, expand=0.94, ampfade=0.95)
burst_note_length_factor = Sig(0.5, mul=0.9, add=0.1)
burst_env = TrigEnv(burst_trigger, env_table, dur=burst_trigger["dur"]*burst_note_length_factor, mul=burst_trigger["amp"])

# Euclidian impulses
def onOnsetsChange():
    euclidian_trigger.setOnsets(int(euclidian_onsets_snap.get()))

euclidian_onsets = Sig(0.5, mul=12, add=3)
euclidian_onsets_snap = Snap(euclidian_onsets, choice=[3,5,7,9,11,13,15])
euclide_change_detect = Change(euclidian_onsets_snap)
euclide_change_func = TrigFunc(euclide_change_detect, onOnsetsChange)
euclidian_trigger = Euclide(time=tempo_time, taps=16, onsets=3, poly=1).play()
euclidian_env = TrigEnv(euclidian_trigger, table=env_table, dur=euclidian_trigger['dur'], mul=euclidian_trigger['amp'])

# master impulse object
env_port = Port(periodic_env, risetime=.001, falltime=.001)

rand_arp = TrigChoice(periodic_trigger, choice=arp_scale)
seq_arp = Iter(periodic_trigger, choice=arp_scale)
arperggiator = Port(seq_arp, risetime=.001, falltime=.001)
# [end ARPEGGIATOR]



#/////////////////////////////
# AUDIO SIGNAL CHAIN
#/////////////////////////////
modulator_freq = Sig(100)
modulator_mul = Sig(1, mul=0.2)
carrier_freq = Sig(100, mul=[1,1.01])
carrier_mul = Sig(1, mul=0.2)

modulator = LFO(freq=modulator_freq, mul=modulator_mul)
FM_carrier = LFO(freq=carrier_freq * modulator, mul=carrier_mul)
AM_carrier = LFO(freq=carrier_freq, mul=carrier_mul * modulator)
voice_selector = SigTo(0)
carrier_selector = Selector([FM_carrier, AM_carrier], voice=voice_selector)

osc_mix = Mix([carrier_selector, carrier_selector], voices=2)

lp_freq = Sig(22000)
lp_freq_port = Port(lp_freq, risetime=0.5, falltime=0.5, init=lp_freq.value)
lp_filter = MoogLP(osc_mix, freq=lp_freq_port, res=1)
hp_freq = Sig(20)
hp_freq_port = Port(hp_freq, risetime=0.5, falltime=0.5, init=hp_freq.value)
hp_filter = Biquadx(lp_filter, freq=hp_freq_port, q=1.5, type=1)

overdrive = effects.Waveshaper(hp_filter, gain=xb1_controller.analysis['LXVel']+0.68)
pan = effects.FreeMic(overdrive, xaxis=xb1_controller.sticks['RX'], zaxis=xb1_controller.sticks['RY'])
pan_selector = Selector([overdrive, pan], voice=xb1_controller.triggers['RT'])

send1 = Sig(pan_selector, mul=xb1_controller.triggers['LT'])
#send2 = Sig(overdrive, mul=xb1_controller.triggers['LT'])

delay_time = Scale(xb1_controller.sticks['RX'], outmin=[0.001, 0.0015], outmax=1, exp=4)


delay = SmoothDelay(send1, delay=delay_time, feedback=xb1_controller.sticks['RY'], mul=0.6)
rev = Freeverb(send1, size=xb1_controller.sticks['LX'], damp=xb1_controller.sticks['LY'], bal=1, mul=.3)

main_out = Compress(input=Mix([pan_selector, delay, rev], voices=2),
                     thresh=-14, ratio=20, knee=1).out()

# [end AUDIO SIGNAL CHAIN]



#/////////////////////////////
# ASSIGNING CONTROLLER BUTTONS
#/////////////////////////////
def toggleModOscFreqEdit():
    if xb1_controller.buttons['X'].getState():
        logAndPrint("Modulator Osc Freq Edit : On")
        xb1_controller.sticks['LY'].setOutMin(0)
        xb1_controller.sticks['LY'].setOutMax(72)
        modulator_freq.value = snap_LY
    else:
        logAndPrint("Modulator Osc Freq Edit : Off")
        modulator_freq.value = snap_LY.get()
        xb1_controller.sticks['LY'].setOutMin(0)
        xb1_controller.sticks['LY'].setOutMax(1)
xb1_controller.buttons['X'].setMode(1)
xb1_controller.buttons['X'].setOnReleaseCallback(toggleModOscFreqEdit)


def toggleCarrierOscFreqEdit():
    if xb1_controller.buttons['B'].getState():
        logAndPrint("Carrier Osc Freq Edit : On")
        pan.zaxis = xb1_controller.sticks['RY'].get()
        delay.feedback = xb1_controller.sticks['RY'].get()
        xb1_controller.sticks['RY'].setOutMin(24)
        xb1_controller.sticks['RY'].setOutMax(108)
        carrier_freq.value = snap_RY
    else:
        logAndPrint("Carrier Osc Freq Edit : Off")
        carrier_freq.value = snap_RY.get()
        xb1_controller.sticks['RY'].setOutMin(0)
        xb1_controller.sticks['RY'].setOutMax(1)
        pan.zaxis = xb1_controller.sticks['RY']
        delay.feedback = xb1_controller.sticks['RY']
xb1_controller.buttons['B'].setMode(1)
xb1_controller.buttons['B'].setOnReleaseCallback(toggleCarrierOscFreqEdit)


def oscillatorsMulEdit(state):
    if state:
        logAndPrint("Osc Volumes Edit : On")
        rev.size = xb1_controller.sticks['LX'].get()
        rev.damp = xb1_controller.sticks['LY'].get()
        modulator_mul.value = xb1_controller.sticks['LX']
        modulator.add = 1 - xb1_controller.sticks['LX']
        pan.xaxis = xb1_controller.sticks['RX'].get()
        delay.delay = delay_time.get()
        carrier_mul.value = xb1_controller.sticks['RX']
    else:
        logAndPrint("Osc Volumes Edit : Off")
        modulator_mul.value = xb1_controller.sticks['LX'].get()
        modulator.add = 1 - xb1_controller.sticks['LX'].get()
        carrier_mul.value = xb1_controller.sticks['RX'].get()
        pan.xaxis = xb1_controller.sticks['RX']
        delay.delay = delay_time
        rev.size = xb1_controller.sticks['LX']
        rev.damp = xb1_controller.sticks['LY']
xb1_controller.buttons['LB'].setMode(0)
xb1_controller.buttons['LB'].setCallback(oscillatorsMulEdit)


def oscillatorsSharpEdit(state):
    if state:
        logAndPrint("Osc Sharp Factor Edit : On")
        rev.size = xb1_controller.sticks['LX'].get()
        rev.damp = xb1_controller.sticks['LY'].get()
        modulator.sharp = xb1_controller.sticks['LX']
        pan.xaxis = xb1_controller.sticks['RX'].get()
        delay.delay = delay_time.get()
        AM_carrier.sharp = xb1_controller.sticks['RX']
        FM_carrier.sharp = xb1_controller.sticks['RX']
    else:
        logAndPrint("Osc Sharp Factor Edit : Off")
        modulator.sharp = xb1_controller.sticks['LX'].get()
        AM_carrier.sharp = xb1_controller.sticks['RX'].get()
        FM_carrier.sharp = xb1_controller.sticks['RX'].get()
        pan.xaxis = xb1_controller.sticks['RX']
        delay.delay = delay_time
        rev.size = xb1_controller.sticks['LX']
        rev.damp = xb1_controller.sticks['LY']
xb1_controller.buttons['RB'].setMode(0)
xb1_controller.buttons['RB'].setCallback(oscillatorsSharpEdit)


mod_type = None
def toggleAMFM():
    global mod_type
    if xb1_controller.buttons['A'].getState():
        mod_type = 'AM'
        logAndPrint('Mode : AM')
        voice_selector.value = 1
    else:
        mod_type = 'FM'
        logAndPrint('Mode : FM')
        voice_selector.value = 0
xb1_controller.buttons['A'].setMode(1)
xb1_controller.buttons['A'].setOnReleaseCallback(toggleAMFM)
toggleAMFM() # init


osc_type_map = {0: "Saw up", 1: "Saw down", 2: "Square", 3: "Triangle", 4: "Pulse", 5: "Bipolar pulse",
                6: "Sample and hold", 7: "Modulated Sine"}


modulator_type = 0
def cycleWaveShapeMod():
    global modulator_type
    modulator_type = (modulator_type + 1) % 8
    modulator.setType(modulator_type)
    logAndPrint("Modulator Osc Type : ", osc_type_map[modulator_type])


carrier_type = 0
def cycleWaveShapeCarrier():
    global carrier_type
    carrier_type = (carrier_type + 1) % 8
    AM_carrier.setType(carrier_type)
    FM_carrier.setType(carrier_type)
    logAndPrint("Carrier Osc type : ", osc_type_map[carrier_type])


arp_modes = ["sequential", "random"]
arp_mode = 0
def changeArpeggiatorMode():
    global arp_mode
    arp_mode = (arp_mode + 1) % len(arp_modes)

    if arp_mode == 0:
        arperggiator.input = seq_arp
    elif arp_mode == 1:
        arperggiator.input = rand_arp
    logAndPrint("Arpeggiator mode : ", arp_modes[arp_mode])


env_modes = ["periodic", "scattered", "random", "euclidian"]
env_mode = 0
def changeEnveloppeMode():
    global env_mode, rand_arp, seq_arp
    env_mode = (env_mode + 1) % len(env_modes)

    if env_mode == 0:
        env_port.input = periodic_env
        rand_arp.input = periodic_trigger
        seq_arp.input = periodic_trigger
    elif env_mode == 1:
        env_port.input = burst_env
        rand_arp.input = burst_trigger
        seq_arp.input = burst_trigger
    elif env_mode == 2:
        env_port.input = cloud_env
        rand_arp.input = cloud_trigger
        seq_arp.input = cloud_trigger
    elif env_mode == 3:
        env_port.input = euclidian_env
        rand_arp.input = euclidian_trigger
        seq_arp.input = euclidian_trigger
    logAndPrint("Enveloppe mode : ", env_modes[env_mode])


def onDPad(value):
    # value is a list of two ints that can be -1, 0 or 1
    # -1 means left/down and 1 means right/up. 0 is when nothing is pressed
    # value[0] is horizontal axis, value[1] is the vertical axis
    if value[0] == -1: # left
        cycleWaveShapeMod()
    elif value[0] == 1: # right
        cycleWaveShapeCarrier()
    if value[1] == -1: # down
        changeEnveloppeMode()
    elif value[1] == 1: # up
        changeArpeggiatorMode()
xb1_controller.dpad.setCallback(onDPad)


def toggleArpeggiatorMod():
    if xb1_controller.buttons['LS'].getState():
        logAndPrint("Modulator Arppegiator On")
        modulator.freq = modulator_freq * arperggiator
    else:
        logAndPrint("Modulator Arppegiator Off")
        modulator.freq = modulator_freq
xb1_controller.buttons['LS'].setMode(1)
xb1_controller.buttons['LS'].setOnReleaseCallback(toggleArpeggiatorMod)


def toggleArpeggiatorCarrier():
    if xb1_controller.buttons['RS'].getState():
        logAndPrint("Carrier Arppegiator On")
        AM_carrier.freq = carrier_freq * arperggiator
        FM_carrier.freq = carrier_freq * modulator * arperggiator
    else:
        logAndPrint("Carrier Arppegiator Off")
        AM_carrier.freq = carrier_freq
        FM_carrier.freq = carrier_freq * modulator
xb1_controller.buttons['RS'].setMode(1)
xb1_controller.buttons['RS'].setOnReleaseCallback(toggleArpeggiatorCarrier)


arp_env_state = False
def toggleArpeggiatorEnvelope():
    global arp_env_state
    arp_env_state = not arp_env_state

    if arp_env_state:
        logAndPrint("Arpeggiator Envelope : On")
        osc_mix.mul = env_port
    else:
        logAndPrint("Arpeggiator Envelope : Off")
        osc_mix.mul = 1
xb1_controller.registerCombination(["LS", "RS"], toggleArpeggiatorEnvelope)


def toggleArpeggiatorEdit():
    if xb1_controller.buttons['Y'].getState():
        logAndPrint("Arppegiator Edit : On")
        # remove previous mappings
        rev.size = xb1_controller.sticks['LX'].get()
        rev.damp = xb1_controller.sticks['LY'].get()
        pan.xaxis = xb1_controller.sticks['RX'].get()
        delay.delay = delay_time.get()

        # create new mappings
        tempo.value = xb1_controller.sticks['LX']
        cloud_density.value = xb1_controller.sticks['LX']
        scatter_speed.value = xb1_controller.sticks['LX']
        euclidian_onsets.value = xb1_controller.sticks['RX']
        note_length.value = xb1_controller.sticks['RX']
        burst_note_length_factor.value = xb1_controller.sticks['RX']
    else:
        logAndPrint("Arppegiator Edit : Off")
        # remove mappings from this function
        tempo.value = xb1_controller.sticks['LX'].get()
        cloud_density.value = xb1_controller.sticks['LX'].get()
        scatter_speed.value = xb1_controller.sticks['LX'].get()
        euclidian_onsets.value = xb1_controller.sticks['RX'].get()
        note_length.value = xb1_controller.sticks['RX'].get()
        burst_note_length_factor.value = xb1_controller.sticks['RX'].get()

        # put back previous mappings
        rev.size = xb1_controller.sticks['LX']
        rev.damp = xb1_controller.sticks['LY']
        pan.xaxis = xb1_controller.sticks['RX']
        delay.delay = delay_time
xb1_controller.buttons['Y'].setMode(1)
xb1_controller.buttons['Y'].setOnReleaseCallback(toggleArpeggiatorEdit)


LPF_state = False
LPF_freq = 3000
def toggleLPF():
    global LPF_state
    LPF_state = not LPF_state

    if LPF_state:
        logAndPrint("LPF On")
        lp_freq.value = LPF_freq
        lp_filter.res = 1
    else:
        logAndPrint("LPF Off")
        lp_freq.value = 22000
        lp_filter.res = 0
xb1_controller.registerCombination(["X", "A"], toggleLPF)


def LPFUp():
    global LPF_freq
    LPF_freq *= 1.1
    LPF_freq = 22000 if LPF_freq > 22000 else LPF_freq

    logAndPrint("Setting LPF cutoff to {:.2f}Hz".format(LPF_freq))
    lp_freq.value = LPF_freq
xb1_controller.buttons['X'].setOnHoldCallback(LPFUp, True)


def LPFDown():
    global LPF_freq
    LPF_freq *= 0.9
    LPF_freq = 500 if LPF_freq < 500 else LPF_freq

    logAndPrint("Setting LPF cutoff to {:.2f}Hz".format(LPF_freq))
    lp_freq.value = LPF_freq
xb1_controller.buttons['A'].setOnHoldCallback(LPFDown, True)


HPF_state = False
HPF_freq = 500
def toggleHPF():
    global HPF_state
    HPF_state = not HPF_state

    if HPF_state:
        logAndPrint("HPF On")
        hp_freq.value = HPF_freq
        hp_filter.q = 1.5
    else:
        logAndPrint("HPF Off")
        hp_freq.value = 20
        hp_filter.q = 1
xb1_controller.registerCombination(["Y", "B"], toggleHPF)


def HPFUp():
    global HPF_freq, HPF_state
    HPF_freq *= 1.1
    HPF_freq = 1000 if HPF_freq > 1000 else HPF_freq

    logAndPrint("Setting HPF cutoff to {:.2f}Hz".format(HPF_freq))
    if HPF_state:
        hp_freq.value = HPF_freq
xb1_controller.buttons['Y'].setOnHoldCallback(HPFUp, True)


def HPFDown():
    global HPF_freq, HPF_state
    HPF_freq *= 0.9
    HPF_freq = 20 if HPF_freq < 20 else HPF_freq

    logAndPrint("Setting HPF cutoff to {:.2f}Hz".format(HPF_freq))
    if HPF_state:
        hp_freq.value = HPF_freq
xb1_controller.buttons['B'].setOnHoldCallback(HPFDown, True)
# [end ASSIGNING CONTROLLER BUTTONS]
