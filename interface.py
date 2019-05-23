import wx
import time
import os
import config_file_io
import pyo
import configparser
import math
from typing import *

SCRIPT_PATH = os.path.dirname(os.path.realpath(__file__))

REC_DIR = os.path.join(os.path.expanduser('~'), 'Desktop')


def createFilename():
    return os.path.join(REC_DIR, "rec_{}.wav".format(time.strftime("%d-%m-%y_%H-%M-%S")))


def getScaledColour(value):
    b = int((1 - value) * 255)
    r = int(value * 255)
    return wx.Colour(r, 0, b)


def ampTodB(x, prec):
    if x <= 0.000001:
        return -120.0
    return round(20 * math.log10(x), prec)


class CustomMessageDialog(wx.Dialog):
    def __init__(self, parent, message, title):
        wx.Dialog.__init__(self, parent, -1, title, size=(200, 100))
        self._gbs = wx.GridBagSizer(vgap=5, hgap=5)
        self._message = wx.StaticText(self, -1, label=message)
        self._gbs.Add(self._message, (0, 0))
        self._ok_btn = wx.Button(self, label="Ok", id=wx.ID_OK)
        self._gbs.Add(self._ok_btn, (1, 0), flag=wx.EXPAND)
        box = wx.BoxSizer()
        box.Add(self._gbs, 1, wx.EXPAND | wx.ALL, 10)
        self.SetSizerAndFit(box)


class DeviceSetup(wx.Dialog):
    def __init__(self):
        wx.Dialog.__init__(self, None, pos=(200, 200), title="Device Setup",
                           style=wx.DEFAULT_FRAME_STYLE & ~(wx.RESIZE_BORDER | wx.MAXIMIZE_BOX))
        self._gbs = wx.GridBagSizer(vgap=5, hgap=5)

        config_filename = "config.ini"
        if os.path.exists(os.path.join(SCRIPT_PATH, "custom_config.ini")):
            config_filename = "custom_config.ini"

        config = config_file_io.read(os.path.join(SCRIPT_PATH, config_filename))

        sr_list = ["44100", "48000", "88200", "96000"]
        sr_label = wx.StaticText(self, label="Sample Rate")
        self._gbs.Add(sr_label, pos=(0, 0))
        self._sr_choice = wx.Choice(self, choices=sr_list)
        self._sr_choice.SetSelection(sr_list.index(str(config['server']['sr'])))
        self._gbs.Add(self._sr_choice, pos=(1, 0), flag=wx.EXPAND)

        nchnls_list = ["1", "2", "3", "4"]
        nchnls_label = wx.StaticText(self, label="Channels")
        self._gbs.Add(nchnls_label, pos=(2, 0))
        self._nchlns_choice = wx.Choice(self, choices=nchnls_list)
        self._nchlns_choice.SetSelection(nchnls_list.index(str(config['server']['nchnls'])))
        self._gbs.Add(self._nchlns_choice, pos=(3, 0), flag=wx.EXPAND)

        buffersize_list = ["32", "64", "128", "256", "512", "1024", "2048"]
        buffersize_label = wx.StaticText(self, label="Buffersize")
        self._gbs.Add(buffersize_label, pos=(4, 0))
        self._buffersize_choice = wx.Choice(self, choices=buffersize_list)
        self._buffersize_choice.SetSelection(buffersize_list.index(str(config['server']['buffersize'])))
        self._gbs.Add(self._buffersize_choice, pos=(5, 0), flag=wx.EXPAND)

        duplex_label = wx.StaticText(self, label="Duplex (Out / In+Out)")
        self._gbs.Add(duplex_label, pos=(6, 0))
        self._duplex_choice = wx.Choice(self, choices=["0", "1"])
        self._duplex_choice.SetSelection(config['server']['duplex'])
        self._gbs.Add(self._duplex_choice, pos=(7, 0), flag=wx.EXPAND)

        # input devices
        input_device_label = wx.StaticText(self, label="Input Device")
        self._gbs.Add(input_device_label, pos=(8, 0))
        input_devices_list, index_list = pyo.pa_get_input_devices()
        final_list = ["{}: {}".format(i, d) for i, d in zip(index_list, input_devices_list)]
        self._input_device_choice = wx.Choice(self, choices=final_list)
        self._gbs.Add(self._input_device_choice, pos=(9, 0))

        inindex = index_list.index(pyo.pa_get_default_input())
        if config['device']['inindex']:
            try:
                inindex = index_list.index(config['device']['inindex'])
            except:
                pass

        self._input_device_choice.SetSelection(inindex)

        # output devices
        output_device_label = wx.StaticText(self, label="Output Device")
        self._gbs.Add(output_device_label, pos=(10, 0))
        output_devices_list, index_list = pyo.pa_get_output_devices()

        # this loops replaces non-ascii characters with '?'
        for i, device in enumerate(output_devices_list):
            newtext = ""
            for char in device:
                if ord(char) < 128:
                    newtext += char
                else:
                    newtext += "?"
            output_devices_list[i] = newtext

        final_list = ["{}: {}".format(i, d) for i, d in zip(index_list, output_devices_list)]
        self._output_device_choice = wx.Choice(self, choices=final_list)
        self._gbs.Add(self._output_device_choice, pos=(11, 0))

        outindex = index_list.index(pyo.pa_get_default_output())
        if config['device']['outindex']:
            try:
                outindex = index_list.index(config['device']['outindex'])
            except:
                pass

        self._output_device_choice.SetSelection(outindex)

        self._gbs.Add(-1, 15, pos=(12, 0))

        # buttons
        self._ok_btn = wx.Button(self, label="Ok", id=wx.ID_OK)
        self._gbs.Add(self._ok_btn, (13, 0), flag=wx.EXPAND)
        self._cancel_btn = wx.Button(self, label="Cancel", id=wx.ID_CANCEL)
        self._gbs.Add(self._cancel_btn, (14, 0), flag=wx.EXPAND)

        box = wx.BoxSizer()
        box.Add(self._gbs, 1, wx.EXPAND | wx.ALL, 5)
        self.SetSizerAndFit(box)

        self._ok_btn.Bind(wx.EVT_LEFT_UP, self.OnOkButton)

    def OnOkButton(self, evt):
        evt.Skip()
        self._saveConfig()

    def _saveConfig(self):
        parser = configparser.ConfigParser()
        parser.read(os.path.join(SCRIPT_PATH, "config.ini"))

        parser['server']['sr'] = self._sr_choice.GetString(self._sr_choice.GetSelection())
        parser['server']['nchnls'] = self._nchlns_choice.GetString(self._nchlns_choice.GetSelection())
        parser['server']['buffersize'] = self._buffersize_choice.GetString(self._buffersize_choice.GetSelection())
        parser['server']['duplex'] = self._duplex_choice.GetString(self._duplex_choice.GetSelection())

        inindex, inname = self._input_device_choice.GetString(self._input_device_choice.GetSelection()).split(':', 1)
        parser['device']['inname'] = inname.strip()
        parser['device']['inindex'] = inindex

        outindex, outname = self._output_device_choice.GetString(self._output_device_choice.GetSelection()).split(':', 1)
        parser['device']['outname'] = outname.strip()
        parser['device']['outindex'] = outindex

        custom_config_path = os.path.join(SCRIPT_PATH, "custom_config.ini")
        try:
            f = open(custom_config_path, 'w')
            parser.write(f)
        except:
            # if we make it here, the config file is probably broken or incomplete, so better delete it
            try:
                os.remove(os.path.join(SCRIPT_PATH, "custom_config.ini"))
            except:
                pass

    def getServerInitLine(self):
        return {'sr': int(self._sr_choice.GetString(self._sr_choice.GetSelection())),
                'nchnls': int(self._nchlns_choice.GetString(self._nchlns_choice.GetSelection())),
                'buffersize': int(self._buffersize_choice.GetString(self._buffersize_choice.GetSelection())),
                'duplex': int(self._duplex_choice.GetString(self._duplex_choice.GetSelection()))}

    def getInputDeviceIndex(self):
        return self._input_device_choice.GetString(self._input_device_choice.GetSelection()).split(':', 1)[0]

    def getOutputDeviceIndex(self):
        return self._output_device_choice.GetString(self._output_device_choice.GetSelection()).split(':', 1)[0]


class Grid(wx.Frame):
    """
    class Grid

    :param elem_list: list of tuples ("Text to display", callable, *args))
    """

    def __init__(self, elem_list: List[Tuple[str, Callable, Optional[Any]]], server: pyo.Server, main_out_obj: pyo.PyoObject):
        wx.Frame.__init__(self, None, pos=(200, 200), title="The Grid",
                          style=wx.DEFAULT_FRAME_STYLE & ~(wx.RESIZE_BORDER | wx.MAXIMIZE_BOX))

        self._status_bar = wx.StatusBar(self)
        self.SetStatusBar(self._status_bar)
        self._status_bar.SetFieldsCount(3)
        self._status_bar.SetStatusText("Stopped", 0)

        self._server = server
        self._IS_RECORDING = False
        self._button_size = (100, 100)
        self._button_list = []
        self._callback_mapping = {}
        self._args_mapping = {}
        self._max_columns = 8
        self._slave_windows = []

        # BUTTONS
        self._gbs = wx.GridBagSizer(vgap=5, hgap=5)
        self._start_server_btn = wx.Button(self, label="Start Server")
        self._start_server_btn.Bind(wx.EVT_LEFT_UP, self.ToggleServerState)
        self._gbs.Add(self._start_server_btn, pos=(0, 0), span=wx.GBSpan(1, 3), flag=wx.EXPAND)
        self._rec_btn = wx.Button(self, label="Start Recording")
        self._rec_btn.Bind(wx.EVT_LEFT_UP, self.ToggleRecording)
        self._rec_btn.Disable()
        self._gbs.Add(self._rec_btn, pos=(0, 3), span=wx.GBSpan(1, 3), flag=wx.EXPAND)
        self._mute_btn = wx.Button(self, label="Mute Server")
        self._mute_btn.Bind(wx.EVT_LEFT_UP, self.ToggleMuting)
        self._mute_btn.Disable()
        self._gbs.Add(self._mute_btn, pos=(0, 6), span=wx.GBSpan(1,2), flag=wx.ALIGN_LEFT)

        # METERS
        self._last_peak_value = -120
        self._last_rms_value = -120

        self._peak_meter = pyo.PyoGuiVuMeter(self, nchnls=2, size=(300, 1))
        self._gbs.Add(self._peak_meter, pos=(1,0), span=wx.GBSpan(1, 7))
        self._peak_text = wx.StaticText(self, -1, "")
        self._setPeakText(-120)
        self._peak_text.Bind(wx.EVT_LEFT_DOWN, self.OnPeakValMouseDown)
        self._gbs.Add(self._peak_text, pos=(1, 7), flag=wx.EXPAND)

        self._rms_meter = pyo.PyoGuiVuMeter(self, nchnls=2, size=(300, 1))
        self._gbs.Add(self._rms_meter, pos=(2, 0), span=wx.GBSpan(1, 7))
        self._rms_text = wx.StaticText(self, -1, "")
        self._setRMSText(-120)
        self._rms_text.Bind(wx.EVT_LEFT_DOWN, self.OnRMSValMouseDown)
        self._gbs.Add(self._rms_text, pos=(2, 7), flag=wx.EXPAND)

        self._peak_obj = pyo.PeakAmp(main_out_obj, self._metersCallback)
        self._rms_obj = pyo.RMS(main_out_obj, None)
        self._rms_obj.polltime(0.5)
        self._rms_port = pyo.Port(self._rms_obj, 0.5, 0.1)


        row = 2 # current rox number, which is 1 after adding the sta/stop buttons and the VuMeter
        for elem in elem_list:
            self._button_list.append(wx.Button(self, label=self._formatText(elem[0]), size=self._button_size))

            self._callback_mapping[self._button_list[-1].GetId()] = elem[1]
            if len(elem) > 2:
                self._args_mapping[self._button_list[-1].GetId()] = elem[2:]
            else:
                self._args_mapping[self._button_list[-1].GetId()] = None

            self._button_list[-1].Bind(wx.EVT_LEFT_UP, self.OnMouseUp)

            col = (len(self._button_list) - 1) % self._max_columns
            if col == 0:
                row += 1

            self._gbs.Add(self._button_list[-1], (row, col))

        box = wx.BoxSizer()
        box.Add(self._gbs, 1, wx.EXPAND | wx.ALL, 5)
        self.SetSizerAndFit(box)
        self._gbs.RecalcSizes()

    def OnMouseUp(self, evt):
        evt.Skip()
        if self._args_mapping[evt.GetId()]:
            self._callback_mapping[evt.GetId()](*self._args_mapping[evt.GetId()])
        else:
            self._callback_mapping[evt.GetId()]()

    def Show(self):
        wx.Frame.Show(self)
        for win in self._slave_windows:
            win.Show()

    def ToggleServerState(self, evt):
        evt.Skip()
        if self._server.getIsStarted():
            self._server.stop()
            if self._IS_RECORDING:
                self.ToggleRecording(None)
            self._rec_btn.Disable()
            self._mute_btn.Disable()
            self._start_server_btn.SetLabel("Start Server")
            self._status_bar.SetStatusText("Stopped", 0)
        else:
            self._server.start()
            self._server.amp = self._server.amp # little hack, when the server is restarted the amp value is not taken into account
            self._rec_btn.Enable()
            self._mute_btn.Enable()
            self._start_server_btn.SetLabel("Stop Server")
            self._status_bar.SetStatusText("Playing", 0)

    def ToggleRecording(self, evt):
        if evt is not None: evt.Skip()
        if self._IS_RECORDING:
            self._rec_btn.SetLabel("Start Recording")
            self._server.recstop()
            print("Stop recording")
        else:
            self._rec_btn.SetLabel("Stop Recording")
            filename = createFilename()
            self._server.recstart(filename)
            print("recording to : {}".format(filename))
        self._IS_RECORDING = not self._IS_RECORDING

    def ToggleMuting(self, evt):
        if evt is not None: evt.Skip()
        self._server.amp = 0 if self._server.amp == 1 else 1
        self._updateMuteButtonLabel()

    def _updateMuteButtonLabel(self):
        if self._server.amp:
            self._mute_btn.SetLabel("Mute Server")
        else:
            self._mute_btn.SetLabel("Unmute Server")

    def SetStatusText(self, text, field=0):
        self._status_bar.SetStatusText(text, field)

    def addSlaveWindow(self, win):
        self._slave_windows.append(win)
        x, y = self.GetPosition()
        w,h = self.GetSize()
        offset = 50 * (len(self._slave_windows) - 1)
        win.SetPosition((x + w, y + offset))

    def _formatText(self, text):
        if len(text) > 12:
            seps = [' ', '_', '-']
            pos = -1
            for sep in seps:
                if pos == -1 or (text.find(sep) != -1 and text.find(sep) < pos):
                    pos = text.find(sep)

            if pos != -1 and pos <= 12:
                text = text[:pos + 1] + '\n' + text[pos + 1:]
            else:
                text = text[:12] + '\n' + text[12:]

        return text

    def OnPeakValMouseDown(self, event):
        self._last_peak_value = -120
        self._peak_text.SetForegroundColour(wx.Colour(0,0,0))
        self._setPeakText(-120)
        wx.CallAfter(self.Refresh)
        event.Skip()

    def OnRMSValMouseDown(self, event):
        self._last_rms_value = -120
        self._rms_text.SetForegroundColour(wx.Colour(0, 0, 0))
        self._setRMSText(-120)
        wx.CallAfter(self.Refresh)
        event.Skip()

    def _metersCallback(self, *args):
        new_peak_val = ampTodB(sum(args)/2., 2)
        if new_peak_val > self._last_peak_value:
            self._last_peak_value = new_peak_val
            self._setPeakText(new_peak_val)
        self._peak_meter.setRms(*args)

        rms = self._rms_port.get(all=True)
        new_rms_val = ampTodB(sum(rms)/2., 2)
        if new_rms_val > self._last_rms_value:
            self._last_rms_value = new_rms_val
            self._setRMSText(new_rms_val)
        self._rms_meter.setRms(*rms)

    def _setPeakText(self, value):
        if value >= 0:
            self._peak_text.SetForegroundColour(wx.Colour(255,0,0))
        self._peak_text.SetLabel("{:.2f} dB TP".format(value))

    def _setRMSText(self, value):
        if value >= 0:
            self._rms_text.SetForegroundColour(wx.Colour(255,0,0))
        self._rms_text.SetLabel("{:.2f} dB RMS".format(value))


class Sliders(wx.Frame):
    """
    class Sliders

    :param elem_list: list of dictionaries {'text':"Text to display", 'obj':pyo obj, 'min':min, 'max':max,
                                            'type':'lin' or 'exp', 'default':default value,
                                            'attr': "attribute to apply the value on"}
    """

    def __init__(self, parent, elem_list: List[Dict], title: str = "Sliderzzzzzz"):
        wx.Frame.__init__(self, parent, pos=(200, 200), title=title,
                          style=wx.DEFAULT_FRAME_STYLE & ~(wx.RESIZE_BORDER | wx.MAXIMIZE_BOX))

        self._panel_list = []
        self._sliders_dict = {}
        self._sliders_attributes = {}

        self._gbs = wx.GridBagSizer(vgap=5, hgap=5)

        for elem in elem_list:
            # create panel
            self._panel_list.append(wx.Panel(self, size=(100, 100)))
            panel = self._panel_list[-1]
            gbs = wx.GridBagSizer(vgap=5, hgap=5)

            # create slider and labels
            text = wx.StaticText(panel, label=elem['text'])
            slider = wx.Slider(panel, size=(300, -1))
            self._sliders_dict[slider.GetId()] = slider
            slider.Bind(wx.EVT_SLIDER, self.OnSliderMotion)
            mintext = wx.StaticText(panel, label=str(elem['min']))
            maxtext = wx.StaticText(panel, label=str(elem['max']))
            valuetext = wx.StaticText(panel, label=str(elem['min']))

            # add them to the grid bag sizer
            gbs.Add(text, (0, 0), span=wx.GBSpan(1, 4), flag=wx.EXPAND)
            gbs.Add(slider, (1, 0), span=wx.GBSpan(1, 4), flag=wx.EXPAND)
            gbs.Add(mintext, (2, 0), flag=wx.ALIGN_LEFT)
            gbs.Add(valuetext, (2, 2), flag=wx.ALIGN_RIGHT | wx.EXPAND)
            gbs.Add(maxtext, (2, 3), flag=wx.ALIGN_RIGHT)
            box = wx.BoxSizer()
            box.Add(gbs, 1, wx.EXPAND | wx.ALL, border=5)
            panel.SetSizerAndFit(box)

            # store data relative to the slider's id
            self._sliders_attributes[slider.GetId()] = elem
            self._sliders_attributes[slider.GetId()]['value_label'] = valuetext
            self._setScaledSliderValue(slider.GetId(), elem['default'])

            row = len(self._panel_list) - 1
            self._gbs.Add(panel, (row, 0), flag=wx.EXPAND | wx.ALL)

        box = wx.BoxSizer()
        box.Add(self._gbs, 1, wx.EXPAND | wx.ALL, 5)
        self.SetSizerAndFit(box)

    def OnSliderMotion(self, evt):
        evt.Skip()
        self._updateSliderValue(evt.GetId(), evt.GetEventObject().GetValue())

    def _getScaledSliderValue(self, id, value):
        if self._sliders_attributes[id]['type'] == 'lin':
            value = value / 100. * (self._sliders_attributes[id]['max'] - self._sliders_attributes[id]['min']) + \
                    self._sliders_attributes[id]['min']
        elif self._sliders_attributes[id]['type'] == 'exp':
            value = (value / 100.) ** 2 * (self._sliders_attributes[id]['max'] - self._sliders_attributes[id]['min']) + \
                    self._sliders_attributes[id]['min']

        return value

    def _getNormalizedSliderValue(self, id, value):
        if self._sliders_attributes[id]['type'] == 'lin':
            value = (value - self._sliders_attributes[id]['min']) / (
                        self._sliders_attributes[id]['max'] - self._sliders_attributes[id]['min']) * 100
        elif self._sliders_attributes[id]['type'] == 'exp':
            value = ((value - self._sliders_attributes[id]['min']) / (
                        self._sliders_attributes[id]['max'] - self._sliders_attributes[id]['min'])) ** 2 * 100

        return value

    def _setScaledSliderValue(self, id, value):
        self._sliders_dict[id].SetValue(self._getNormalizedSliderValue(id, value))
        self._updateSliderValue(id, self._getNormalizedSliderValue(id, value))

    def _updateSliderValue(self, id, value):
        col = getScaledColour(value / 100.)
        self._sliders_attributes[id]['value_label'].SetForegroundColour(col)
        value = self._getScaledSliderValue(id, value)
        self._sliders_attributes[id]['value_label'].SetLabel("%.3f" % value)

        if self._sliders_attributes[id]['obj'].getServer().getIsStarted():
            exec("self._sliders_attributes[id]['obj'].{} = value".format(self._sliders_attributes[id]['attr']))


class FileBrowser(wx.Frame):
    def __init__(self, parent):
        wx.Frame.__init__(self, parent, -1, pos=(200, 200), title="File Browser",
                          style=wx.DEFAULT_FRAME_STYLE & ~(wx.RESIZE_BORDER | wx.MAXIMIZE_BOX))

        self._history = []
        self._history_max_count = 10
        self._current_file = ""
        self._onSelectionChanged = lambda x: None

        self._gbs = wx.GridBagSizer(vgap=5, hgap=5)

        self._history_ctrl = wx.Choice(self, size=(500, -1), choices=["Empty history"])
        self._history_ctrl.SetSelection(0)
        self._history_ctrl.Bind(wx.EVT_CHOICE, self.OnSelectFromHistory)
        self._gbs.Add(self._history_ctrl, pos=(0,0))

        self._choose_file_btn = wx.Button(self, -1, "Open File")
        self._choose_file_btn.Bind(wx.EVT_LEFT_UP, self.OnOpenFile)
        self._gbs.Add(self._choose_file_btn, pos=(1,0))

        box = wx.BoxSizer()
        box.Add(self._gbs, 1, wx.EXPAND | wx.ALL, 5)
        self.SetSizerAndFit(box)

    def OnSelectFromHistory(self, evt):
        evt.Skip()

        if evt.GetString() != "Empty history":
            self._current_file = evt.GetString()
            self._moveHistoryItemUp(evt.GetSelection())
            self._history_ctrl.Set(self._history)
            self._history_ctrl.SetSelection(0)
            self._onSelectionChanged(self._current_file)

    def OnOpenFile(self, evt):
        evt.Skip()

        new_selection = self._openFileDialog()

        if os.path.exists(new_selection):
            self._current_file = new_selection
            self._addToHistory(new_selection)
            self._history_ctrl.Set(self._history)
            self._history_ctrl.SetSelection(0)
            self._onSelectionChanged(self._current_file)

    def _openFileDialog(self):
        formats = "wave (.wav, .wave)|*.wav; *.wave|" \
                  "AIFF (.aif, .aiff)|*.aif; *.aiff"

        file_path = ""

        dlg = wx.FileDialog(self, wildcard=formats)
        if dlg.ShowModal():
            file_path = dlg.GetPath()

        dlg.Destroy()
        return file_path

    def _addToHistory(self, path):
        if path in self._history:
            self._moveHistoryItemUp(self._history.index(path))
        else:
            self._history.insert(0, path)

            if len(self._history) > self._history_max_count:
                self._history.pop(self._history_max_count)

    def _moveHistoryItemUp(self, index):
        self._history.insert(0, self._history.pop(index))

    def setSelectionChangedCallback(self, callback):
        self._onSelectionChanged = callback
