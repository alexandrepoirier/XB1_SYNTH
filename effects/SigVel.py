from pyo import *

class SigVel(PyoObject):
    def __init__(self, input, inmin, inmax, time=0.2, damp=2, mul=1, add=0):
        PyoObject.__init__(self, mul, add)

        self._input = input.mix() if len(input)>1 else input
        assert isinstance(inmin, float) or isinstance(inmin, int), "inmin and inmax parameters must be floats or ints"
        assert isinstance(inmax, float) or isinstance(inmax, int), "inmin and inmax parameters must be floats or ints"
        self._inmin = inmin
        self._inmax = inmax
        self._inrange = float(inmax-inmin)
        self._normalize = lambda x: (x-self._inmin)/self._inrange
        self._damp = 1./damp
        self._last_sample = 0

        self._buffer = NewTable(0.1, chnls=1)
        self._filler = TableRec(self._input, self._buffer)
        self._callback = TrigFunc(self._filler['trig'], self._process)

        self._output = SigTo(0, time, mul=mul, add=add)
        self._base_objs = self._output.getBaseObjects()

    def _process(self):
        sample = self._normalize(self._buffer.get(0))
        self._filler.play()
        self._output.value = abs(sample-self._last_sample)*self._damp
        self._last_sample = sample

    def out(self, *args, **kwargs):
        pass

    def play(self, dur=0, delay=0):
        self._last_avg = 0
        self._filler.play(dur, delay)
        self._callback.play(dur, delay)
        return PyoObject.play(self, dur, delay)

    def stop(self):
        self._callback.stop()
        self._filler.stop()
        return PyoObject.stop(self)

    def setInput(self, value):
        self._filler.setInput(value)
        self._input = value

    def setRange(self, inmin, inmax):
        self._inmin = inmin
        self._inmax = inmax
        self._inrange = float(inmax - inmin)

    def setTime(self, value):
        self._output.time = value

    def setDamp(self, value):
        self._damp = 1./value

    @property
    def input(self):
        return self._input

    @input.setter
    def input(self, value):
        self.setInput(value)

    @property
    def inmin(self):
        return self._inmin

    @property
    def inmax(self):
        return self._inmax

    @property
    def range(self):
        return self._inrange
