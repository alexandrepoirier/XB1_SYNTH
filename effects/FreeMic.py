from pyo import *
from .SigVel import SigVel

class FreeMic(PyoObject):
    def __init__(self, input, xaxis, zaxis, mul=1, add=0):
        PyoObject.__init__(self, mul, add)
        assert len(input) <= 2, "FreeMic only supports mono or stereo inputs"
        self._input = input
        self._xaxis = Sig(xaxis)
        self._zaxis = Sig(zaxis)
        self._counter = 0
        self._max_count = 5

        self._xaxis_vel = SigVel(xaxis, inmin=0, inmax=1, damp=2, mul=3, add=0).play()

        self._pitch_shifter = Harmonizer(input, transpo=self._xaxis_vel)
        self._pan = Pan(self._pitch_shifter, pan=self._xaxis, mul=Scale(self._zaxis, outmin=1, outmax=.2))

        self._filter = ButLP(input=Sig(self._pitch_shifter, mul=self._zaxis),
                             freq=Scale(self._zaxis, outmin=22000, outmax=10000))
        self._rev = STRev(self._filter, inpos=self._xaxis, revtime=.7, cutoff=8000, bal=1, roomSize=1,
                          mul=Scale(self._zaxis, outmin=1, outmax=.5, exp=3))

        self._output = Mix([self._pan, self._rev], voices=2, mul=mul, add=add)
        self._base_objs = self._output.getBaseObjects()

    def out(self, chnl=0, inc=1, dur=0, delay=0):
        self._xaxis_vel.play(dur, delay)
        self._zaxis.play(dur, delay)
        self._pitch_shifter.play(dur, delay)
        self._filter.play(dur, delay)
        self._rev.play(dur, delay)
        return PyoObject.out(self, chnl, inc, dur, delay)

    def play(self, dur=0, delay=0):
        self._xaxis_vel.play(dur, delay)
        self._zaxis.play(dur, delay)
        self._pitch_shifter.play(dur, delay)
        self._filter.play(dur, delay)
        self._rev.play(dur, delay)
        return PyoObject.play(self, dur, delay)

    def stop(self):
        self._xaxis_vel.stop()
        self._zaxis.stop()
        self._pitch_shifter.stop()
        self._filter.stop()
        self._rev.stop()
        return PyoObject.stop(self)

    @property
    def xaxis(self):
        return self._xaxis

    @xaxis.setter
    def xaxis(self, x):
        self._xaxis.value = x

    @property
    def zaxis(self):
        return self._zaxis

    @zaxis.setter
    def zaxis(self, z):
        self._zaxis.value = z