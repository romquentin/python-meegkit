import numpy as np

from meegkit import dss, sns, tspca
from meegkit.utils import demean, fold, unfold

import matplotlib.pyplot as plt


def test_tspca_sns_dss():  # TODO
    """Test TSPCA, SNS, DSS.

    Requires data stored in a time X channels X trials matrix.

    Remove environmental noise with TSPCA (shifts=-50:50).
    Remove sensor noise with SNS.
    Remove non-repeatable components with DSS.
    """
    # Random data (time*chans*trials)
    data = np.random.random((800, 102, 200))
    ref = np.random.random((800, 3, 200))

    # remove means
    noisy_data = demean(data)
    noisy_ref = demean(ref)

    # Apply TSPCA
    # -------------------------------------------------------------------------
    # shifts = np.arange(-50, 51)
    # print('TSPCA...')
    # y_tspca, idx = tspca.tsr(noisy_data, noisy_ref, shifts)[0:2]
    # print('\b OK!')
    y_tspca = noisy_data

    # Apply SNS
    # -------------------------------------------------------------------------
    nneighbors = 10
    print('SNS...')
    y_tspca_sns, r = sns.sns(y_tspca, nneighbors)
    print('\b OK!')

    # apply DSS
    # -------------------------------------------------------------------------
    print('DSS...')
    # Keep all PC components
    y_tspca_sns = demean(y_tspca_sns)
    print(y_tspca_sns.shape)
    todss, fromdss, _, _ = dss.dss1(y_tspca_sns)
    print('\b OK!')

    # c3 = DSS components
    y_tspca_sns_dss = fold(
        np.dot(unfold(y_tspca_sns), todss), y_tspca_sns.shape[0])

    return y_tspca, y_tspca_sns, y_tspca_sns_dss


def test_tsr(show=True):
    """Test time-shift regression."""
    sr = 200
    nsamples = 10000
    nchans = 10
    x = np.random.randn(nsamples, nchans)

    # artifact + harmonics
    artifact = np.sin(np.arange(nsamples) / sr * 2 * np.pi * 10)[:, None]
    artifact[artifact < 0] = 0
    artifact = 5 * artifact ** 3
    signal = x + artifact

    signal -= np.mean(signal, keepdims=True)
    artifact -= np.mean(artifact, keepdims=True)

    # Without shifts
    y, idx, mean_total, weights = tspca.tsr(
        signal,
        artifact,
        shifts=[0])

    if show:
        f, ax = plt.subplots(2, 1, num='without shifts')
        ax[0].plot(y[:500, 0], 'grey', label='recovered signal')
        ax[0].plot(x[:500, 0], ':', label='real signal')
        ax[1].plot((y - x)[:500], label='residual')
        ax[0].legend()
        ax[1].legend()
        # plt.show()

    # Test residual almost 0.0
    np.testing.assert_almost_equal(y - x, np.zeros_like(y), decimal=1)

    # With shifts. We slide the input array by one sample, and check that the
    # artifact is successfully regressed.
    y, idx, mean_total, weights = tspca.tsr(
        signal,
        np.roll(artifact, 1, axis=0),
        shifts=[-1, 0, 1])

    if show:
        f, ax = plt.subplots(3, 1, num='with shifts')
        ax[0].plot(signal[:500], label='signal + noise')
        ax[1].plot(x[:500, 0], 'grey', label='real signal')
        ax[1].plot(y[:500, 0], ':', label='recovered signal')
        ax[2].plot((signal - y)[:500, 0], label='before - after')
        ax[0].legend()
        ax[1].legend()
        ax[2].legend()
        plt.show()

if __name__ == '__main__':
    # import pytest
    # pytest.main([__file__])
    test_tsr()
