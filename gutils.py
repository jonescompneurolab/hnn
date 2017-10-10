from PyQt5.QtCore import QCoreApplication
from PyQt5 import QtGui

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

# get new window width, height scaled by current screen resolution relative to original development resolution
def scalegeom (width, height):
  devwidth, devheight = 2880.0, 1620.0 # resolution used for development - used to scale window height/width
  screenwidth, screenheight = getscreengeom()
  widthnew = int((screenwidth / devwidth) * width)
  heightnew = int((screenheight / devheight) * height)
  return widthnew, heightnew

# scale font size
def scalefont (fsize):
  pass # devfont

