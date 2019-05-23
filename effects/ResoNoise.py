from pyo import *
import math
import os

class ResoNoise(PyoObject):
    """
    class ResoNoise

    Warning: This class is very expansive to compute since it can create a massive amount of streams.
    You can calculate it by multiplying the number of harmonics by the polyphony.
    """
    piano_harms = [1,12,19,24,27,34,36,40]
    organ_harms = [1,19.02,27.86,33.69,36,43.02]
    def __init__(self, pitch, amp, harms='piano', q=8, path=None, feedback=0, mul=1, add=0):
        PyoObject.__init__(self, mul, add)

        self._q = Sig(q)
        self._path = path

        self._scaleHarmToFactor = lambda x: 2. ** (x / 12.)
        self._scaleFactorToHarm = lambda x: math.log(x,2)*12.

        if isinstance(harms, list):
            self._harms = [self._scaleHarmToFactor(i) for i in harms]
        elif harms == 'piano':
            self._harms = [self._scaleHarmToFactor(i) for i in self.piano_harms]
        elif harms == 'organ':
            self._harms = [self._scaleHarmToFactor(i) for i in self.organ_harms]
        else:
            raise ValueError("harms attribute must be 'piano', 'organ', or a list of harmonics (in semitones)")

        if path is None:
            self._source = Noise(amp)
        else:
            assert os.path.exists(path), "path attribute must be a valid path to a sound file"
            self._snd_table = SndTable(path, chnl=0)
            self._feedback = Sig(feedback)
            self._source_gain = Sig(1, mul=amp)
            self._source = OscLoop(self._snd_table, freq=self._snd_table.getRate(),
                                   feedback=self._feedback, mul=self._source_gain)

        self._res_objs = []
        for i in range(len(amp)):
            self._res_objs.append(Resonx(self._source[i], freq=[pitch[i] * factor for factor in self._harms],
                                   q=self._q, mul=[j / j ** 1.15 for j in range(1, len(self._harms) + 1)])
                            )

        self._output = Mix(self._res_objs, mul=mul, add=add)
        self._base_objs = self._output.getBaseObjects()

    def play(self, dur=0, delay=0):
        for obj in self._res_objs:
            obj.play(dur, delay)
        self._feedback.play(dur, delay)
        self._q.play(dur, delay)
        self._source.play(dur, delay)
        self._output.play(dur, delay)
        return PyoObject.play(self, dur, delay)

    def stop(self):
        for obj in self._res_objs:
            obj.stop()
        self._feedback.stop()
        self._q.stop()
        self._source.stop()
        self._output.stop()
        return PyoObject.stop(self)

    def out(self, chnl=0, inc=1, dur=0, delay=0):
        for obj in self._res_objs:
            obj.play(dur, delay)
        self._feedback.play(dur, delay)
        self._q.play(dur, delay)
        self._source.play(dur, delay)
        self._output.play(dur, delay)
        return PyoObject.out(self, chnl, inc, dur, delay)

    def setSourceGain(self, x):
        if self._path is None:
            raise AttributeError("source gain attribute not initialized")
        self._source_gain.value = x

    def setFeedback(self, x):
        if self._path is None:
            raise AttributeError("feedback attribute not initialized")
        self._feedback.value = x

    def setQ(self, x):
        if self._path is None:
            raise AttributeError("q attribute not initialized")
        self._q.value = x

    def setPath(self, path):
        assert os.path.exists(path), "path attribute must be a valid path to a sound file"
        if self._path is None:
            raise RuntimeError("source type can only be determined at initialization time")
        self._snd_table.setSound(path)
        self._path = path

    def getSourceGain(self):
        if self._path is None:
            raise AttributeError("source gain attribute not initialized")
        return self._source_gain.value

    def getFeedback(self):
        if self._path is None:
            raise AttributeError("feedback attribute not initialized")
        return self._feedback.value

    def getQ(self):
        if self._path is None:
            raise AttributeError("q attribute not initialized")
        return self._q.value

    def getPath(self):
        if self._path is None:
            raise AttributeError("path attribute not initialized")
        return self._path

    @property
    def gain(self):
        return self.getSourceGain()
    @gain.setter
    def gain(self, x):
        self.setSourceGain(x)

    @property
    def feedback(self):
        return self.getFeedback()
    @feedback.setter
    def feedback(self, x):
        self.setFeedback(x)

    @property
    def q(self):
        return self.getQ()
    @q.setter
    def q(self, x):
        self.setQ(x)

    @property
    def path(self):
        return self.getPath()
    @path.setter
    def path(self, x):
        self.setPath(x)

    def ctrl(self, *args, **kwargs):
        print("ctrl method not implemented for ResoNoise class")