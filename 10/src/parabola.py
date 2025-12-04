import numpy as np
import matplotlib.pyplot as plt
a = 1.
b =1.
c = 2
xlo = 0
xhi = 10
npoints = 100
x = np.linspace(xlo, xhi, npoints)
y = a*x**2 + b*x + c
plt.plot(x,y)
plt.savefig("parabola.png")