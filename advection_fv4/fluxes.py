import mesh.reconstruction as reconstruction

def fluxes(my_data, rp, dt):
    """Construct the fluxes through the interfaces for the linear advection
    equation:

      a  + u a  + v a  = 0
       t      x      y

    We use a fourth-order Godunov method to construct the interface
    states, using Runge-Kutta integration.  Since this is 4th-order,
    we need to be aware of the difference between a face-average and
    face-center for the fluxes.

    In the pure advection case, there is no Riemann problem we need to
    solve -- we just simply do upwinding.  So there is only one 'state'
    at each interface, and the zone the information comes from depends
    on the sign of the velocity.

    Our convection is that the fluxes are going to be defined on the
    left edge of the computational zones


     |             |             |             |
     |             |             |             |
    -+------+------+------+------+------+------+--
     |     i-1     |      i      |     i+1     |

              a_l,i  a_r,i   a_l,i+1


    a_r,i and a_l,i+1 are computed using the information in
    zone i,j.

    Parameters
    ----------
    my_data : FV object
        The data object containing the grid and advective scalar that
        we are advecting.
    rp : RuntimeParameters object
        The runtime parameters for the simulation
    dt : float
        The timestep we are advancing through.
    scalar_name : str
        The name of the variable contained in my_data that we are
        advecting

    Returns
    -------
    out : ndarray, ndarray
        The fluxes averaged over the x and y faces

    """

    myg = my_data.grid

    a = my_data.get_var("density")

    # get the advection velocities
    u = rp.get_param("advection.u")
    v = rp.get_param("advection.v")


    # interpolate cell-average a to face-averaged a on interfaces in each
    # dimension
    a_x = myg.scratch_array()
    a_x.v(buf=1)[:,:] = 7./12.*(a.ip(-1, buf=1) + a.v(buf=1)) - \
                        1./12.*(a.ip(-2, buf=1) + a.ip(1, buf=1))

    a_y = myg.scratch_array()
    a_y.v(buf=1)[:,:] = 7./12.*(a.jp(-1, buf=1) + a.v(buf=1)) - \
                        1./12.*(a.jp(-2, buf=1) + a.jp(1, buf=1))


    # calculate the face-centered a using the transverse Laplacian
    a_x_cc = myg.scratch_array()
    bufx = (0, 1, 0, 0)
    a_x_cc.v(buf=bufx)[:,:] = a_x.v(buf=bufx) - \
        1./24*(a_x.jp(-1, buf=bufx) - 2*a_x.v(buf=bufx) + a_x.jp(1, buf=bufx))

    a_y_cc = myg.scratch_array()
    bufy = (0, 0, 0, 1)
    a_y_cc.v(buf=bufy)[:,:] = a_y.v(buf=bufy) - \
        1./24*(a_y.ip(-1, buf=bufy) - 2*a_y.v(buf=bufy) + a_y.ip(1, buf=bufy))


    # compute the face-averaged fluxes
    F_x = myg.scratch_array()
    F_x_avg = u*a_x
    F_x.v(buf=bufx)[:,:] = u*a_x_cc.v(buf=bufx) + \
        1./24*(F_x_avg.jp(-1, buf=bufx) - 2*F_x_avg.v(buf=bufx) + F_x_avg.jp(1, buf=bufx))

    F_y = myg.scratch_array()
    F_y_avg = v*a_y
    F_y.v(buf=bufy)[:,:] = v*a_y_cc.v(buf=bufy) + \
        1./24*(F_y_avg.ip(-1, buf=bufy) - 2*F_y_avg.v(buf=bufy) + F_y_avg.ip(1, buf=bufy))

    return F_x, F_y
