# DEPRECATE

import logging
from neuron import h

from jupyter_geppetto.geppetto_comm import GeppettoCoreAPI as G
from neuron_ui import neuron_utils
from neuron_ui import neuron_geometries_utils

import params_default
from conf import fcfg,dconf
from simdat import *

class HNN:
  def __init__ (self):
    logging.debug('Loading HNN')
    neuron_utils.createProject(name='HNN')
    import run

    self.t_vec = h.Vector()
    self.t_vec.record(h._ref_t)
    neuron_utils.createStateVariable(id='time', name='time',
                                     units='ms', python_variable={"record_variable": self.t_vec,
                                                                  "segment": None})

    neuron_geometries_utils.extractGeometries()

    logging.debug('HNN loaded')

    self.RunSimButton = neuron_utils.add_button('Run', extraData={'commands':[]})
    self.StopSimButton = neuron_utils.add_button('Stop',extraData={'commands':[]})
    self.SetParams = neuron_utils.add_button('Set Parameters')
    self.BasePanel = neuron_utils.add_panel('HNN Control', items=[self.RunSimButton,self.StopSimButton,self.SetParams],widget_id='hnnBasePanel')
    self.BasePanel.on_close(self.close)
    self.BasePanel.display()

  def close (self):
    self.BasePanel.close()
    del self.BasePanel

""" 
to start (first 2 commands from console)

./NEURON-UI/NEURON-UI &
jupyter console --existing
import os
os.chdir('/u/samn/hnn/NEURON-UI/neuron_ui/models/hnn')
import hnn_nrnui
net=hnn_nrnui.HNN()

"""

