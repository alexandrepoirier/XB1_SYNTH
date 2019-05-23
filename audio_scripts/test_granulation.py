if False:
    from pyo import *
    from controller import *
    import effects
    xb1_controller = Controller()

# GRANULTAOR
hann = HannTable()
table = NewTable(1, 2)
pos_jitter = Noise(Sig(xb1_controller.scrub['LY'], mul=server.getSamplingRate()/2., add=8000))
pos = Sig(xb1_controller.scrub['LX'], mul=table.getSize(), add=pos_jitter)
abs_dur = Sig(xb1_controller.scrub['RY'], mul=0.1, add=0.15)
jitter_dur = Sig(xb1_controller.scrub['LY'], mul=0.05)
dur = Noise(jitter_dur, abs_dur)

granul = Granulator(table, env=hann, pos=pos, dur=dur, basedur=0.2, grains=25, mul=0.5)


# SYNTH
osc = LFO([80,81])
vocoder = Vocoder(granul, osc)

main_out = Mix(vocoder, voices=2).out()

def fileSelectionCallback(path):
    granul.setPos(0)
    table = SndTable(path)
    granul.setTable(table)
    pos.mul = table.getSize()
    granul.setPos(pos)


SCRUB_STATE = True
def togglePositionScrub():
    global SCRUB_STATE

    if SCRUB_STATE:
        print("Disable scrub")
        pos.value = xb1_controller.scrub['LX'].get()
    else:
        print("Enable scrub")
        pos.value = xb1_controller.scrub['LX']

    SCRUB_STATE = not SCRUB_STATE
xb1_controller.buttons['LS'].setOnPressCallback(togglePositionScrub)


def onDPad(value):
    # value is a list of two ints that can be -1, 0 or 1
    # -1 means left/down and 1 means right/up. 0 is when nothing is pressed
    # value[0] is horizontal axis, value[1] is the vertical axis
    if value[0] == -1: # left
        pass
    elif value[0] == 1: # right
        pass
    if value[1] == -1: # down
        pass
    elif value[1] == 1: # up
        pass
xb1_controller.dpad.setCallback(onDPad)
