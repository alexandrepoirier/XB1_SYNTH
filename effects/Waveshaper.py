from pyo import *

class Waveshaper(PyoObject):
    def __init__(self, input, gain=0.686306, cutoff=20000, mul=1, add=0):
        PyoObject.__init__(self, mul, add)
        self._input = input
        self._gain = Sig(gain)
        self._cutoff = cutoff
        self._in_fader = InputFader(input)
        in_fader, gain, cutoff, mul, add, lmax = convertArgsToLists(self._in_fader, self._gain, cutoff, mul, add)

        # Waveshaping function
        x = in_fader * self._gain
        a = 1 + Exp( Sqrt( Abs(x) ) * -0.75)
        self._func = ( Exp(x) - Exp(-x * a) ) / ( Exp(x) + 1./Exp(x) )

        #Filter and output
        self._lowpass = ButLP(self._func, cutoff)
        self._output = Sig(self._lowpass, mul, add)
        self._base_objs = self._output.getBaseObjects()

    def play(self, dur=0, delay=0):
        self._gain.play(dur, delay)
        self._lowpass.play(dur, delay)
        return PyoObject.play(self, dur, delay)

    def stop(self):
        self._gain.stop()
        self._lowpass.stop()
        return PyoObject.stop(self)

    def out(self, chnl=0, inc=1, dur=0, delay=0):
        self._gain.play(dur, delay)
        self._lowpass.play(dur, delay)
        return PyoObject.out(self, chnl, inc, dur, delay)

    def setInput(self, x, fadetime=0.05):
        """
        Replace the `input` attribute.

        :Args:

            x : PyoObject
                New signal to process.
            fadetime : float, optional
                Crossfade time between old and new input. Defaults to 0.05.
        """
        self._input = x
        self._in_fader.setInput(x, fadetime)

    def setGain(self, x):
        """float or PyoObject. Gain factor."""
        self._gain.value = x

    def setCutoff(self, x):
        """float or PyoObject. Cutoff frequency for the Butterworth lowpass filter."""
        self._cutoff = x
        self._lowpass.freq = x

    @property
    def input(self):
        return self._input
    @input.setter
    def input(self, x): self.setInput(x)

    @property
    def gain(self):
        return self._gain.get()
    @gain.setter
    def gain(self, x): self.setGain(x)

    @property
    def cutoff(self):
        return self._lowpass.freq
    @cutoff.setter
    def cutoff(self, x): self.setCutoff(x)

    def ctrl(self, map_list=None, title=None, wxnoserver=False):
        self._map_list = [SLMap(0., 1., "lin", "gain", self._gain.get(), "float"),
                          SLMap(20, 20000, "log", "cutoff", self._cutoff, "float"),
                          SLMapMul(self._mul)]
        PyoObject.ctrl(self, map_list, title, wxnoserver)