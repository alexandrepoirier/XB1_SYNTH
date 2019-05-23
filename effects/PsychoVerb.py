from pyo import *
import random

class PsychoVerb(PyoObject):
    """
        Reverb using 8 delay lines with randomly generated delay times.

        :Parent: :py:class:`PyoObject`

        :Args:

        input: PyoObject
            Input signal to pan.
        pan: float or PyoObject, optional
            Pan value between -1 and 1 inclusively.

        .. note::
            Only works on mono and stereo signals.
        """

    def __init__(self, input, feedback=0.2, damp=0, bal=0.5, chnl=2, mul=1, add=0):
        PyoObject.__init__(self, mul, add)
        self._input = input
        self._feedback = feedback
        self._damp = Sig(damp)
        self._bal = bal
        feedback, damp, bal, mul, add, lmax = convertArgsToLists(feedback, damp, bal, mul, add)
        # delay values
        self._delay_ranges = [(0.12,0.13), (0.11, 0.116), (0.106, 0.109), (0.092, 0.105),
                              (0.08, 0.09), (0.04, 0.06), (0.02, 0.038), (0.01, 0.018)]
        self._generateDelays()
        self._freq_index_list = [i for i in range(len(self._delay_ranges))]
        self._generateBaseFreqs()
        self._getFreq = lambda x: (x/float(len(self._delay_ranges)))**3*self._frange+self._fmin

        self._comp = Compress(self._input, thresh=-30, ratio=10, risetime=.15, falltime=.1, lookahead=25, knee=.8)
        # split bands
        self._bands_obj_list = [ButBP(self._comp, freq=self._getFreq(i), q=2) for i in self._freq_index_list]
        # early reflections going throug lowpass
        self._ERs_obj = SmoothDelay(self._bands_obj_list, delay=self._delay_times,
                                    feedback=self._feedback, maxdelay=0.2, mul=self._bal)
        self._lowpass_obj = ButLP(self._ERs_obj, freq=Scale(self._damp, inmin=0, inmax=1, outmin=22000, outmax=500))
        # late reflections
        self._LRs_obj_list = [SmoothDelay(self._lowpass_obj, delay=self._delay_times[0]*3, feedback=0.3)]
        for i in range(1, len(self._delay_ranges)):
            self._LRs_obj_list.append(SmoothDelay(self._LRs_obj_list[i-1], delay=self._delay_times[i]*3, feedback=0.3))
        self._LRs_obj_list[-1].mul = self._bal

        self._dry_obj = Sig(self._input, mul=1 - self._bal)
        self._output_obj = Mix([self._dry_obj, self._LRs_obj_list[-1]], voices=chnl, mul=mul, add=add)
        self._base_objs = self._output_obj.getBaseObjects()

    def _generateDelays(self):
        self._delay_times = []
        for elem in self._delay_ranges:
            self._delay_times.append(random.uniform(*elem))

    def _generateBaseFreqs(self):
        random.shuffle(self._freq_index_list)
        self._fmin = random.randint(300,500)
        self._fmax = random.randint(10000, 18000)
        self._frange = self._fmax - self._fmin

    def play(self, dur=0, delay=0):
        self._output_obj.play(dur, delay)
        return PyoObject.play(self, dur, delay)

    def stop(self):
        self._output_obj.stop()
        return PyoObject.stop(self)

    def out(self, chnl=0, inc=1, dur=0, delay=0):
        self._output_obj.play(dur, delay)
        return PyoObject.out(self, chnl, inc, dur, delay)

    def generate(self):
        self._generateDelays()
        self._ERs_obj.delay = self._delay_times
        self._generateBaseFreqs()
        for i, obj in enumerate(self._bands_obj_list):
            obj.freq = self._getFreq(self._freq_index_list[i])

    def dump(self):
        print(self)
        print("delay times: {}".format(self._delay_times))
        print("min freq: {}, max freq: {}".format(self._fmin, self._fmax))
        print("freq index list: {}".format(self._freq_index_list))

    def setDelayTimes(self, values):
        if not isinstance(values, list):
            print("PsychoVerb Error: expected list as argument")
            return
        if len(values) != len(self._delay_times):
            print("PsychoVerb Error: exactly {} values expected in list".format(len(self._delay_times)))
            return
        self._delay_times = values
        self._ERs_obj.delay = values

    def setRange(self, min, max):
        if min > max:
            print("PsychoVerb Error: min argument larger than max")
            return
        self._fmin = min
        self._fmax = max
        self._frange = max-min

    def setIndexList(self, index_list):
        if not isinstance(index_list, list):
            print("PsychoVerb Error: expected list as argument")
            return
        self._freq_index_list = index_list

    def setInput(self, x):
        """
        Replace the `input` attribute.

        :Args:

            x : PyoObject
                New signal to process.
        """
        self._input = x
        self._pre_delay_obj.setInput(x)

    @property
    def input(self):
        return self._input

    @input.setter
    def input(self, x):
        self.setInput(x)