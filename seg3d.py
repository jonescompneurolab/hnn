# from pt3d of section, calculate the 3d location of segment centers, or
# a list of 3d points for each segment where the first and last 3-d points
# are the segment boundaries
# written by mh

from neuron import h

def segment_centers_3d (sec):
  ''' return list of x, y, z tuples for centers of non-zero area segments '''
  # vector of arc values of segment centers
  arcseg = h.Vector([seg.x for seg in sec])
  return interpolate(pt3d(sec), arcseg)

def segment_points_3d (sec):
  ''' return list of nseg length list of x,y,z tuples for segments
      first and last xyz tuple are the ends of the segment '''
  # vector of arc values of segment edges (nseg+1)
  arcseg = h.Vector(sec.nseg + 1).indgen().div(sec.nseg)
  n = int(sec.n3d())
  axyz = pt3d(sec)
  xyz = interpolate(axyz, arcseg)
  # organize into [[(x,y,z)]*nseg] but remove end identical points in [(x,y,z)]
  ret = []
  j = 0 # index into axyz vectors;
  for iseg in range(int(sec.nseg)):
    segitem = []
    a1 = arcseg[iseg] # proximal edge
    a2 = arcseg[iseg + 1] # distal edge
    segitem.append(xyz[iseg])
    while j < n and axyz[0][j] < a2: # insert the ones > a1 and less than a2
      a, pt =  axyz[0][j], (axyz[1][j], axyz[2][j], axyz[3][j])
      if a > a1:
        segitem.append(pt)
      j += 1
    segitem.append(xyz[iseg + 1])
    ret.append(segitem)
  return ret

def pt3d (sec):
  ''' return list of arc, x, y, z vectors from pt3d info of sec '''
  n = int(sec.n3d())
  #list of 3d point vectors
  sec.push()
  axyz = [h.Vector([f(i) for i in range(n)]) for f in [h.arc3d, h.x3d, h.y3d, h.z3d]]
  h.pop_section()
  axyz[0].div(sec.L)
  return axyz

def interpolate (axyz, arcvec):
  ''' return list of x, y, z tuples at the arcvec locations '''
  #interpolate onto arcvec
  xyz = [v.c().interpolate(arcvec, axyz[0]) for v in axyz[1:]]
  return [(xyz[0][i],xyz[1][i],xyz[2][i]) for i in range(len(xyz[0]))]

def drawsec (sec):
  # draw original 3d points (x,y values). Not using Shape because of origin issues
  g = h.Graph(0)
  g.view(2)
  n = int(sec.n3d())
  g.beginline(1, 4)
  for i in range(n):
    g.line(sec.x3d(i), sec.y3d(i))
  return g

def test_segment_centers (sec, g):
  xyz = segment_centers_3d(sec)
  for x in xyz:
    #print (x)
    g.mark(x[0], x[1], 'O', 10, 2, 1)
  g.exec_menu("View = plot")

def test_segment_points (sec, g):
  xyzsegs = segment_points_3d(sec)
  for iseg, xyzseg in enumerate(xyzsegs):
    color = 4 + iseg%2 #blue, green
    g.beginline(color, 1)
    for x,y,z in xyzseg:
      g.line(x, y)

if __name__ == '__main__':
  # load pyramidal of neurondemo
  from neuron import gui
  h.load_file(h.neuronhome() + '/demo/pyramid.nrn')
  s = h.dendrite_1[8] #proximal apical
  s.nseg = 5
  #h.load_file(h.neuronhome() + '/demo/pyramid.ses')

  g = drawsec(s)
  test_segment_points(s, g)
  test_segment_centers(s, g)

