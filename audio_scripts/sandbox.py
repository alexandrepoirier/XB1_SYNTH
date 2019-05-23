from pyo import *
s = Server(sr=48000).boot()
s.start()

# SCRIPT STARTS HERE

a = SfPlayer(SNDS_PATH + "/transparent.aif", loop=True)
split = BandSplit(a, num=4)
d = WGVerb(split[3], feedback=[.94,.90], cutoff=5000, bal=.25, mul=1)
mix = Mix([a, a, d], voices=2).out()

# SCRIPT ENDS HERE

s.gui(locals())
