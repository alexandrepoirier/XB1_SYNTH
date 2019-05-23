#/////////////////////////////
# GLOBALS AND IMPORTS
#/////////////////////////////

from pyo import *
from typing import *
import time
import threading
import sys

# setting this to true will print controller data every time time osc data is received
DEBUG = False

CONTROLLER_ROOT_ADDRESS = '/XB1'
ANALYSIS_ROOT_ADDRESS = '/ANA'
BUTTONS_ADDRESS = '/btn'
CONTINUOUS_INPUTS_ADDRESS = '/cts'

CONTINUOUS_INPUTS = ['LT', 'RT', 'LX', 'LY', 'RX', 'RY']
BUTTON_INPUTS = ['A', 'B', 'X', 'Y', 'LB', 'LT', 'RB', 'RT', 'BACK', 'START', 'LS', 'RS', 'DPAD', 'XB']
ANALYSIS_PARAMS = ['LXVel', 'LYVel', 'RXVel', 'RYVel', 'LTVel', 'RTVel', 'Density']
# [end GLOBALS AND IMPORTS]


def islambda(func):
  LAMBDA = lambda:0
  return isinstance(func, type(LAMBDA)) and func.__name__ == LAMBDA.__name__


class CallbackTimer_base(threading.Thread):
    def __init__(self, duration: Union[float, int], callback: callable, args: List[Any] = None, lock=None):
        threading.Thread.__init__(self)
        self._dur = duration
        self._callback = callback
        self._args = args
        self._lock = lock
        self._is_alive = False
        self._stop_event = threading.Event()

    def run(self):
        self._is_alive = True
        time.sleep(self._dur)
        if not self._stop_event.is_set():
            if self._lock:
                self._lock.acquire()
            if self._args is None:
                self._callback()
            else:
                self._callback(*self._args)
            if self._lock:
                self._lock.release()
        self._is_alive = False

    def stop(self):
        self._stop_event.set()


class CallbackTimer:
    def __init__(self, duration: Union[float, int], callback: callable, args: List[Any] = None, lock=None):
        self._dur = duration
        self._callback = callback
        self._args = args
        self._lock = lock
        self._timer_objs = []

    def start(self):
        nobjs = len(self._timer_objs)
        i = 0
        # stop previous timers and delete old ones if any
        while i < nobjs:
            if self._timer_objs[i].is_alive():
                self._timer_objs[i].stop()
                i += 1
            else:
                del self._timer_objs[i]
                nobjs -= 1

        self._timer_objs.append(CallbackTimer_base(self._dur, self._callback, self._args, self._lock))
        self._timer_objs[-1].start()

    def stop(self):
        if self._timer_objs:
            self._timer_objs[-1].stop()

    def setCallback(self, callback: callable, args: List[Any] = None):
        self._callback = callback
        self._args = args

    def setLock(self, lock):
        self._lock = lock

    def is_alive(self):
        return self._timer_objs[-1]._is_alive


class CallbackQueue:
    def __init__(self, delay: Union[float, int], lock=None):
        self._delay = delay
        self._lock = lock
        self._items = []
        self._async_cleanup = CallbackTimer(1, self._cleanup)

    def _cleanup(self):
        i = 0
        max = len(self._items)
        while i < max:
            if not self._items[i].is_alive():
                del self._items[i]
                max -= 1
            else:
                i += 1

    def queue(self, item: callable, args: List[Any] = None, offset=0.00, lock=None):
        if lock is None:
            lock = self._lock
        self._items.append(CallbackTimer(self._delay+offset, item, args, lock))
        self._items[-1].start()

    def empty(self):
        for item in self._items:
            item.stop()
        self._async_cleanup.start()

    def is_empty(self):
        for item in self._items:
            if item.is_alive():
                return False
        return True

    def getItem(self):
        """
        Get the most recently queued item.
        :return: item
        """
        return self._items[-1]

    def getItems(self):
        """
        Get the complete list of items in the queue, dead or alive.
        :return: list of items
        """
        return self._items


class CallbackLoop_base(threading.Thread):
    def __init__(self, duration: Union[float, int], callback: callable, args: List[Any] = None, lock=None):
        threading.Thread.__init__(self)
        self._dur = duration
        self._callback = callback
        self._args = args
        self._lock = lock
        self._is_alive = False
        self._stop_event = threading.Event()

    def run(self):
        self._is_alive = True
        while not self._stop_event.is_set():
            if self._lock:
                self._lock.acquire()
            if self._args is None:
                self._callback()
            else:
                self._callback(*self._args)
            if self._lock:
                self._lock.release()

            time.sleep(self._dur)
        self._is_alive = False

    def stop(self):
        self._stop_event.set()


class CallbackLoop:
    def __init__(self, duration: Union[float, int], callback: callable, args: List[Any] = None, lock=None):
        self._dur = duration
        self._callback = callback
        self._args = args
        self._lock = lock
        self._looper_objs = []

    def start(self):
        nobjs = len(self._looper_objs)
        i = 0
        # stop previous timers and delete old ones if any
        while i < nobjs:
            if self._looper_objs[i].is_alive():
                self._looper_objs[i].stop()
                i += 1
            else:
                del self._looper_objs[i]
                nobjs -= 1

        self._looper_objs.append(CallbackLoop_base(self._dur, self._callback, self._args, self._lock))
        self._looper_objs[-1].start()

    def stop(self):
        if self._looper_objs:
            self._looper_objs[-1].stop()

    def setCallback(self, callback: callable, args: List[Any] = None):
        self._callback = callback
        self._args = args

    def setLock(self, lock):
        self._lock = lock

    def is_alive(self):
        return self._looper_objs[-1]._is_alive


class ButtonModeEnum:
    hold = 0
    toggle = 1
    str_mapping = {"hold":hold, "momentary":hold, "toggle":toggle, "latch":toggle}

    @classmethod
    def getitem(cls, item):
        return ButtonModeEnum.str_mapping[item]

    @classmethod
    def contains(cls, item):
        for key, val in ButtonModeEnum.str_mapping.items():
            if item == val or item == key:
                return True
        return False


class Button:
    """
    class Button
    
    Implements the different behaviors of a button.

    :Args:

        name: string
            Name of the button. ie.: A, B, X, Y, etc.
        event_delay: int or float
            Maximum time allowed between two presses for them to be considered consecutive.
        hold_delay: int or float
            Time a button needs to be pressed for it to be considered a hold event.
        hold_repeat_delay: int or float
            Time between recurrent calls when a button is held down. Used when "repeat" is set to True.
    """
    def __init__(self, name: AnyStr, event_delay: Union[int, float], hold_delay: Union[int, float],
                 hold_repeat_delay: Union[int, float]):
        self._button_str = name
        self._event_delay = event_delay
        self._hold_delay = hold_delay
        self._hold_repeat_delay = hold_repeat_delay
        self._state = False # the state changes according to the mode
        self._value = 0 # this is the value continuously sent by the controller, either 0 or 1
        self._mode = ButtonModeEnum.toggle
        # registers the time the button was pressed, resets back to zero on release
        self._timestamp = 0
        self._repeats = 0
        self._REPEAT_HOLD_EVENT = False # defined by user, defines if the callback should be repeated
        self._HOLD_EVENT_VALID = False # set to true once the hold event handler has been called

        self._multipress_objs = []
        self._combination_objs = []

        # threaded queue stuff
        self._state_lock = threading.Lock()
        self._global_event_queue = CallbackQueue(self._event_delay, self._state_lock)
        self._hold_event_queue = CallbackQueue(self._hold_delay, self._state_lock)
        self._hold_callback_loop = None
        self._QUEUE_BASIC_CALLBACKS_FLAG = False
        self._TRIGGER_BASIC_CALLBACKS_FLAG = False

        # callbacks
        self._onPressCallback = lambda: None # called when the button is pressed
        self._onReleaseCallback = lambda: None # called when the button is released
        self._onHoldCallback = lambda: None # called when the button is held down for the amount of time specified in self._hold_delay
        self._callback = lambda x: None # called both when the button is pressed and released
        # this callback passes the state variable as an argument

    def _onPress(self):
        if DEBUG:
            print("[{}] pressed".format(self._button_str))

        if self._isRepeatedPress():
            self._repeats += 1
        else:
            self._repeats = 1
        self._timestamp = time.time()

        # systematically queue the hold event, it'll get cancelled if the hold time wasn't long enough
        # or it'll get cancelled if a combination gets triggered
        self._hold_event_queue.queue(self._onHoldEvent, lock=self._state_lock)

        # if part of combination, either queue MultiPress events or the basic callback
        if self._combination_objs:
            if self._multipress_objs:
                if self._repeats > 1:
                    for mp in self._multipress_objs:
                        if mp == self._repeats:
                            self._global_event_queue.empty()
                            self._global_event_queue.queue(mp)
            if self._global_event_queue.is_empty():
                self._QUEUE_BASIC_CALLBACKS_FLAG = True
                self._global_event_queue.queue(self._onPressUpdateState)
                self._global_event_queue.queue(self._onPressCallback, offset=0.01)
        else:
            # if there are MultiPress events, either : queue the current one if there are other MultiPress events
            # or : trigger the MultiPress if no other exists
            # if no MultiPress event exists : trigger the basic callback
            if self._multipress_objs:
                if self._repeats > 1:
                    for mp in self._multipress_objs:
                        if self._repeats == mp:
                            if self._repeats < self._multipress_objs[-1]:
                                self._global_event_queue.empty()
                                self._global_event_queue.queue(mp)
                            else:
                                mp()
                else:
                    self._QUEUE_BASIC_CALLBACKS_FLAG = True
                    self._global_event_queue.queue(self._onPressUpdateState)
                    self._global_event_queue.queue(self._onPressCallback, offset=0.01)
            else:
                self._TRIGGER_BASIC_CALLBACKS_FLAG = True
                self._onPressUpdateState()
                self._onPressCallback()

    def _onPressUpdateState(self):
        if self._mode == 0:
            self._state = True
            if DEBUG:
                print("[{}] state updated to {}".format(self._button_str, self._state))

    def _onReleaseUpdateState(self):
        if self._mode == 0:
            self._state = False
        elif self._mode == 1:
            self._state = not self._state
        if DEBUG:
            print("[{}] state updated to {}".format(self._button_str, self._state))

    def _resetFlags(self):
        self._TRIGGER_BASIC_CALLBACKS_FLAG = False
        self._QUEUE_BASIC_CALLBACKS_FLAG = False

    def _onRelease(self):
        if DEBUG:
            print("[{}] released".format(self._button_str))

        # if the hold event didn't trigger, then cancel the hold event callback queue and proceed with normal event flow
        if self._HOLD_EVENT_VALID:
            self._HOLD_EVENT_VALID = False
            if self._REPEAT_HOLD_EVENT:
                self._hold_callback_loop.stop()
        else:
            self._hold_event_queue.empty()

            if self._TRIGGER_BASIC_CALLBACKS_FLAG:
                self._onReleaseUpdateState()
                self._onReleaseCallback()
            else:
                if self._QUEUE_BASIC_CALLBACKS_FLAG:
                    self._global_event_queue.queue(self._onReleaseUpdateState)
                    self._global_event_queue.queue(self._onReleaseCallback, offset=0.01)

    def _isRepeatedPress(self):
        if (time.time() - self._timestamp) <= self._event_delay:
            return True
        else:
            return False

    def _onHoldEvent(self):
        if islambda(self._onHoldCallback):
            return

        self._HOLD_EVENT_VALID = True
        if self._REPEAT_HOLD_EVENT:
            self._hold_callback_loop.start()
        else:
            self._onHoldCallback()

    def _queueItem(self, item):
        self._global_event_queue.queue(item)

    def emptyQueue(self):
        self._global_event_queue.empty()
        self._hold_event_queue.empty()
        self._resetFlags()

    def set(self, value):
        if value != self._value:
            self._value = value
            self._enterCallbackLogic()

    def _enterCallbackLogic(self):
        if self._value == 1:
            self._onPress()
        else:
            self._onRelease()

        if self._TRIGGER_BASIC_CALLBACKS_FLAG:
            self._callback(self._state)
        else:
            if self._QUEUE_BASIC_CALLBACKS_FLAG:
                self._global_event_queue.queue(self._callback, [self._state])

        if self._value != 1:
            # reset the flags AFTER the callback logic is done
            self._resetFlags()

        # this NEEDS to happen AFTER the queue is updated
        # because the code coming after this might cancel the queue
        for combination in self._combination_objs:
            combination.setButtonState(self._button_str, bool(self._value))

    def get(self):
        return self._value

    def addMultiPressEvent(self, repeats, callback):
        if repeats not in self._multipress_objs:
            self._multipress_objs.append(MultiPress(repeats, callback))
        self._multipress_objs.sort()

    def addCombinationEvent(self, combination_object):
        self._combination_objs.append(combination_object)

    def setOnPressCallback(self, callback):
        assert callable(callback), "Callback must be of type 'callable'"
        self._onPressCallback = callback

    def setOnReleaseCallback(self, callback):
        assert callable(callback), "Callback must be of type 'callable'"
        self._onReleaseCallback = callback

    def setOnHoldCallback(self, callback, repeat=False):
        assert callable(callback), "Callback must be of type 'callable'"
        self._onHoldCallback = callback
        self._REPEAT_HOLD_EVENT = repeat
        if repeat:
            self._hold_callback_loop = CallbackLoop(self._hold_repeat_delay, callback)

    def setCallback(self, callback):
        assert callable(callback), "Callback must be of type 'callable'"
        self._callback = callback

    def setMode(self, mode):
        if isinstance(mode, int):
            if ButtonModeEnum.contains(mode):
                self._mode = mode
        elif isinstance(mode, str):
            self._mode = ButtonModeEnum.getitem(mode)
        else:
            raise TypeError("'mode' can either be of type int or str")

    def getState(self):
        return self._state

    def getTimestamp(self):
        return self._timestamp

    def getButtonString(self):
        return self._button_str


class DPad:
    """
    class DPad
    
    Implements the basic functions of a D-Pad.

    :Args:
        callback: callable
            Function to be called when the D-Pad state changes. ie. any button is pressed or unpressed.
            Note: A list is passed as an argument to the callback.
    """
    def __init__(self, callback: callable = None):
        if callback:
            self.setCallback(callback)
        else:
            self._callback = lambda x: None
        self._value = [0,0]

    def set(self, value):
        if value != self._value:
            self._value = value
            if value:
                self._callback(value)

    def getValue(self):
        return self._value

    def setCallback(self, callback):
        assert callable(callback), "Callback must be of type 'callable'"
        self._callback = callback


class ButtonCombination(object):
    """
    class ButtonCombination
    
    Defines the button combination model
    
    :parent: object
    
    :arguments:
        buttons : the list of buttons part of the combination
        delta : maximum time (in seconds) allowed between the first and last button press for a combination to be valid.
        target_callback : function to be triggered by this combination as set by the user
        event_callback : function to call when the combination happens, this is the controller's method that ensures
                         the combination is valid which will put the combination in the queue.
    """
    def __init__(self, buttons: List[str], delta: Union[float, int],
                 target_callback: callable, event_callback: callable):
        assert isinstance(buttons, list), "buttons attribute must be of type list"
        for elem in buttons:
            assert isinstance(elem, str), "buttons attribute must be a list of strings"
        assert isinstance(delta, float), "delta attribute must be of type float"
        assert callable(target_callback), "target_callback attribute must be a callable"

        self._btns = buttons
        self._btns.sort()
        self._btns_state = [False] * len(self._btns)
        self._delta = delta
        # the callback will always be set to the controllers main combination callback
        self._target_callback = target_callback
        self._event_callback = event_callback
        self._initial_time = 0

    def __iter__(self):
        for item in self._btns:
            yield item

    def __contains__(self, item):
        return item in self._btns

    def __eq__(self, other):
        return self._btns == other

    def __ne__(self, other):
        return self._btns != other

    def __call__(self):
        self._target_callback()

    def _allButtonsPressed(self):
        for state in self._btns_state:
            if not state:
                return False
        return True

    def _allButtonsUnpressed(self):
        for state in self._btns_state:
            if state:
                return False
        return True

    def _verifyTiming(self):
        if (time.time() - self._initial_time) <= self._delta:
            return True
        else:
            return False

    def setButtonState(self, btn, state):
        if state and self._allButtonsUnpressed():
            self._initial_time = time.time()

        self._btns_state[self._btns.index(btn)] = state

        if state and self._allButtonsPressed() and self._verifyTiming():
            self._event_callback(self)


class MultiPress(object):
    """
    class MultiPress
    
    Stores the data relative to a MultiPress event (fast consecutive button presses)
    
    :arguments:
        repeats : number of repeats to watch for, subsequent presses are ignored when delta is exceeded
        callback : function to call when the MultiPress event is valid
    """
    def __init__(self, repeats: int, callback: callable):
        assert repeats > 1, "at least two repeats are required for a MultiPress event"
        assert callable(callback), "callback attribute must be a callable"
        self._repeats = repeats
        self._callback = callback

    def __call__(self):
        self._callback()

    def __lt__(self, other):
        return self._repeats < other

    def __gt__(self, other):
        return self._repeats > other

    def __eq__(self, other):
        return self._repeats == other

    def __ne__(self, other):
        return self._repeats != other


class Scrub(PyoObject):
    def __init__(self, obj, min=0, max=1):
        PyoObject.__init__(self)
        self._obj = obj
        self._min = min
        self._max = max
        self._update_time = 0.1
        self._func_timer = CallbackLoop(self._update_time, self._update)
        self._value = 0
        self._sig = SigTo(self._value, time=self._update_time)

        self._base_objs = self._sig.getBaseObjects()

        self._func_timer.start()

    def stop(self):
        PyoObject.stop(self)
        self._func_timer.stop()

    def _update(self):
        self._value += (self._obj.get()**3)/10

        if self._value < self._min:
            self._value = self._min
        elif self._value > self._max:
            self._value = self._max

        self._sig.value = self._value


class Controller:
    def __init__(self):
        self._global_event_delay = 0.18
        self._hold_button_delay = 1
        self._hold_repeat_delay = 0.5
        self._combinations = []
        self._queue = CallbackQueue(self._global_event_delay)

        # Initialize audio objects to receive controller data

        global CONTINUOUS_INPUTS, BUTTON_INPUTS, ANALYSIS_PARAMS

        # continuous inputs
        self._continuous_objs = {}
        for input in CONTINUOUS_INPUTS:
            self._continuous_objs[input] = SigTo(0)

        # utile quand le driver de base est utilise sur windows, sinon useless
        triggers_min = 0

        self._scaled_continuous_objs = {}
        self._scaled_continuous_objs['LT'] = Scale(self._continuous_objs['LT'], inmin=triggers_min, inmax=1, outmin=0, outmax=1)
        self._scaled_continuous_objs['RT'] = Scale(self._continuous_objs['RT'], inmin=triggers_min, inmax=1, outmin=0, outmax=1)
        self._scaled_continuous_objs['LX'] = Scale(self._continuous_objs['LX'], inmin=-1, inmax=1, outmin=0, outmax=1)
        self._scaled_continuous_objs['LY'] = Scale(self._continuous_objs['LY'], inmin=-1, inmax=1, outmin=0, outmax=1)
        self._scaled_continuous_objs['RX'] = Scale(self._continuous_objs['RX'], inmin=-1, inmax=1, outmin=0, outmax=1)
        self._scaled_continuous_objs['RY'] = Scale(self._continuous_objs['RY'], inmin=-1, inmax=1, outmin=0, outmax=1)

        self._scrub_objs = {}
        #self._scrub_objs['LT'] = Clip(Delay(self._continuous_objs['LT']**3, 0.1, feedback=0.5, mul=0.1), min=0, max=1)
        #self._scrub_objs['RT'] = Clip(Delay(self._continuous_objs['RT']**3, 0.1, feedback=0.5, mul=0.1), min=0, max=1)
        self._scrub_objs['LX'] = Scrub(self._continuous_objs['LX'])
        self._scrub_objs['LY'] = Scrub(self._continuous_objs['LY'])
        self._scrub_objs['RX'] = Scrub(self._continuous_objs['RX'])
        self._scrub_objs['RY'] = Scrub(self._continuous_objs['RY'])

        # buttons
        self._button_objs = {}
        for btn in BUTTON_INPUTS:
            if btn == 'DPAD':
                self._dpad_obj = DPad()
            else:
                self._button_objs[btn] = Button(name=btn, event_delay=self._global_event_delay,
                                                hold_delay=self._hold_button_delay,
                                                hold_repeat_delay=self._hold_repeat_delay)

        # analysis
        self._analysis_objs = {}
        for param in ANALYSIS_PARAMS:
            self._analysis_objs[param] = SigTo(0)

    def cleanup(self):
        for key, obj in self._scrub_objs.items():
            obj.stop()

    def _convertArgs(self, args, type):
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

    def _analysisDataCallback(self, which, *args):
        arg = self._convertArgs(args, "f")
        if DEBUG:
            print('/{} : {}'.format(which, arg))
        self._analysis_objs[which].value = arg

    def _continuousInputDataCallback(self, which, *args):
        arg = self._convertArgs(args, "f")
        if DEBUG:
            print('/{} : {}'.format(which, arg))
        self._continuous_objs[which].value = arg
        if which in ['LT', 'RT']:
            self._button_objs[which].set(arg)

    def _buttonsDataCallback(self, which, *args):
        arg = self._convertArgs(args, "i")
        if DEBUG:
            print('/{} : {}'.format(which, arg))
        if which == 'DPAD':
            self._dpad_obj.set(arg)
        else:
            self._button_objs[which].set(arg)

    def oscDataCallback(self, address, *args):
        if address.startswith("{}{}".format(CONTROLLER_ROOT_ADDRESS, CONTINUOUS_INPUTS_ADDRESS)):
            self._continuousInputDataCallback(address.rsplit("/", 1)[1], *args)
        elif address.startswith("{}{}".format(CONTROLLER_ROOT_ADDRESS, BUTTONS_ADDRESS)):
            self._buttonsDataCallback(address.rsplit("/", 1)[1], *args)
        elif address.startswith(ANALYSIS_ROOT_ADDRESS):
            self._analysisDataCallback(address.rsplit("/", 1)[1], *args)

    def mainDataCallback(self, controller_data, analysis_data=None):
        for btn in BUTTON_INPUTS:
            if btn == 'DPAD':
                self._dpad_obj.set(controller_data[btn])
            else:
                self._button_objs[btn].set(controller_data[btn])

        for input in CONTINUOUS_INPUTS:
            self._continuous_objs[input].value = controller_data[input]
            if input in ['LT', 'RT']:
                self._button_objs[input].set(controller_data[input])

        if analysis_data:
            for param in ANALYSIS_PARAMS:
                self._analysis_objs[param].value = analysis_data[param]

    def onCombinationEvent(self, combination_obj):
        if self._queue.is_empty():
            for btn in combination_obj:
                self._button_objs[btn].emptyQueue()
            self._queue.queue(combination_obj)
        else:
            # if the new combination contains the same buttons as the previous one plus others, it has priority
            for btn in self._queue.getItem():
                if btn not in combination_obj:
                    return
            self._queue.empty()
            self._queue.queue(combination_obj)
            for btn in combination_obj:
                self._button_objs[btn].emptyQueue()

    def registerCombination(self, buttons, callback):
        new = ButtonCombination(buttons, self._global_event_delay, callback, self.onCombinationEvent)
        for comb in self._combinations:
            if comb == new:
                raise ValueError("Trying to register an already existing combination.")

        self._combinations.append(new)

        for btn in new:
            self._button_objs[btn].addCombinationEvent(new)

    def registerMultiPress(self, button, repeats, callback):
        self._button_objs[button].addMultiPressEvent(repeats, callback)

    def setScaledObjectAttributes(self, name, inmin, inmax, outmin, outmax):
        self._scaled_continuous_objs[name].setInMin(inmin)
        self._scaled_continuous_objs[name].setInMax(inmax)
        self._scaled_continuous_objs[name].setOutMin(outmin)
        self._scaled_continuous_objs[name].setOutMax(outmax)

    def _getContinuousObjects(self, keys):
        sub = {}
        for key in self._scaled_continuous_objs:
            if key in keys:
                sub[key] = self._scaled_continuous_objs[key]
        return sub

    @property
    def buttons(self):
        return self._button_objs

    @property
    def dpad(self):
        return self._dpad_obj

    @property
    def triggers(self):
        return self._getContinuousObjects(['LT', 'RT'])

    @property
    def sticks(self):
        return self._getContinuousObjects(['LX', 'LY', 'RX', 'RY'])

    @property
    def analysis(self):
        return self._analysis_objs

    @property
    def scrub(self):
        return self._scrub_objs
