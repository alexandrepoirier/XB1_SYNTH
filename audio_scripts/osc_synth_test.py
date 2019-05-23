#!/usr/bin/env python
# encoding: utf-8


from pyo import *
import sys

# Globals
CONTROLLER_ROOT_ADDRESS = '/XB1'
ANALYSIS_ROOT_ADDRESS = '/ANA'
BUTTONS_ADDRESS = '/btn'
CONTINUOUS_INPUTS_ADDRESS = '/cts'
DEBUG = False # prints osc data received

class Button:
    def __init__(self, callback=None):
        if callback:
            self._callback = callback
        else:
            self._callback = lambda: print("Button at {} pressed.".format(hex(id(self))))
        self._value = 0
    
    def set(self, value):
        if value != self._value:
            self._value = value
            if value:
                self._callback()


class DPad:
    def __init__(self, callback=None):
        if callback:
            self._callback = callback
        else:
            self._callback = lambda x: print("D-Pad value : {}".format(x))
        self._value = [0,0]

    def set(self, value):
        if value != self._value:
            self._value = value
            if value:
                self._callback(value)


def convertArgs(args, type):
    if len(args) > 1:
        if type == "i":
            return [int(arg) for arg in args]
        if type == "f":
            return [float(arg) for arg in args]
    else:
        if type == "i":
            return int(args[0])
        if type == "f":
            return float(args[0])


s = Server()
#s.setInputDevice(7)
#s.setOutputDevice(9)
s.boot()

freqs = [SigTo(50),SigTo(150)]

def octaveDown():
    global freqs
    for f in freqs:
        f.value = f.value/2.

def octaveUp():
    global freqs
    for f in freqs:
        f.value = f.value*2.


# continuous inputs
LT = SigTo(0)
RT = SigTo(0)
LX = SigTo(0)
LY = SigTo(0)
RX = SigTo(0)
RY = SigTo(0)

triggers_min = 0
if sys.platform == 'darwin':
    triggers_min = -1

scaled_LT = Scale(LT, inmin=triggers_min, inmax=1, mul=0.2)
scaled_RT = Scale(RT, inmin=triggers_min, inmax=1, mul=0.2)
scaled_LX = Scale(LX, inmin=-1, inmax=1)
scaled_LY = Scale(LY, inmin=-1, inmax=1)
scaled_RX = Scale(RX, inmin=-1, inmax=1)
scaled_RY = Scale(RY, inmin=-1, inmax=1)

# buttons
LB = Button(octaveDown)
RB = Button(octaveUp)
A = Button()
B = Button()
X = Button()
Y = Button()
BACK = Button()
START = Button()
LS = Button()
RS = Button()
DPAD = DPad()

sine = SuperSaw(freq=freqs, detune=scaled_LX, bal=scaled_LY, mul=[scaled_LT,scaled_RT])
rev = Freeverb(sine, size=scaled_RX, damp=-scaled_RY, bal=scaled_RY).out()

def oscDataCallback(address, *args):
    if address.startswith("{}{}".format(CONTROLLER_ROOT_ADDRESS, CONTINUOUS_INPUTS_ADDRESS)):
        continuousInputDataCallback(address.rsplit("/", 1)[1], *args)
    elif address.startswith("{}{}".format(CONTROLLER_ROOT_ADDRESS, BUTTONS_ADDRESS)):
        buttonsDataCallback(address.rsplit("/", 1)[1], *args)
    elif address.startswith(ANALYSIS_ROOT_ADDRESS):
        analysisDataCallback(address.rsplit("/", 1)[1], *args)


def analysisDataCallback(address, *args):
    args = convertArgs(args, "f")
    if DEBUG:
        print('{} : {}'.format(address, args))


def continuousInputDataCallback(address, *args):
    args = convertArgs(args, "f")
    if DEBUG:
        print('{} : {}'.format(address, args))
    if address == 'LT':
        LT.value = args
    elif address == 'RT':
        RT.value = args
    elif address == 'LX':
        LX.value = args
    elif address == 'LY':
        LY.value = args
    elif address == 'RX':
        RX.value = args
    elif address == 'RY':
        RY.value = args

def buttonsDataCallback(address, *args):
    args = convertArgs(args, "i")
    if DEBUG:
        print('{} : {}'.format(address, args))
    if address == 'LB':
        LB.set(args)
    elif address == 'RB':
        RB.set(args)
    elif address == 'A':
        A.set(args)
    elif address == 'B':
        B.set(args)
    elif address == 'X':
        X.set(args)
    elif address == 'Y':
        Y.set(args)
    elif address == 'LS':
        LS.set(args)
    elif address == 'RS':
        RS.set(args)
    elif address == 'BACK':
        BACK.set(args)
    elif address == 'START':
        START.set(args)
    elif address == 'DPAD':
        DPAD.set(args)


osc_receiver = OscDataReceive(5005, "*", oscDataCallback)


s.gui(locals())
