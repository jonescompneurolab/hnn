# cartesian.py - returns cartesian product of a list of np arrays
#                from StackOverflow.com
#
# v 1.10.0-py35
# rev 2015-05-01 (SL: deprecated, tested)
# last major: (SL: imported from Stack Overflow)

import numpy as np
import itertools as it

def cartesian(arrays, out=None):
    """ Parameters
        ----------
        arrays : list of array-like
            1-D arrays to form the cartesian product of.
        out : ndarray
            Array to place the cartesian product in.

        Returns
        -------
        out : ndarray
            2-D array of shape (M, len(arrays)) containing cartesian products
            formed of input arrays.

        Examples
        --------
        >>> cartesian(([1, 2], [4, 5], [6, 7]))
        array([[1, 4, 6],
               [1, 4, 7],
               [1, 5, 6],
               [1, 5, 7],
               [2, 4, 6],
               [2, 4, 7],
               [2, 5, 6],
               [2, 5, 7])
    """
    try:
        xrange

    except:
        xrange = range

    arrays = [np.asarray(x) for x in arrays]

    n = np.prod([x.size for x in arrays])
    if out is None:
        out = np.zeros([n, len(arrays)], dtype='float64')

    m = int(n / arrays[0].size)

    out[:, 0] = np.repeat(arrays[0], m)

    if arrays[1:]:
        cartesian(arrays[1:], out=out[:m, 1:])

        for j in xrange(1, arrays[0].size):
            out[j*m:(j+1)*m,1:] = out[:m, 1:]

    return out

if __name__ == '__main__':
    arrs = [np.arange(3), np.array([0]), np.array([5, 6, 7]), np.array([0, 1])]
    out = cartesian(arrs)
    print('old way')
    print(out)

    out_it = [item for item in it.product(*arrs)]
    print('it way')
    for item in out_it:
        print(item)
