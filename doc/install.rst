Installation
=======================================

Requirements
------------

HNN requires Python 3.x (`<www.python.org>`_) and the NEURON simulation environment (`<www.neuron.yale.edu>`_)
compiled to use Python3 and optimally, with MPI support. 

Required packages:
 #. MPI
 #. Matplotlib
 #. NEURON compiled with MPI, Python support - $PYTHONPATH must point to Python 3
 #. Numpy
 #. PyOpenGL
 #. Python3
 #. PyQt5
 #. pyqtgraph
 #. Scipy


Installers
----------

 #. `CentOS install script <https://bitbucket.org/samnemo/hnn/src/70f8db5fc7310a811378920d61954d0277abe8c8/installer/centos/build.sh?at=master>`_
 #. `Ubuntu install script <https://bitbucket.org/samnemo/hnn/src/70f8db5fc7310a811378920d61954d0277abe8c8/installer/ubuntu/build.sh?at=master>`_

To install using these scripts, download the relevant installer. Then from
a terminal, change into the directory with the ``build.sh`` script and run 
``sudo ./build.sh`` . **Note: you will need the sudo password.**

Mac OSX and Windows installers are currently under development.

All source code is available on bitbucket at: http://bitbucket.org/samnemo/hnn

