from pyo import *
s = Server(sr=48000).boot()
s.start()

test = "port"

if test == "cloud":
    dens = Expseg([(0,1),(5,50)], loop=True, exp=5, initToFirstVal=True).play()
    m = Cloud(density=50, poly=2).play()
    tr = TrigRand(m, min=300, max=1000)
    tr_p = Port(tr, risetime=0.001, falltime=0.001)
    a = Sine(freq=tr_p, mul=0.2).out()

if test == "burst":
    env = CosTable([(0,0), (100,0.5), (500, 0.3), (4096,0.3), (8192,0)])
    m = Metro(2).play()
    tb = TrigBurst(m, time=0.15, count=[15,20], expand=[0.92,0.9], ampfade=0.85)
    amp = TrigEnv(tb, env, dur=tb["dur"], mul=tb["amp"]*0.3)
    a = Sine([800,600], mul=amp)
    rev = STRev(a, inpos=[0,1], revtime=1.5, cutoff=5000, bal=0.1).out()

if test == "euclid":
    t = CosTable([(0, 0), (100, 1), (500, .3), (8191, 0)])
    beat = Euclide(time=.125, taps=16, onsets=8, poly=1).play()
    trmid = TrigXnoiseMidi(beat, dist=12, mrange=(60, 96))
    trhz = Snap(trmid, choice=[0, 2, 3, 5, 7, 8, 10], scale=1)
    tr2 = TrigEnv(beat, table=t, dur=beat['dur'], mul=beat['amp'])
    a = Sine(freq=trhz, mul=tr2 * 0.3).out()

if test == "port":
    from random import uniform

    x = Sig(value=500)
    p = Port(x, risetime=.1, falltime=1)
    a = Sine(freq=[p, p * 1.01], mul=.2).out()

    def new_freq():
        x.value = uniform(400, 800)

    pat = Pattern(function=new_freq, time=1).play()

s.gui(locals())
