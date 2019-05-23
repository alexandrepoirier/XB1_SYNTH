#!/usr/bin/env python
# encoding: utf-8



#/////////////////////////////
# GLOBALS AND IMPORTS
#/////////////////////////////

from pyo import *
import wx
import time
import os
import controller
import effects
import utils
from interface import DeviceSetup, CustomMessageDialog, Grid, Sliders, FileBrowser

CWD = os.getcwd()

DEBUG = False # prints osc data received
# [end GLOBALS AND IMPORTS]



#/////////////////////////////
# SERVER SETUP
#/////////////////////////////

server = Server()

app = wx.App()

while not server.getIsBooted():
    ds = DeviceSetup()
    ds.CentreOnScreen()

    if ds.ShowModal() == wx.ID_OK:
        try:
            server.reinit(**ds.getServerInitLine())
            server.setOutputDevice(ds.getOutputDeviceIndex())
            server.setInputDevice(ds.getInputDeviceIndex())
            time.sleep(.1)
            server.boot()
        except:
            dlg = CustomMessageDialog(None, "An error occured while booting the server.\nCheck server's setup parameters.", "Error")
            dlg.ShowModal()
            dlg.Destroy()
    else:
        exit()

    ds.Destroy()
# [end SERVER SETUP]



#/////////////////////////////
# MONITORING SETUP
#/////////////////////////////

import monitoring
mon = monitoring.Monitor() # setting audio source after script execution

def logAndPrint(*args):
    mon.log(*args)
    print(*args)
# [end MONITORING SETUP]



#/////////////////////////////
# AUDIO AND CONTROLLER SETUP
#/////////////////////////////

main_volume = Sig(1)

xb1_controller = controller.Controller()
osc_receiver = OscDataReceive(5005, "*", xb1_controller.oscDataCallback)

audio_scripts = ["AMFM.py", "test_granulation.py", "amb_gen.py"]
script_index = 0 # select script to run here

file = open(os.path.join(CWD, "audio_scripts", audio_scripts[script_index])).read()
script = "{}".format(file)
exec(script)

assert 'main_out' in globals(), "Error : main_out object doesn't exist"
main_out.mul = main_volume
mon.setAudioSource(main_out)
# [end AUDIO AND CONTROLLER SETUP]



#/////////////////////////////
# INTERFACE ELEMENTS
#/////////////////////////////

main_win = Grid(elem_list=[], server=server, main_out_obj=main_out)
main_win.SetTitle(audio_scripts[script_index])
main_volume_slider = Sliders(main_win, [{'text': "Main Volume", 'obj': main_volume, 'min': 0, 'max': 2,
                                         'type': "lin", 'default': 1, 'attr': "value"}])

main_win.addSlaveWindow(main_volume_slider)

if "fileSelectionCallback" in globals():
    file_browser_win = FileBrowser(main_win)
    file_browser_win.setSelectionChangedCallback(fileSelectionCallback)
    main_win.addSlaveWindow(file_browser_win)
# [end INTERFACE ELEMENTS]

#/////////////////////////////
# BASIC CONTROLS
#/////////////////////////////

IS_RECORDING = False
IS_MUTED = False
rec_dir = os.path.join(os.path.expanduser('~'), 'Desktop')
createFilename = lambda: os.path.join(rec_dir, "rec_{}.wav".format(time.strftime("%d-%m-%y_%H-%M-%S")))
server.recordOptions(sampletype=1)

def muteServer():
    global main_win
    main_win.ToggleMuting(None)
xb1_controller.buttons['START'].setMode(1)
xb1_controller.buttons['START'].setOnReleaseCallback(muteServer)

def startRecording():
    global main_win
    main_win.ToggleRecording(None)
xb1_controller.buttons['BACK'].setMode(1)
xb1_controller.buttons['BACK'].setOnReleaseCallback(startRecording)
# [end BASIC CONTROLS]


mon.logSessionStart()
main_win.Show()
app.MainLoop()

server.stop()
mon.logSessionEnd()
xb1_controller.cleanup()
