#!/usr/bin/env python

"""

an example of using the multigrid class to solve Laplace's equation.  Here, we
solve

u_xx + u_yy = -2[(1-6x**2)y**2(1-y**2) + (1-6y**2)x**2(1-x**2)]
u = 0 on the boundary

this is the example from page 64 of the book `A Multigrid Tutorial, 2nd Ed.'

The analytic solution is u(x,y) = (x**2 - x**4)(y**4 - y**2)

"""

from __future__ import print_function

import sys

import numpy
import mesh.patch as patch
import variable_coeff_MG as MG
import pylab

pi = numpy.pi
sin = numpy.sin
cos = numpy.cos

# the analytic solution
def true(x,y):
    return sin(pi*x)*sin(pi*y)


# the coefficients
def alpha(x,y):
    #return x*(1+x) + y*(1-y)
    return numpy.ones_like(x)

# the L2 error norm
def error(myg, r):

    # L2 norm of elements in r, multiplied by dx to
    # normalize
    return numpy.sqrt(myg.dx*myg.dy*numpy.sum((r[myg.ilo:myg.ihi+1,
                                                 myg.jlo:myg.jhi+1]**2).flat))


# the righthand side
def f(x,y):
    #return pi*(2*x + 1)*sin(pi*y)*cos(pi*x) + \
    #    pi*(2*y + 1)*sin(pi*x)*cos(pi*y) - \
    #    2*pi**2*(x*(x + 1) + y*(y + 1))*sin(pi*x)*sin(pi*y)
    return -2.0*pi**2*sin(pi*x)*sin(pi*y)


                
# test the multigrid solver
nx = 8
ny = nx


# create the coefficient variable
g = patch.Grid2d(nx, ny, ng=1)
d = patch.CellCenterData2d(g)
bc_c = patch.BCObject(xlb="periodic", xrb="periodic",
                      ylb="periodic", yrb="periodic")
d.register_var("c", bc_c)
d.create()

c = d.get_var("c")
c[:,:] = alpha(g.x2d, g.y2d)


# check whether the RHS sums to zero (necessary for periodic)
rhs = f(g.x2d, g.y2d)
print(numpy.sum(rhs[g.ilo:g.ihi+1,g.jlo:g.jhi+1]))




# create the multigrid object
a = MG.VarCoeffCCMG2d(nx, ny,
                      xl_BC_type="periodic", yl_BC_type="periodic",
                      xr_BC_type="periodic", yr_BC_type="periodic",
                      coeffs=c, coeffs_bc=bc_c,
                      verbose=1)


# debugging
#for i in range(a.nlevels):
#    print(i)
#    print(a.grids[i].get_var("coeffs"))


# initialize the solution to 0
a.init_zeros()

# initialize the RHS using the function f
rhs = f(a.x2d, a.y2d)
a.init_RHS(rhs)

# solve to a relative tolerance of 1.e-11
a.solve(rtol=1.e-11)

# alternately, we can just use smoothing by uncommenting the following
#a.smooth(a.nlevels-1,50000)

# get the solution 
v = a.get_solution()

# compute the error from the analytic solution
b = true(a.x2d,a.y2d)
e = v - b

print(" L2 error from true solution = %g\n rel. err from previous cycle = %g\n num. cycles = %d" % \
      (error(a.soln_grid, e), a.relative_error, a.num_cycles))


# plot it
pylab.figure(num=1, figsize=(5.0,5.0), dpi=100, facecolor='w')

pylab.imshow(numpy.transpose(v[a.ilo:a.ihi+1,a.jlo:a.jhi+1]), 
          interpolation="nearest", origin="lower",
          extent=[a.xmin, a.xmax, a.ymin, a.ymax])


pylab.xlabel("x")
pylab.ylabel("y")

pylab.savefig("mg_test.png")


# store the output for later comparison
my_data = a.get_solution_object()
my_data.write("mg_test")


