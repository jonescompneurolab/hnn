import numpy as np

from bokeh.layouts import gridplot
from bokeh.plotting import figure, show, output_file

x = np.linspace(0, 4*np.pi, 100)
y = np.sin(x)

TOOLS = "pan,wheel_zoom,box_zoom,reset,save,box_select"


p2 = figure(title="Another Legend Example", tools=TOOLS)

p2.line(x, y, legend="sin(x)")
output_file("legend.html", title="legend.py example")
show(p2)  # open a browser 