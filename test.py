from netpyne import sim

expData = {}
expData['x'] = range(5)
expData['y'] = [x * 2 for x in range(5)]
sim.analysis.iplotDipole(expData)