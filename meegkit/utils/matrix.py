"""Matrix operation utility functions."""
import numpy as np


def relshift(X, ref, shifts, fill_value=0, axis=0):
    """Create shifted versions of X relative to ref with padding.

    `ref` is replicated to have the same shape as `y` and padded accordingly.

    Parameters
    ----------
    X : array, shape = (n_samples[, n_epochs][, n_trials])
        Array to shift.
    ref : array, shape = (n_samples[, n_epochs][, n_trials])
        Reference array against which `X` is shifted.
    shifts : array | int
        Array of shifts.
    fill_value : float
        Value to pad output axis by.
    axis : int
        The axis along which elements are shifted.

    Returns
    -------
    y : array, shape = (n_samples[, n_epochs][, n_trials], n_shifts)
        Shifted array.
    y_ref : array, shape = (n_samples[, n_epochs][, n_trials], n_shifts)
        Reference array, repeated to match `y.shape`. Padding matches that of
        `y`.

    See Also
    --------
    multishift, shift, shiftnd

    """
    shifts, n_shifts = _check_shifts(shifts)
    X = _check_data(X)
    ref = _check_data(ref)

    if X.shape[0] != ref.shape[0]:
        raise AttributeError('X and ref must have same n_times')

    # First we delay X
    y = multishift(X, shifts=shifts, axis=axis, fill_value=fill_value)

    # Then we create as many copies of ref as there are lags
    y_ref = multishift(ref, shifts=np.zeros(n_shifts), axis=axis)

    # We need to find out the indices of the padded values in `y`. For this we
    # use a hack where we feed in an array of ones to multishift(), with a
    # known `fill_value`.
    temp = multishift(np.ones_like(X), shifts=shifts, axis=axis, fill_value=0)
    mask = temp == 0
    y_ref[mask] = fill_value

    return y, y_ref


def multishift(X, shifts, fill_value=0, axis=0, keep_dims=False):
    """Apply several shifts along specified axis.

    If `shifts` has multiple values, the output will contain one shift per
    page. Shifted data are padded with `fill_value`.

    Parameters
    ----------
    X : array, shape = (n_samples[, n_epochs][, n_trials])
        Array to shift.
    shifts : array
        Array of shifts.
    fill_value : float | np.nan
        Value to pad output axis by.
    axis : int, optional
        The axis along which elements are shifted.
    keep_dims : bool
        If True, keep singleton dimensions in output.

    Returns
    -------
    y : array, shape = (n_samples[, n_epochs][, n_trials], n_shifts)
        Shifted array.

    See Also
    --------
    relshift, shift, shiftnd

    """
    shifts, n_shifts = _check_shifts(shifts)
    X = _check_data(X)

    # Loop over shifts
    y = np.zeros(X.shape + (n_shifts,))
    for i, s in enumerate(shifts):
            y[..., i] = shift(X, shift=s, fill_value=fill_value, axis=axis)

    if n_shifts == 1 and not keep_dims:
        y = np.squeeze(y, axis=-1)

    return y


def shift(X, shift, fill_value=0, axis=0):
    """Shift array along its first, second or last dimension.

    Output is padded by `fill_value`.

    Parameters
    ----------
    X : array, shape = (n_samples[, n_epochs][, n_trials])
        Multidimensional input array.
    shift : int
        The number of places by which elements are shifted along axis.
    fill_value : float
        Value to pad output axis by.
    axis : int, optional
        The axis along which elements are shifted.

    Returns
    -------
    y : array
        Output array, with the same shape as `X`.

    See Also
    --------
    relshift, multishift, shiftnd

    """
    if not np.equal(np.mod(shift, 1), 0):
        raise AttributeError('shift must be a single int')

    # reallocate empty array and assign slice.
    y = np.empty_like(X)

    if shift == 0:
        y[:] = X
    else:
        if axis == 0:
            if shift > 0:
                y[:shift, ...] = fill_value
                y[shift:, ...] = X[:-shift]
            elif shift < 0:
                y[shift:,  ...] = fill_value
                y[:shift,  ...] = X[-shift:]

        elif axis == 1:
            if shift > 0:
                y[:, :shift, ...] = fill_value
                y[:, shift:, ...] = X[:, :-shift]
            elif shift < 0:
                y[:, shift:,  ...] = fill_value
                y[:, :shift,  ...] = X[:, -shift:]

        elif axis == -1:
            if shift > 0:
                y[..., :shift] = fill_value
                y[..., shift:] = X[..., :-shift]
            elif shift < 0:
                y[..., shift:] = fill_value
                y[..., :shift] = X[..., -shift:]

        else:
            raise NotImplementedError('Axis must be 0, 1 or -1.')

    return y


def shiftnd(X, shift, fill_value=0, axis=None):
    """Roll array elements along a given axis with padding.

    Elements off the end of the array are treated as zeros. This function is
    slower than function:`shift`, so prefer the latter when possible.

    Parameters
    ----------
    X : array
        Multidimensional input array.
    shift : int
        The number of places by which elements are shifted along axis.
    fill_value : float
        Value to pad output axis by.
    axis : int, optional
        The axis along which elements are shifted. By default, the array is
        flattened before shifting, after which the original shape is restored.

    Returns
    -------
    y : array, (n_samples, [n_epochs, ][n_trials, ])
        Output array, with the same shape as `X`.

    See Also
    --------
    np.roll     : Elements that roll off one end come back on the other.
    np.rollaxis : Roll the specified axis backwards, until it lies in a given
                  position.

    Examples
    --------
    >>> x = np.arange(10)
    >>> shiftnd(x, 2)
    array([0, 0, 0, 1, 2, 3, 4, 5, 6, 7])
    >>> x2 = np.reshape(x, (2,5))
    >>> x2
    array([[0, 1, 2, 3, 4],
           [5, 6, 7, 8, 9]])
    >>> shiftnd(x2, 1)
    array([[0, 0, 1, 2, 3],
           [4, 5, 6, 7, 8]])
    >>> shiftnd(x2, -2)
    array([[2, 3, 4, 5, 6],
           [7, 8, 9, 0, 0]])
    >>> shiftnd(x2, 1, axis=0)
    array([[0, 0, 0, 0, 0],
           [0, 1, 2, 3, 4]])
    >>> shiftnd(x2, -1, axis=0)
    array([[5, 6, 7, 8, 9],
           [0, 0, 0, 0, 0]])
    >>> shiftnd(x2, 1, axis=1)
    array([[0, 0, 1, 2, 3],
           [0, 5, 6, 7, 8]])

    """
    X = np.asanyarray(X)
    if shift == 0:
        return X

    if axis is None:
        n = X.size
        reshape = True
    else:
        n = X.shape[axis]
        reshape = False

    if np.abs(shift) > n:
        y = np.ones_like(X) * fill_value
    elif shift < 0:
        shift += n
        pad = np.ones_like(X.take(np.arange(n - shift), axis)) * fill_value
        y = np.concatenate((X.take(np.arange(n - shift, n), axis), pad), axis)
    else:
        pad = np.ones_like(X.take(np.arange(n - shift, n), axis)) * fill_value
        y = np.concatenate((pad, X.take(np.arange(n - shift), axis)), axis)

    if reshape:
        return y.reshape(X.shape)
    else:
        return y


def theshapeof(X):
    """Return the shape of X."""
    if not isinstance(X, np.ndarray):
        raise AttributeError('X must be a numpy array')

    if X.ndim == 3:
        return X.shape[0], X.shape[1], X.shape[2]
    elif X.ndim == 2:
        return X.shape[0], X.shape[1], 1
    elif X.ndim == 1:
        return X.shape[0], 1, 1
    else:
        raise ValueError("Array contains more than 3 dimensions")


def unsqueeze(X):
    """Append singleton dimensions to an array."""
    X = _check_data(X)
    if X.shape != theshapeof(X):
        return X.reshape(theshapeof(X))
    else:
        return X


def fold(X, epochsize):
    """Fold 2D X into 3D."""
    if X.ndim != 2:
        raise AttributeError('X must be 2D')

    n_chans = X.shape[0] // epochsize
    X = np.transpose(
        np.reshape(X, (epochsize, n_chans, X.shape[1]),
                   order="F").copy(), [0, 2, 1])
    return X


def unfold(X):
    """Unfold 3D X."""
    n_samples, n_chans, n_trials = theshapeof(X)

    if n_trials > 1:
        return np.reshape(
            np.transpose(X, (0, 2, 1)),
            (n_samples * n_trials, n_chans), order="F").copy()
    else:
        return X


def demean(X, weights=None):
    """Remove weighted mean over columns (samples)."""
    if weights is None:
        weights = np.array([])

    n_samples, n_chans, n_trials = theshapeof(X)
    X = unfold(X)

    if weights.any():
        weights = unfold(weights)

        if weights.shape[0] != X.shape[0]:
            raise ValueError('X and weights arrays should have same ' +
                             'number of rows and pages.')

        if weights.shape[1] == 1 or weights.shape[1] == n_chans:
            the_mean = np.sum(X * weights) // np.sum(weights)
        else:
            raise ValueError('Weight array should have either the same ' +
                             'number of columns as X array, or 1 column.')

        demeaned_X = X - the_mean
    else:
        the_mean = np.mean(X, 0)
        demeaned_X = X - the_mean

    demeaned_X = fold(demeaned_X, n_samples)

    # the_mean.shape = (1, the_mean.shape[0])
    return demeaned_X, the_mean


def normcol(X, weights=None):
    """Normalize each column so that its weighted mean square value is 1.

    If X is 3D, pages are concatenated vertically before calculating the
    norm.

    Weight should be either a column vector, or a matrix (2D or 3D) of same
    size as X.

    Parameters
    ----------
    X: X to normalize
    weights: weight

    Returns
    -------
    X_norm: normalized X

    """
    if X.ndim == 3:
        n_samples, n_chans, n_trials = X.shape
        X = unfold(X)
        if not weights.any():
            # no weights
            X_norm = fold(normcol(X), n_samples)
        else:
            if weights.shape[0] != n_samples:
                raise ValueError("Weight array should have same number of' \
                                 'columns as X")

            if weights.ndim == 2 and weights.shape[1] == 1:
                weights = np.tile(weights, (1, n_samples, n_trials))

            if weights.shape != weights.shape:
                raise ValueError("Weight array should have be same shape as X")

            weights = unfold(weights)

            X_norm = fold(normcol(X, weights), n_samples)
    else:
        n_samples, n_chans, n_trials = theshapeof(X)
        if not weights.any():
            X_norm = X * ((np.sum(X ** 2) / n_samples) ** -0.5)
        else:
            if weights.shape[0] != X.shape[0]:
                raise ValueError('Weight array should have same number of ' +
                                 'columns as X')

            if weights.ndim == 2 and weights.shape[1] == 1:
                weights = np.tile(weights, (1, n_chans))

            if weights.shape != X.shape:
                raise ValueError('Weight array should have be same shape as X')

            if weights.shape[1] == 1:
                weights = np.tile(weights, (1, n_chans))

            X_norm = X * \
                (np.sum((X ** 2) * weights) / np.sum(weights)) ** -0.5

    return X_norm


def _check_shifts(shifts):
    """Check shifts."""
    if not isinstance(shifts, (np.ndarray, list, np.integer, type(None))):
        raise AttributeError('shifts should be a list, an array or an int')
    if isinstance(shifts, (list, np.integer)):
        shifts = np.array(shifts).flatten()
    if shifts is None or len(shifts) == 0:
        shifts = np.array([0])
    n_shifts = np.size(shifts)
    return shifts, n_shifts


def _check_data(X):
    """Check data is numpy array and has the proper dimensions."""
    if not isinstance(X, (np.ndarray, list)):
        raise AttributeError('data should be a list or a numpy array')

    dtype = np.complex128 if np.any(np.iscomplex(X)) else np.float64
    X = np.asanyarray(X, dtype=dtype)
    if X.ndim > 3:
        raise ValueError('Data must be 3D at most')

    return X