import os
import time
import pyo
import getpass
import socket


NETWORK_ROOT = "\\\\MTL-BI458\\XB1_Monitoring"


class SoundRecorder:
    """
    Double buffered sound recorder.
    """
    def __init__(self, obj, path, chnls):
        # instance variables
        self._chnls = chnls
        self._path = path # root path for recordings
        self._table_dur = 120.0 # min 5 sec.
        self._current_table_index = -1
        self._table_count = 2
        self._table_list = [pyo.NewTable(self._table_dur, self._chnls) for i in range(self._table_count)]
        self._total_count = 0

        # pyo objects
        self._getNextTable()
        self._rec_obj = pyo.TableRec(obj, self._table_list[self._current_table_index])
        self._tswitch_trig = pyo.TrigFunc(self._rec_obj['trig'], self._switchNextTable, arg=[i for i in range(self._table_count)])

    def record(self):
        self._rec_obj.play()
        return self

    def stop(self):
        cur_pos = self._rec_obj['time'].get()
        self._rec_obj.stop()
        self._savePartialTable(cur_pos)

    def _getNextTable(self):
        self._current_table_index = (self._current_table_index + 1) % self._table_count

    def _getPreviousTable(self):
        return (self._current_table_index - 1) % self._table_count

    def _switchNextTable(self, index):
        if index != 0:
            return
        self._getNextTable()
        self._rec_obj.setTable(self._table_list[self._current_table_index])
        self._rec_obj.play()
        self._total_count += 1
        self._saveTable(self._getPreviousTable())

    def _createFilename(self):
        return os.path.join(self._path, "rec_{:02d}.wav".format(self._total_count))

    def _saveTable(self, index):
        self._table_list[index].save(self._createFilename())

    def _savePartialTable(self, pos):
        self._total_count += 1
        pos = int(pos)
        final_table = pyo.DataTable(pos, self._chnls)
        final_table.copyData(self._table_list[self._current_table_index], srcpos=0, destpos=0, length=pos)
        final_table.fadeout()
        final_table.save(self._createFilename())



class Monitor:
    def __init__(self, audio_source=None):
        try:
            self._username = getpass.getuser()
        except:
            self._username = "unknown"

        self._hostname = socket.getfqdn().split('.', 1)[0]
        if not self._hostname:
            self._hostname = "UNKNOWN"

        self._session_number = -1
        self._session_path = ""

        try:
            self._initFolderStructure()
            self._log = self._createSessionLog()
        except:
            self._log = None

        if audio_source and self._session_path:
            self._rec_obj = SoundRecorder(audio_source, self._session_path, 2)
        else:
            self._rec_obj = None

    def _initFolderStructure(self):
        """
        Creates the folder structure and the session path.
        :return: None
        """
        userpath = os.path.join(NETWORK_ROOT, self._hostname, self._username)
        if os.path.exists(userpath):
            folders = os.listdir(userpath)
            if folders:
                self._session_number = int(folders[-1]) + 1
            else:
                self._session_number = 0
        elif os.path.exists(os.path.join(NETWORK_ROOT, self._hostname)):
            os.mkdir(userpath)
            self._session_number = 0
        else:
            os.mkdir(os.path.join(NETWORK_ROOT, self._hostname))
            os.mkdir(userpath)
            self._session_number = 0

        self._session_path = os.path.join(userpath, "{:02d}".format(self._session_number))
        os.mkdir(self._session_path)

    def _createSessionLog(self):
        """
        Creates a new log for the current session.
        :return: FileObject
        """
        return open(os.path.join(self._session_path, "log.txt"), 'w')

    def _writeLine(self, text):
        if self._log:
            self._log.write( "[{}] {}\n".format(time.strftime("%H:%M:%S"), text) )

    def logSessionStart(self):
        self._writeLine("Session started")
        if self._rec_obj:
            self._rec_obj.record()

    def log(self, *args):
        text = ""
        for arg in args:
            text += arg
        self._writeLine(text)

    def logSessionEnd(self):
        self._writeLine("Session ended")
        if self._rec_obj:
            self._rec_obj.stop()

    def setAudioSource(self, audio_source):
        if self._session_path:
            self._rec_obj = SoundRecorder(audio_source, self._session_path, 2)



if __name__ == "__main__":
    server = pyo.Server()
    server.setOutputDevice(9)
    server.setInputDevice(7)
    server.boot().start()
    sine = pyo.Sine([300,400], mul=0.3).play()

    mon = Monitor(sine)
    mon.logSessionStart()
    state = False
    for i in range(15):
        state = not state
        if state:
            time.sleep(1)
            sine.freq = [300, 500]
        else:
            time.sleep(1)
            sine.freq = [300, 400]
    mon.logSessionEnd()
