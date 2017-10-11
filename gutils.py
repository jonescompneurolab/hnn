from PyQt5.QtCore import QCoreApplication
from PyQt5 import QtGui

# some graphics utilities

# use pyqt5 to get screen resolution
def getscreengeom ():
  width,height = 2880, 1620 # default width,height - used for development
  app = QCoreApplication.instance() # can only have 1 instance of qtapp; get that instance
  app.setDesktopSettingsAware(True)
  if len(app.screens()) > 0:
    screen = app.screens()[0]
    geom = screen.geometry()
    return geom.width(), geom.height()
  else:
    return width, height

# check if display has low resolution
def lowresdisplay ():
  w, h = getscreengeom()
  return w < 1400 or h < 700

# get DPI for use in matplotlib figures (part of simulation output canvas - in simdat.py)
def getmplDPI ():
  if lowresdisplay(): return 40
  return 120

# get new window width, height scaled by current screen resolution relative to original development resolution
def scalegeom (width, height):
  devwidth, devheight = 2880.0, 1620.0 # resolution used for development - used to scale window height/width
  screenwidth, screenheight = getscreengeom()
  widthnew = int((screenwidth / devwidth) * width)
  heightnew = int((screenheight / devheight) * height)
  return widthnew, heightnew

# set dialog's position (x,y) and rescale geometry based on original width and height and development resolution
def setscalegeom (dlg, x, y, origw, origh):
  nw, nh = scalegeom(origw, origh)
  # print('origw,origh:',origw, origh,'nw,nh:',nw, nh)
  dlg.setGeometry(x, y, int(nw), int(nh))
  return int(nw), int(nh)

# set dialog in center of screen and rescale size based on original width and height and development resolution
def setscalegeomcenter (dlg, origw, origh):
  nw, nh = scalegeom(origw, origh)
  # print('origw,origh:',origw, origh,'nw,nh:',nw, nh)
  sw, sh = getscreengeom()
  x = (sw-nw)/2
  y = (sh-nh)/2
  dlg.setGeometry(x, y, int(nw), int(nh))
  return int(nw), int(nh)

# scale font size
def scalefont (fsize):
  pass # devfont

