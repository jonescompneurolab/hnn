'''
init.py

Starting script to run NetPyNE-based HNN model.

Usage:
    python init.py # Run simulation, optionally plot a raster

MPI usage:
    mpiexec -n 4 nrniv -python -mpi init.py

Contributors: salvadordura@gmail.com
'''

from netpyne import sim
from utils import setCfgFromFile

cfgFile = '../param/ERPYes100Trials.param' # ../param/netpyne_test.param' ../param/ERPYes100Trials.param' # ../param/OnlyRhythmicProx.param'

from cfg import cfg
cfg = setCfgFromFile(cfgFile, cfg)
from netParams import netParams

sim.create(simConfig = cfg, netParams = netParams)  # SimulateAnalyze

saveJsonPsection = 1
saveJsonConns = 0
saveSpks = 0
saveDipole = 0

# save json with psection
if saveJsonPsection:
    import json
    data = {}
    remove = ['cell', 'regions','species', 'point_processes', 'hoc_internal_name', 'name']#, 'morphology']
    removeMorph = ['parent', 'trueparent']
    for icell, c in enumerate(sim.net.cells):
        try:
            data[icell] = {}
            cellType =  c.tags['cellType']
            for isec, sec in enumerate(c.secs.values()):
                name = cellType + '_' + str(sec['hObj'].name()).split('.')[-1]
                data[icell][ name] = sec['hObj'].psection()
                for x in remove:
                    del data[icell][name][x]
                for key in removeMorph:
                    if key in data[icell][name]['morphology']:
                        del data[icell][name]['morphology'][key]
                        #data[icell][name]['morphology'][key] = str(data[icell][name]['morphology'][key])
        except:
            print('Error processing %d'%(icell))

    with open('hnn_secs_netpyne.json', 'w') as f:
        json.dump(data, f)


# save json with psection
if saveJsonConns:
    import json
    data = {}
    data_wrong = []
    
    from neuron import h
    conns = list(h.List('NetCon'))
    
    vecstimCount = 0
    for conn in conns:
        #try:
            if str(conn.pre()).startswith('VecStim'):
                preGid = 'VecStim'
            elif conn.precell(): 
                preGid = conn.precell().gid

            postGid = conn.postcell().gid
            sec_loc = str(conn.postseg()).split('>.')[1]
            sec = sec_loc.split('(')[0]
            loc = sec_loc.split('(')[1][:-1]
            weight = conn.weight[0]
            delay = conn.delay if weight > 0.0 else 0.0
            synTau1 = conn.syn().tau1
            synTau2 = conn.syn().tau2
            key = '%s_%s_%s_%s_%s_%s' % (str(preGid), str(postGid), sec, str(loc), str(synTau1), str(synTau2))
            if key in data:
                data[key].append([weight, delay])
            else:
                data[key] = [[weight, delay]]
        # except:
        #     print(str(conn.precell()), str(conn.postseg()))
        #     data_wrong.append([str(conn.precell()), str(conn.postseg())])

    print('Errors: %d'%(len(data_wrong)))
    with open('hnn_conns_netpyne.json', 'w') as f:
        json.dump(data, f)

if saveSpks:
    sim.simulate()
    sim.analyze()
    with open('spikes_netpyne_erp_2.txt', 'w') as fspkout:
        for spkt, spkid in zip(sim.simData['spkt'], sim.simData['spkid']):
            fspkout.write('%3.2f\t%d\n' % (spkt, spkid))

if saveDipole:
    sim.simulate()
    sim.analyze()
    
    import numpy as np

    # renormalize the dipole and save
    def baseline_renormalize():
        # N_pyr cells in grid. This is PER LAYER
        N_pyr = sim.cfg.N_pyr_x * sim.cfg.N_pyr_y
        dpl_offset = {
            # these values will be subtracted
            'L2': N_pyr * 0.0443,
            'L5': N_pyr * -49.0502
        }

        # L2 dipole offset can be roughly baseline shifted over the entire range of t
        dpl = {'L2': np.array(sim.simData['dipole']['L2']),
               'L5': np.array(sim.simData['dipole']['L5'])}
        dpl['L2'] -= dpl_offset['L2']

        m = 3.4770508e-3
        b = -51.231085
        # these values were fit over the range [750., 5000]
        t1 = 750.
        m1 = 1.01e-4
        b1 = -48.412078

        t = sim.simData['t']

        # piecewise normalization
        dpl['L5'][t <= 37.] -= dpl_offset['L5']
        dpl['L5'][(t > 37.) & (t < t1)] -= N_pyr * (m * t[(t > 37.) & (t < t1)] + b)
        dpl['L5'][t >= t1] -= N_pyr * (m1 * t[t >= t1] + b1)
        # recalculate the aggregate dipole based on the baseline normalized ones
        dpl['agg'] = dpl['L2'] + dpl['L5']

        return dpl

    # convolve with a hamming window
    def hammfilt(x, winsz):
        from pylab import convolve
        from numpy import hamming
        win = hamming(winsz)
        win /= sum(win)
        return convolve(x,win,'same')

    # baseline renormalize
    dpl = baseline_renormalize()

    # convert units from fAm to nAm, rescale and smooth
    for key in dpl.keys():
        dpl[key] *= 1e-6 * sim.cfg.dipole_scalefctr
        
        if sim.cfg.dipole_smooth_win > 0:
            dpl[key] = hammfilt(dpl[key], sim.cfg.dipole_smooth_win/sim.cfg.dt)

        # Set index 0 to 0
        #dpl[key][0] = 0.0

    t_vec = sim.simData['t']
    dp_rec_L2 = dpl['L2']
    dp_rec_L5 = dpl['L5']
    with open('dpl_netpyne_erp_2.txt', 'w') as f:
        for k in range(len(sim.simData['t'])):
            f.write("%03.3f\t" % t_vec[k])
            f.write("%5.4f\t" % (dp_rec_L2[k] + dp_rec_L5[k]))
            f.write("%5.4f\t" % dp_rec_L2[k])
            f.write("%5.4f\n" % dp_rec_L5[k])

