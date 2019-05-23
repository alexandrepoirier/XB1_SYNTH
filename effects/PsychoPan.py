from pyo import *

class PsychoPan(PyoObject):
    """
    Uses the precedence effect coupled with a BP filter to pan a signal left and right.

    :Parent: :py:class:`PyoObject`

    :Args:

    input: PyoObject
        Input signal to pan.
    pan: float or PyoObject, optional
        Pan value between -1 and 1 inclusively.

    .. note::
        Only works on mono and stereo signals.
    """
    def __init__(self, input, pan=0, cutoff=3000, mul=1, add=0):
        PyoObject.__init__(self, mul, add)
        chnls = len(input)
        assert chnls <= 2, "PsychoPan: Input can only be mono or stereo"
        self._input = input
        self._pan = Sig(pan)
        self._max_delay = .025
        self._cutoff = cutoff
        self._q = .5
        # TODO permettre de specifier les attributs inmin et inmax
        self._left_pan = Scale(self._pan, inmin=0, inmax=0.5, outmin=1, outmax=0, exp=2)
        self._right_pan = Scale(self._pan, inmin=0.5, inmax=1, outmin=0, outmax=1, exp=2)

        if chnls == 1:
            self._delay = SmoothDelay([self._input, self._input],
                                delay=[self._right_pan * self._max_delay, self._left_pan * self._max_delay])
            self._dry_signal = Sig(0, add=[self._input * (1 - self._right_pan), self._input * (1 - self._left_pan)])
            self._band_pass = ButBP(self._delay, freq=self._cutoff, q=1, mul=[self._right_pan, self._left_pan])
            self._output = Mix([self._band_pass, self._dry_signal], voices=2, mul=mul,add=add)
        else:
            self._delay = SmoothDelay(self._input,
                                [self._right_pan * self._max_delay, self._left_pan * self._max_delay])
            self._left_dry_signal = Sig(self._input[0], mul=(1 - self._right_pan))
            self._right_dry_signal = Sig(self._input[1], mul=(1 - self._left_pan))
            self._band_pass = ButBP(self._delay, freq=self._cutoff, q=self._q, mul=[self._right_pan, self._left_pan])
            self._output = Mix([self._band_pass, self._left_dry_signal, self._right_dry_signal],
                               voices=2, mul=mul, add=add)

        self._base_objs = self._output.getBaseObjects()

    def play(self, dur=0, delay=0):
        self._left_pan.play(dur, delay)
        self._right_pan.play(dur, delay)
        self._delay.play(dur, delay)
        self._band_pass.play(dur, delay)
        self._output.play(dur, delay)
        return PyoObject.play(self, dur, delay)

    def stop(self):
        self._left_pan.stop()
        self._right_pan.stop()
        self._delay.stop()
        self._band_pass.stop()
        self._output.stop()
        return PyoObject.stop(self)

    def out(self, chnl=0, inc=1, dur=0, delay=0):
        self._left_pan.play(dur, delay)
        self._right_pan.play(dur, delay)
        self._delay.play(dur, delay)
        self._band_pass.play(dur, delay)
        self._output.play(dur, delay)
        return PyoObject.out(self, chnl, inc, dur, delay)

    def setInput(self, x):
        """
        Replace the `input` attribute.

        :Args:

            x : PyoObject
                New signal to process.
        """
        self._input = x
        self._delay.setInput(x)

    def setPan(self, x):
        """float or PyoObject. Pan factor."""
        self._pan.value = x

    def setCutoff(self, x):
        """float or PyoObject. Cutoff frequency for the Butterworth bandpass filter."""
        self._cutoff = x
        self._band_pass.freq = x

    @property
    def input(self):
        return self._input

    @input.setter
    def input(self, x):
        self.setInput(x)

    @property
    def pan(self):
        return self._pan.get()

    @pan.setter
    def pan(self, x):
        self.setPan(x)

    @property
    def cutoff(self):
        return self._cutoff

    @cutoff.setter
    def cutoff(self, x):
        self.setCutoff(x)