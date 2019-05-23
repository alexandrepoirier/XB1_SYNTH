class VelocityTracker:
    def __init__(self, fps):
        self._tick = 0
        self._buffer_tick = 0
        self._FPS = fps
        self._instant_velocity = 0
        self._short_term_velocity = 0
        self._long_term_velocity = 0
        self._BUFFER_LENGTH = fps // 5
        self._buffer = [0]*self._BUFFER_LENGTH
        self._history = [0]*fps
        self._getDiscreetVel = lambda i: abs(self._buffer[i % self._BUFFER_LENGTH] - self._buffer[(i - 1) % self._BUFFER_LENGTH])

    def __getitem__(self, item):
        if item == 'InstantVel': return self._instant_velocity
        elif item == 'ShortTermVel': return self._short_term_velocity
        elif item == 'LongTermVel': return self._long_term_velocity

    def _computeVelocity(self):
        self._instant_velocity = self._getDiscreetVel(self._buffer_tick)
        vel_sum = 0
        for i in range(self._BUFFER_LENGTH):
            vel_sum += self._getDiscreetVel(i)
        self._short_term_velocity = vel_sum / self._BUFFER_LENGTH
        self._history[self._tick] = self._short_term_velocity
        self._long_term_velocity = sum(self._history) / self._FPS

    def tick(self, value):
        self._tick = (self._tick + 1) % self._FPS
        self._buffer_tick = self._tick % self._BUFFER_LENGTH
        self._buffer[self._buffer_tick] = value
        self._computeVelocity()


class StickVelocityTracker:
    def __init__(self, fps):
        self._x_axis = VelocityTracker(fps)
        self._y_axis = VelocityTracker(fps)

    def __getitem__(self, item):
        if item == 'X': return self._x_axis
        elif item == 'Y': return self._y_axis

    def tick(self, x_value, y_value):
        self._x_axis.tick(x_value)
        self._y_axis.tick(y_value)


class TriggerVelocityTracker(VelocityTracker):
    def __init__(self, fps):
        VelocityTracker.__init__(self, fps)


class DensityTracker:
    def __init__(self, buttons, fps):
        self._btns = buttons
        self._FPS = fps
        self._tick = 0
        self._time_tick = 0 # in seconds
        self._BUFFER_LENGTH = 60 # in seconds
        self._BUFFER_LENGTH_TICKS = self._BUFFER_LENGTH * self._FPS # in ticks
        self._buffer = [0] * self._BUFFER_LENGTH_TICKS
        self._btns_last_state = {}
        for btn in self._btns:
            self._btns_last_state[btn] = 0

        # 0-10 sec. accounts for 50%
        # 10-20 sec. accounts for 30%
        # 30-60 sec. accounts for 20%
        self._weighting = {(0, int(self._BUFFER_LENGTH_TICKS // 8)) : .75,
                           (int(self._BUFFER_LENGTH_TICKS // 8), int(self._BUFFER_LENGTH_TICKS // 2)) : .15,
                           (int(self._BUFFER_LENGTH_TICKS // 2), self._BUFFER_LENGTH_TICKS) : .1}
        self._density = 0

    def _readValues(self, values):
        pos = self._tick + (self._time_tick * self._FPS)
        self._buffer[pos] = 0
        for btn in self._btns:
            val = values[btn]
            if val != self._btns_last_state[btn]:
                self._btns_last_state[btn] = val
                if val:
                    self._buffer[pos] += 1

    def _computeDensity(self):
        pos = self._tick + (self._time_tick * self._FPS)
        self._density = 0
        for bracket, weight in self._weighting.items():
            bracket_total = 0
            for i in range(*bracket):
                bracket_total += self._buffer[(pos - i) % self._BUFFER_LENGTH_TICKS]
            self._density += bracket_total / (bracket[1]-bracket[0]) * weight
        self._density *= 60

    def tick(self, values):
        self._readValues(values)
        self._tick += 1
        if self._tick == self._FPS:
            self._tick = 0
            self._time_tick = (self._time_tick + 1) % self._BUFFER_LENGTH

    def get(self):
        self._computeDensity()
        return self._density
