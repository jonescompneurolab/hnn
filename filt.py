from pylab import convolve
from numpy import hamming
import numpy as np

# box filter
def boxfilt (x, winsz):
  win = [1.0/winsz for i in range(int(winsz))]
  return convolve(x,win,'same')

# convolve with a hamming window
def hammfilt (x, winsz):
  win = hamming(winsz)
  win /= sum(win)
  return convolve(x,win,'same')

# returns x
def emptyfilt (x, winsz):
  return np.array(x)

