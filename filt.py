from pylab import convolve

# box filter
def boxfilt (x, winsz):
  win = [1.0/winsz for i in range(int(winsz))]
  return convolve(x,win,'same')
