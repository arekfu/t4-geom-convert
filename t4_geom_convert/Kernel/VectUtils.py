# -*- coding: utf-8 -*-
'''
:author: Davide Mancusi
:date: 2019-09-19
'''

from math import sqrt, cos, sin


def scal(v1, v2):
    '''Yields the scalar product of `v1` and `v2`.'''
    a1, b1, c1 = v1
    a2, b2, c2 = v2
    result = a1*a2 + b1*b2 + c1*c2
    return float(result)


def vect(v1, v2):
    '''Yields the vector product of `v1` and `v2`.'''
    x1, y1, z1 = v1
    x2, y2, z2 = v2
    result = (y1*z2-z1*y2,x2*z1-x1*z2,x1*y2-y1*x2)
    return result


def mixed(v1, v2, v3):
    '''Yields the mixed product of `v1`, `v2` and `v3`.

    The mixed product is defined as `v1 · (v2 × v3)` and is equal to the
    determinant of the matrix having the components of `v1`, `v2` and `v3` as
    rows.
    '''
    return scal(v1, vect(v2, v3))


def rescale(a, v1):
    '''Return `v1` multiplied by a scalar `a`, as a new vector.'''
    x1, y1, z1 = v1
    return (a*x1, a*y1, a*z1)


def vsum(*args):
    '''Return the vector sum of its arguments.'''
    xsum = 0.
    ysum = 0.
    zsum = 0.
    for vec in args:
        xsum += vec[0]
        ysum += vec[1]
        zsum += vec[2]
    return xsum, ysum, zsum


def vdiff(v1, v2):
    '''Return the vector difference of `v1` and `v2` (`v1-v2`).'''
    x1, y1, z1 = v1
    x2, y2, z2 = v2
    return (x1-x2, y1-y2, z1-z2)


def renorm(vec, norm=1.):
    '''Return a new vector parallel to `vec` whose norm is equal to `norm`.'''
    return rescale(norm/mag(vec), vec)


def mag2(vec):
    '''Return the square of the magnitude of `vec`.'''
    return scal(vec, vec)


def mag(vec):
    '''Return the magnitude of `vec`.'''
    return sqrt(mag2(vec))


def rotate(vec, axis, angle):
    r'''Rotate vector `vec` around the axis `axis` by angle `angle`, according
    to the right-hand rule.

    This function uses Rodrigues' rotation formula. If we denote `vec` as `v`,
    the angle as `θ` and the axis as `k`, the formula reads:

    .. math::

        v' = v \cos(\theta) + (k ^ v) \sin(\theta)
             + k (k\cdot v) (1 - \cos(\theta))

    Examples:

        >>> from math import pi
        >>> vec = (1, 1, 0)
        >>> axis = (0, 0, 1)
        >>> rot_vec = rotate(vec, axis, 0.5*pi)
        >>> print('({:.5f}, {:.5f}, {:.5f})'.format(*rot_vec))
        (-1.00000, 1.00000, 0.00000)
        >>> rot_vec = rotate(vec, axis, 0.25*pi)
        >>> print('({:.5f}, {:.5f}, {:.5f})'.format(*rot_vec))
        (0.00000, 1.41421, 0.00000)

    :param vec: the vector to rotate
    :param axis: the rotation axis (must be a unit vector)
    :param angle: the rotation angle, in radians
    '''
    cangle = cos(angle)
    sangle = sin(angle)
    term1 = rescale(cangle, vec)
    term2 = rescale(sangle, vect(axis, vec))
    term3 = rescale((1 - cangle)*scal(axis, vec), axis)
    return vsum(term1, term2, term3)


def planeParamsFromPoints(pt1, pt2, pt3):
    '''Compute the parameters `(a ,b, c, d)` of the plane passing through the
    three given points `pt1`, `pt2`, `pt3`.

    The equation of the plane is written in the MCNP form as

    .. math::

        a x + b y + c z - d = 0

    Furthermore, the normal to the plane is oriented in such as way that the
    origin has negative sense (this is the MCNP convention).
    '''
    d12 = vdiff(pt1, pt2)
    d13 = vdiff(pt1, pt3)
    normal = vect(d12, d13)
    normal_len2 = mag2(normal)
    if normal_len2 <= 1e-10:
        raise ValueError('Cannot convert plane from three points because the '
                         'points are collinear or almost so: {}, {}, {}'
                         .format(pt1, pt2, pt3))
    unit_normal = renorm(normal)
    pos = scal(unit_normal, pt1)
    if pos > 0.:  # make sure the origin lies on the negative side of the plane
        return [unit_normal[0], unit_normal[1], unit_normal[2], pos]
    return [-unit_normal[0], -unit_normal[1], -unit_normal[2], -pos]


def planeParamsFromNormalAndPoint(normal, point):
    '''Return the MCNP-style parameters of the plane having the given normal
    and passing through the given points.'''
    intercept = scal(normal, point)
    return [normal[0], normal[1], normal[2], intercept]
