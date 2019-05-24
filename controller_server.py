#/////////////////////////////
# IMPORTS AND PROJECT VARIABLES
#/////////////////////////////

# imports
from operator import attrgetter
import platform
import pygame
from pygame.locals import *

# custom imports
from mappingobject import DualMappingObject
from draw import *
from analysis import *

PLATFORM = platform.uname()[0].upper()

if PLATFORM == 'WINDOWS':
    import xinput

__version__ = '1.0.0'
__vernum__ = tuple([int(s) for s in __version__.split('.')])
DEBUG = False
ENGINE_PAUSED = False
GUI = True

max_fps = 60
trigger_error_win = -3.051850947599719e-05
controller_values = {'A':0, 'B':0, 'X':0, 'Y':0, 'LB':0, 'RB':0, 'LS':0, 'RS':0, 'BACK':0, 'START':0, 'XB':0,
                     'DPAD':(0,0), 'LX':0, 'LY':0, 'RX':0, 'RY':0, 'LT':0, 'RT':0}
controller_data_types = {'A':"i", 'B':"i", 'X':"i", 'Y':"i", 'LB':"i", 'RB':"i", 'LS':"i", 'RS':"i", 'BACK':"i",
                         'START':"i", 'XB':"i", 'DPAD':["i","i"], 'LX':"f", 'LY':"f", 'RX':"f", 'RY':"f", 'LT':"f",
                         'RT':"f"}
analysis_values = {'LXVel':0, 'LYVel':0, 'RXVel':0, 'RYVel':0, 'LTVel':0, 'RTVel':0, 'Density':0}
# [end IMPORTS AND PROJECT VARIABLES]



#/////////////////////////////
# OSC SETUP
#/////////////////////////////

import argparse
from pythonosc import udp_client, osc_bundle_builder, osc_message_builder


OSC_STATUS = {0:'Sending data', 1:'Error', 2:'Network unreachable', 3:'Paused'}
OSC_STATUS_CODE = 0
CONTROLLER_ROOT_ADDRESS = '/XB1'
ANALYSIS_ROOT_ADDRESS = '/ANA'
BUTTONS_ADDRESS = '/btn'
CONTINUOUS_INPUTS_ADDRESS = '/cts'
IP_ADDRESS = "127.0.0.1"
OSC_PORT = 5005

parser = argparse.ArgumentParser()
parser.add_argument("--ip", default=IP_ADDRESS, help="The ip of the OSC server")
parser.add_argument("--port", type=int, default=OSC_PORT, help="The port the OSC server is listening on")
args = parser.parse_args()
client = udp_client.SimpleUDPClient(args.ip, args.port)

def sendOSCData():
    global OSC_STATUS_CODE
    try:
        # build all osc messages for the controller values
        controller_bundle_builder = osc_bundle_builder.OscBundleBuilder(osc_bundle_builder.IMMEDIATELY)
        for key in controller_values:
            # differentiate between buttons and continuous inputs
            if "i" in controller_data_types[key]:
                address = "{}{}/{}".format(CONTROLLER_ROOT_ADDRESS, BUTTONS_ADDRESS, key)
            elif controller_data_types[key] == "f":
                address = "{}{}/{}".format(CONTROLLER_ROOT_ADDRESS, CONTINUOUS_INPUTS_ADDRESS, key)
            msg = osc_message_builder.OscMessageBuilder(address)
            if key == 'DPAD':
                msg.add_arg(controller_values[key][0], controller_data_types[key][0])
                msg.add_arg(controller_values[key][1], controller_data_types[key][1])
            else:
                msg.add_arg(controller_values[key], controller_data_types[key])
            controller_bundle_builder.add_content(msg.build())

        # build all osc messages for the analysis values
        analysis_bundle_builder = osc_bundle_builder.OscBundleBuilder(osc_bundle_builder.IMMEDIATELY)
        for key in analysis_values:
            msg = osc_message_builder.OscMessageBuilder("{}/{}".format(ANALYSIS_ROOT_ADDRESS, key))
            msg.add_arg(analysis_values[key], "f")
            analysis_bundle_builder.add_content(msg.build())

        # build final bundle
        osc_data = osc_bundle_builder.OscBundleBuilder(osc_bundle_builder.IMMEDIATELY)
        osc_data.add_content(controller_bundle_builder.build())
        osc_data.add_content(analysis_bundle_builder.build())
        # send bundles over network
        client.send(osc_data.build())
    except InterruptedError:
        OSC_STATUS_CODE = 1
    except OSError:
        OSC_STATUS_CODE = 2
    else:
        OSC_STATUS_CODE = 0

# [end OSC SETUP]



#/////////////////////////////
# PYGAME AND CONTROLLER INIT
#/////////////////////////////

XBOX_CONTROLLER = False
JOYSTICK_NAME = ''
joystick = None
screen = None
screen_rect = None
clock = None

def init():
    global XBOX_CONTROLLER, JOYSTICK_NAME, joystick, buttons_codes, axis_codes, d_pad_codes
    global pygame, screen, screen_rect, clock

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


init()
# [end PYGAME AND CONTROLLER INIT]



#/////////////////////////////
# DISPLAY ELEMENTS
#/////////////////////////////

# button display
button_a = Struct(rect=Rect(560, 200, 20, 20), value=0)
button_b = Struct(rect=Rect(600, 160, 20, 20), value=0)
button_x = Struct(rect=Rect(520, 160, 20, 20), value=0)
button_y = Struct(rect=Rect(560, 120, 20, 20), value=0)
button_left_bumper = Struct(rect=Rect(40, 80, 40, 20), value=0)
button_right_bumper = Struct(rect=Rect(560, 80, 40, 20), value=0)
button_back = Struct(rect=Rect(240, 160, 20, 20), value=0)
button_start = Struct(rect=Rect(400, 160, 20, 20), value=0)
button_left_stick = Struct(rect=Rect(60, 160, 20, 20), value=0)
button_right_stick = Struct(rect=Rect(400, 240, 20, 20), value=0)
button_xbox = Struct(rect=Rect(320, 100, 20, 20), value=0)
buttons = {
    'A':button_a, 'B':button_b, 'X':button_x, 'Y':button_y,
    'LB':button_left_bumper, 'RB':button_right_bumper,
    'BACK':button_back, 'START':button_start,
    'LS':button_left_stick, 'RS':button_right_stick, 'XB':button_xbox}

# stick display
left_stick = Struct(rect=Rect(0, 0, 80, 40), x=0.0, y=0.0)
right_stick = Struct(rect=Rect(0, 0, 40, 40), x=0.0, y=0.0)
left_stick.rect.center = button_left_stick.rect.center
right_stick.rect.center = button_right_stick.rect.center

# trigger display
left_trigger = Struct(rect=Rect(40, 40, 40, 40), value=0.0)
right_trigger = Struct(rect=Rect(560, 40, 40, 40), value=0.0)

# d-pad display arrangement:
# (-1,  1)    (0,  1)    (1,  1)
# (-1,  0     (0,  0)    (1,  0)
# (-1, -1)    (0, -1)    (1, -1)
d_pad = {}
d_pad_posx = {-1: 0, 0: 20, 1: 40}
d_pad_posy = {1: 0, 0: 20, -1: 40}
for y in 1, 0, -1:
    for x in -1, 0, 1:
        d_pad[x, y] = Struct(rect=Rect(220 + d_pad_posx[x], 220 + d_pad_posy[y], 20, 20), value=0)
pressed_pads = [0,0]  # save state
# [end DISPLAY ELEMENTS]



#/////////////////////////////
# EVENT HANDLING FUNCTIONS
#/////////////////////////////

def update_d_pad_mac(event, event_type):
    d_pad[tuple(pressed_pads)].value = 0
    if event_type == JOYBUTTONDOWN:
        if d_pad_codes[event.button] == 'DOWN':
            pressed_pads[1] = -1
        elif d_pad_codes[event.button] == 'UP':
            pressed_pads[1] = 1
        elif d_pad_codes[event.button] == 'LEFT':
            pressed_pads[0] = -1
        elif d_pad_codes[event.button] == 'RIGHT':
            pressed_pads[0] = 1
        d_pad[tuple(pressed_pads)].value = 1
    elif event_type == JOYBUTTONUP:
        if d_pad_codes[event.button] == 'DOWN':
            pressed_pads[1] = 0
        elif d_pad_codes[event.button] == 'UP':
            pressed_pads[1] = 0
        elif d_pad_codes[event.button] == 'LEFT':
            pressed_pads[0] = 0
        elif d_pad_codes[event.button] == 'RIGHT':
            pressed_pads[0] = 0
        if pressed_pads != [0,0]:
            d_pad[tuple(pressed_pads)].value = 1
    controller_values['DPAD'] = pressed_pads


def update_triggers_windows(axis, value):
    if XBOX_CONTROLLER:
        if axis == axis_codes['RT']:
            controller_values['RT'] = value
            right_trigger.value = value
        elif axis == axis_codes['LT']:
            controller_values['LT'] = value
            left_trigger.value = value
    else:
        if value == trigger_error_win:
            left_trigger.value = 0
            right_trigger.value = 0
        elif value > 0:
            controller_values['LT'] = value
            left_trigger.value = value
        elif value < 0:
            controller_values['RT'] = -value
            right_trigger.value = -value


def update_axis_motion_windows(axis, value):
    global controller_values
    if axis == axis_codes['LY']:
        if XBOX_CONTROLLER:
            left_stick.y = stick_center_snap(value)
            controller_values['LY'] = value
        else:
            left_stick.y = stick_center_snap(-value)
            controller_values['LY'] = -value
    elif axis == axis_codes['LX']:
        left_stick.x = stick_center_snap(value)
        controller_values['LX'] = value
    elif axis == axis_codes['RY']:
        if XBOX_CONTROLLER:
            right_stick.y = stick_center_snap(value)
            controller_values['RY'] = value
        else:
            right_stick.y = stick_center_snap(-value)
            controller_values['RY'] = -value
    elif axis == axis_codes['RX']:
        right_stick.x = stick_center_snap(value)
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
            if axis == axis_codes['LT']:
                left_trigger.value = (value + 1) / 2.
            elif axis == axis_codes['RT']:
                right_trigger.value = (value + 1) / 2.
            elif axis == axis_codes['LY']:
                left_stick.y = stick_center_snap(-value)
            elif axis == axis_codes['LX']:
                left_stick.x = stick_center_snap(value)
            elif axis == axis_codes['RY']:
                right_stick.y = stick_center_snap(-value)
            elif axis == axis_codes['RX']:
                right_stick.x = stick_center_snap(value)


def handle_button_down(event):
    if DEBUG:
        print('JOYBUTTONDOWN: button {}'.format(event.button))
    if event.button in buttons_codes:
        controller_values[buttons_codes[event.button]] = 1
        buttons[buttons_codes[event.button]].value = 1
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
        buttons[buttons_codes[event.button]].value = 0
    elif PLATFORM == 'DARWIN' and event.button in d_pad_codes:
        update_d_pad_mac(event, JOYBUTTONUP)
    else:
        if DEBUG:
            print('Button not mapped')


def handle_hat_motion(event):
    # pygame sends this; xinput sends a button instead--the handler converts the button to a hat event
    if DEBUG:
        print('JOYHATMOTION: joy {} hat {} value {}'.format(event.joy, event.hat, event.value))
    global pressed_pads
    d_pad[tuple(pressed_pads)].value = 0
    pressed_pads = event.value
    if event.value != (0, 0):
        d_pad[pressed_pads].value = 1
    controller_values['DPAD'] = pressed_pads

# [end EVENT HANDLING FUNCTIONS]



#/////////////////////////////
# ANALYSIS OBJECTS
#/////////////////////////////

ls_velocity = StickVelocityTracker(max_fps)
rs_velocity = StickVelocityTracker(max_fps)
lt_velocity = TriggerVelocityTracker(max_fps)
rt_velocity = TriggerVelocityTracker(max_fps)
density = DensityTracker(list(buttons.keys()), max_fps)
# [end ANALYSIS OBJECTS]



#/////////////////////////////
# MAIN LOOP
#/////////////////////////////

if GUI:
    screen = pygame.display.set_mode((640, 480))
    pygame.display.set_caption("XB1 OSC Synth Project - Server Window")
    screen_rect = screen.get_rect()

    while True:
        clock.tick(max_fps)
        if ENGINE_PAUSED:
            for event in pygame.event.get():
                if event.type == KEYDOWN:
                    if event.key == K_SPACE:
                        ENGINE_PAUSED = False
                        OSC_STATUS_CODE = 0
                    elif event.key == K_q:
                        if pygame.key.get_mods() == KMOD_LMETA:
                            quit()
        else:
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
                elif event.type == KEYDOWN:
                    if event.key == K_ESCAPE:
                        quit()
                    elif event.key == K_q:
                        if pygame.key.get_mods() == KMOD_LMETA:
                            quit()
                    elif event.key == K_r:
                        if pygame.key.get_mods() == KMOD_LMETA:
                            pass # implement reset
                    elif event.key == K_SPACE:
                        ENGINE_PAUSED = True
                elif event.type == QUIT:
                    quit()

            # analysis objects update
            ls_velocity.tick(left_stick.x, left_stick.y)
            rs_velocity.tick(right_stick.x, right_stick.y)
            lt_velocity.tick(left_trigger.value)
            rt_velocity.tick(right_trigger.value)
            btn_values = {}
            for btn in buttons:
                btn_values[btn] = buttons[btn].value
            density.tick(btn_values)
            analysis_values['LXVel'] = ls_velocity['X']['LongTermVel']
            analysis_values['LYVel'] = ls_velocity['Y']['LongTermVel']
            analysis_values['RXVel'] = rs_velocity['X']['LongTermVel']
            analysis_values['RYVel'] = rs_velocity['Y']['LongTermVel']
            analysis_values['LTVel'] = lt_velocity['LongTermVel']
            analysis_values['RTVel'] = rt_velocity['LongTermVel']
            analysis_values['Density'] = density.get()

            if DEBUG:
                print("Controller values : {}".format(controller_values))

            screen.fill(COLORS['black'])

            # draw the controls
            for button in buttons.values():
                if button == button_xbox:
                    draw_xbox_button(button, screen)
                else:
                    draw_button(button, screen)
            draw_stick(left_stick, screen)
            draw_stick(right_stick, screen)
            draw_trigger(left_trigger, screen)
            draw_trigger(right_trigger, screen)
            draw_d_pad(d_pad, screen)

            # send the osc data
            sendOSCData()
            # draw program state
            if ENGINE_PAUSED:
                w, h = HUGE_FONT.size("PAUSED")
                screen.blit(HUGE_FONT.render("PAUSED", True, COLORS['white']), (320-int(w/2), 20))
                OSC_STATUS_CODE = 3

            draw_values(controller_values, analysis_values, screen)
            draw_osc_satus(OSC_STATUS, OSC_STATUS_CODE, IP_ADDRESS, CONTROLLER_ROOT_ADDRESS, ANALYSIS_ROOT_ADDRESS,
                           OSC_PORT, screen)

            pygame.display.flip()
else:
    while True:
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
            elif event.type == KEYDOWN:
                if event.key == K_ESCAPE:
                    quit()
                elif event.key == K_q:
                    if pygame.key.get_mods() == KMOD_LMETA:
                        quit()
                elif event.key == K_r:
                    if pygame.key.get_mods() == KMOD_LMETA:
                        pass  # implement reset
                elif event.key == K_SPACE:
                    ENGINE_PAUSED = True
            elif event.type == QUIT:
                quit()

        # analysis objects update
        ls_velocity.tick(left_stick.x, left_stick.y)
        rs_velocity.tick(right_stick.x, right_stick.y)
        lt_velocity.tick(left_trigger.value)
        rt_velocity.tick(right_trigger.value)
        btn_values = {}
        for btn in buttons:
            btn_values[btn] = buttons[btn].value
        density.tick(btn_values)
        analysis_values['LXVel'] = ls_velocity['X']['LongTermVel']
        analysis_values['LYVel'] = ls_velocity['Y']['LongTermVel']
        analysis_values['RXVel'] = rs_velocity['X']['LongTermVel']
        analysis_values['RYVel'] = rs_velocity['Y']['LongTermVel']
        analysis_values['LTVel'] = lt_velocity['LongTermVel']
        analysis_values['RTVel'] = rt_velocity['LongTermVel']
        analysis_values['Density'] = density.get()

        if DEBUG:
            print("Controller values : {}".format(controller_values))

        # send the osc data
        sendOSCData()
# [end MAIN LOOP]
