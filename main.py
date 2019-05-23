#----------------------------------------------------------------
#
#
#
#                 **************************
#         THIS IS WHAT USED TO BE controller_server.py
#                 **************************
#
#
#
#
#----------------------------------------------------------------


def controller_worker(controller_continuous_array, controller_buttons_array, continuous_ref_array, btns_ref_array, RUN):
    #/////////////////////////////
    # IMPORTS AND PROJECT VARIABLES
    #/////////////////////////////

    # imports
    from operator import attrgetter
    import platform
    import pygame
    import pygame.locals
    from threading import Thread

    # custom imports
    from mappingobject import DualMappingObject
    #import draw
    import analysis

    PLATFORM = platform.uname()[0].upper()

    if PLATFORM == 'WINDOWS':
        import xinput

    __version__ = '1.0.0'
    __vernum__ = tuple([int(s) for s in __version__.split('.')])

    DEBUG = False

    max_fps = 60
    trigger_error_win = -3.051850947599719e-05
    controller_values = {'A':0, 'B':0, 'X':0, 'Y':0, 'LB':0, 'RB':0, 'LS':0, 'RS':0, 'BACK':0, 'START':0, 'XB':0,
                         'DPAD':[0,0], 'LX':0, 'LY':0, 'RX':0, 'RY':0, 'LT':0, 'RT':0}
    analysis_values = {'LXVel':0, 'LYVel':0, 'RXVel':0, 'RYVel':0, 'LTVel':0, 'RTVel':0, 'Density':0}
    # [end IMPORTS AND PROJECT VARIABLES]



    #/////////////////////////////
    # PYGAME AND CONTROLLER INIT
    #/////////////////////////////

    XBOX_CONTROLLER = False
    JOYSTICK_NAME = ''
    joystick = None
    clock = None

    #global XBOX_CONTROLLER, JOYSTICK_NAME, joystick, buttons_codes, axis_codes, d_pad_codes
    #global pygame, screen, screen_rect, clock

    pygame.init()
    pygame.joystick.init()

    clock = pygame.time.Clock()
    # Initialize a joystick object: grabs the first joystick
    if PLATFORM == 'WINDOWS':
        joysticks = xinput.XInputJoystick.enumerate_devices()
        if DEBUG:
            print("Joysticks returned by XInputJoystick : {}".format(joysticks))
        device_numbers = list(map(attrgetter('device_number'), joysticks))
        if DEBUG:
            print("Joysticks device numbers : {}".format(device_numbers))
        if device_numbers:
            joystick = pygame.joystick.Joystick(device_numbers[0])
            JOYSTICK_NAME = joystick.get_name().upper()
            if DEBUG:
                print('Joystick: {} using "{}" device'.format(PLATFORM, JOYSTICK_NAME))
            if 'XBOX' in JOYSTICK_NAME:
                XBOX_CONTROLLER = True
                joystick = xinput.XInputJoystick(device_numbers[0])
                buttons_codes = DualMappingObject((0,'A'), (1,'B'), (2,'X'), (3,'Y'), (4,'LB'), (5,'RB'), (6,'BACK'),
                                                  (7,'START'), (8,'LS'), (9,'RS'), (10,'XB'))
                axis_codes = DualMappingObject(('LX',1), ('LY',0), ('RX',4), ('RY',3), ('LT',2), ('RT',5))
                if DEBUG:
                    print('Using xinput.XInputJoystick')
            else:
                # put other logic here for handling platform + device type in the event loop
                if DEBUG:
                    print('Using pygame joystick')
                joystick.init()
                buttons_codes = DualMappingObject((0,'A'), (1,'B'), (2,'X'), (3,'Y'), (4,'LB'), (5,'RB'), (6,'BACK'),
                                                  (7,'START'), (8,'LS'), (9,'RS'), (10,'XB'))
                axis_codes = DualMappingObject(('LX',0), ('LY',1), ('RX',4), ('RY',3), ('LT',2), ('RT',2))
        d_pad_codes = DualMappingObject((0,'DOWN'), (0,'UP'), (0,'LEFT'), (0,'RIGHT')) # setting this as a default just in case
    elif PLATFORM == 'DARWIN':
        joysticks = []
        for i in range(0, pygame.joystick.get_count()):
            joysticks.append(pygame.joystick.Joystick(i))
            joysticks[-1].init()
            if DEBUG:
                print("Detected joystick '", joysticks[-1].get_name(), "'")
        buttons_codes = DualMappingObject((11, 'A'), (12, 'B'), (13, 'X'), (14, 'Y'), (8, 'LB'), (9, 'RB'), (5, 'BACK'),
                                          (4, 'START'), (6, 'LS'), (7, 'RS'), (10, 'XB'))
        axis_codes = DualMappingObject(('LX', 0), ('LY', 1), ('RX', 2), ('RY', 3), ('LT', 4), ('RT', 5))
        d_pad_codes = DualMappingObject((1, 'DOWN'), (0, 'UP'), (2, 'LEFT'), (3, 'RIGHT'))
    # [end PYGAME AND CONTROLLER INIT]



    #/////////////////////////////
    # EVENT HANDLING FUNCTIONS
    #/////////////////////////////

    def update_d_pad_mac(event, event_type):
        if event_type == JOYBUTTONDOWN:
            if d_pad_codes[event.button] == 'DOWN':
                controller_values['DPAD'][1] = -1
            elif d_pad_codes[event.button] == 'UP':
                controller_values['DPAD'][1] = 1
            elif d_pad_codes[event.button] == 'LEFT':
                controller_values['DPAD'][0] = -1
            elif d_pad_codes[event.button] == 'RIGHT':
                controller_values['DPAD'][0] = 1
        elif event_type == JOYBUTTONUP:
            if d_pad_codes[event.button] == 'DOWN':
                controller_values['DPAD'][1] = 0
            elif d_pad_codes[event.button] == 'UP':
                controller_values['DPAD'][1] = 0
            elif d_pad_codes[event.button] == 'LEFT':
                controller_values['DPAD'][0] = 0
            elif d_pad_codes[event.button] == 'RIGHT':
                controller_values['DPAD'][0] = 0


    def update_triggers_windows(axis, value):
        if XBOX_CONTROLLER:
            if axis == axis_codes['RT']:
                controller_values['RT'] = value
            elif axis == axis_codes['LT']:
                controller_values['LT'] = value
        else:
            if value > 0:
                controller_values['LT'] = value
            elif value < 0:
                controller_values['RT'] = -value


    def update_axis_motion_windows(axis, value):
        global controller_values
        if axis == axis_codes['LY']:
            if XBOX_CONTROLLER:
                controller_values['LY'] = value
            else:
                controller_values['LY'] = -value
        elif axis == axis_codes['LX']:
            controller_values['LX'] = value
        elif axis == axis_codes['RY']:
            if XBOX_CONTROLLER:
                controller_values['RY'] = value
            else:
                controller_values['RY'] = -value
        elif axis == axis_codes['RX']:
            controller_values['RX'] = value
        else:
            update_triggers_windows(axis, value)


    def handle_axis_motion(axis, value):
        global controller_values
        if DEBUG:
            print('JOYAXISMOTION: axis {}, value {}'.format(event.axis, event.value))
        if axis in axis_codes:
            if PLATFORM == 'WINDOWS':
                update_axis_motion_windows(axis, value)
            elif PLATFORM == 'DARWIN':
                controller_values[axis_codes[axis]] = -value if axis in [axis_codes['LY'], axis_codes['RY']] else value


    def handle_button_down(event):
        if DEBUG:
            print('JOYBUTTONDOWN: button {}'.format(event.button))
        if event.button in buttons_codes:
            controller_values[buttons_codes[event.button]] = 1
        elif PLATFORM == 'DARWIN' and event.button in d_pad_codes:
            update_d_pad_mac(event, JOYBUTTONDOWN)
        else:
            if DEBUG:
                print('Button not mapped')


    def handle_button_up(event):
        if DEBUG:
            print('JOYBUTTONUP: button {}'.format(event.button))
        if event.button in buttons_codes:
            controller_values[buttons_codes[event.button]] = 0
        elif PLATFORM == 'DARWIN' and event.button in d_pad_codes:
            update_d_pad_mac(event, JOYBUTTONUP)
        else:
            if DEBUG:
                print('Button not mapped')


    def handle_hat_motion(event):
        # pygame sends this; xinput sends a button instead--the handler converts the button to a hat event
        if DEBUG:
            print('JOYHATMOTION: joy {} hat {} value {}'.format(event.joy, event.hat, event.value))
        controller_values['DPAD'] = event.value
    # [end EVENT HANDLING FUNCTIONS]



    #/////////////////////////////
    # ANALYSIS OBJECTS
    #/////////////////////////////

    # ls_velocity = analysis.StickVelocityTracker(max_fps)
    # rs_velocity = analysis.StickVelocityTracker(max_fps)
    # lt_velocity = analysis.TriggerVelocityTracker(max_fps)
    # rt_velocity = analysis.TriggerVelocityTracker(max_fps)
    # density = analysis.DensityTracker(['A', 'B', 'X', 'Y', 'LB', 'RB'], max_fps)
    # [end ANALYSIS OBJECTS]



    #/////////////////////////////
    # MAIN CONTROLLER UPDATE LOOP
    #/////////////////////////////

    while RUN:
        clock.tick(max_fps)
        if XBOX_CONTROLLER:
            joystick.dispatch_events()

        for event in pygame.event.get():
            if DEBUG:
                print('event: {}'.format(pygame.event.event_name(event.type)))
            if event.type == JOYAXISMOTION:
                handle_axis_motion(event.axis, event.value)
            elif event.type == JOYBUTTONDOWN:
                handle_button_down(event)
            elif event.type == JOYBUTTONUP:
                handle_button_up(event)
            elif event.type == JOYHATMOTION:
                handle_hat_motion(event)

        # analysis objects update
        # ls_velocity.tick(controller_values['LX'], controller_values['LY'])
        # rs_velocity.tick(controller_values['RX'], controller_values['RY'])
        # lt_velocity.tick(controller_values['LT'])
        # rt_velocity.tick(controller_values['RT'])
        # density.tick(controller_values)
        # analysis_values['LXVel'] = ls_velocity['X']['LongTermVel']
        # analysis_values['LYVel'] = ls_velocity['Y']['LongTermVel']
        # analysis_values['RXVel'] = rs_velocity['X']['LongTermVel']
        # analysis_values['RYVel'] = rs_velocity['Y']['LongTermVel']
        # analysis_values['LTVel'] = lt_velocity['LongTermVel']
        # analysis_values['RTVel'] = rt_velocity['LongTermVel']
        # analysis_values['Density'] = density.get()

        if DEBUG:
            print("Controller values : {}".format(controller_values))

        #update array
        with controller_continuous_array.get_lock():
            for i, elem in enumerate(continuous_ref_array):
                controller_continuous_array[i].value = controller_values[elem]

        with controller_buttons_array.get_lock():
            for i, elem in enumerate(btns_ref_array):
                controller_buttons_array[i].value = controller_values[elem]
    # [end MAIN CONTROLLER UPDATE LOOP]


#----------------------------------------------------------------
#
#
#
#                 **************************
#         THIS IS WHAT USED TO BE controller_client.py
#                 **************************
#
#
#
#
#----------------------------------------------------------------


#/////////////////////////////
# GLOBALS AND IMPORTS
#/////////////////////////////

from pyo import *
import wx
import time
import os
import multiprocessing

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
#osc_receiver = OscDataReceive(5005, "*", xb1_controller.oscDataCallback)

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



#/////////////////////////////
# MAIN FLOW
#/////////////////////////////

btns_ref = ['A', 'B', 'X', 'Y', 'LB', 'RB', 'LS', 'RS', 'BACK', 'START', 'XB', 'DPAD1', 'DPAD2']
continuous_ref = ['LX', 'LY', 'RX', 'RY', 'LT', 'RT']
controller_values_continuous = multiprocessing.Array("f", len(continuous_ref))
controller_values_btns = multiprocessing.Array("i", len(btns_ref))
WORKER_STATE = multiprocessing.Value('b', True)

controller_process = multiprocessing.Process(target=controller_worker, args=(controller_values_continuous,
                                             controller_values_btns, continuous_ref, btns_ref, WORKER_STATE))

controller_process.start()
#mon.logSessionStart()
main_win.Show()
app.MainLoop()

server.stop()
#mon.logSessionEnd()
xb1_controller.cleanup()

with WORKER_STATE.get_lock():
    WORKER_STATE.value = False

controller_process.join()
# [end MAIN FLOW]
