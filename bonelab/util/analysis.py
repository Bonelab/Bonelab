from __future__ import annotations

# This utility module has some stuff for doing precision analysis and also for
# formatting data and p values in a way that is standardized and nice-looking.
# Nothing in here is ground-breaking but it's annoying to have to figure out how to
# do it and it would be nicer if everyone in the lab did this stuff the same
# way so we know that precision is always being calculated consistently and that
# data is being reported in a standard way (avoids manual formatting)


from typing import Tuple
import numpy as np
from math import floor, log10


def calculate_precision(
        data: np.ndarray, eps: float = 1e-8, ddof: int = 1
) -> Tuple[float, float, float, np.ndarray]:
    """
    Calculate short term precision from a repeat measures dataset.

    Parameters
    ----------
    data : np.ndarray
        The data to calculate precision from. Should be a NxM array where N is
        the number of samples and M is the number of repeats.

    eps : float
        A very small number to prevent division by zero. If your data means
        are very close to zero you probably should not be using CVs though.

    ddof : int
        The delta degrees of freedom to use in the calculation of the standard
        deviations. The default is 1 but if you think it should be 0, or something
        else, that's up to you.

    Returns
    -------
    Tuple[float, float, float, np.ndarray]
        The RMS%CV, LSC, RMS%PE, and %CVs
    """
    means, standard_deviations = data.mean(axis=1), data.std(ddof=ddof, axis=1)
    rms_pe = np.sqrt((standard_deviations ** 2).mean())
    lsc = 2.77 * rms_pe
    cvs = (100 * standard_deviations / (means + eps))
    rms_cv = np.sqrt((cvs ** 2).mean())
    return rms_cv, lsc, rms_pe, cvs


def format_estimate(estimate: float, stderr: float, err_label="SEE") -> str:
    """
    Format an estimate and its standard error into a nice string. Uses the standard
    rules for reporting where you keep only 1 significant digit for the error,
    unless it leads with a 1, in which case you keep 2 significant digits, and
    then you match the number of decimal places in the estimate to the error.

    Parameters
    ----------
    estimate : float
        The estimate.

    stderr : float
        The standard error of the estimate.

    err_label : str
        The label to use for the standard error. The default is "SEE". You might want to
        swap in "SD" or something depending on what you are reporting.

    Returns
    -------
    str
        The nice-looking string.
    """
    estimate, stderr = float(estimate), float(stderr)
    leading_one = (int(str(stderr).replace("0", "").replace(".", "")[0]) == 1)
    decimal_places = -int(floor(log10(abs(stderr)))) + leading_one
    estimate = round(estimate, decimal_places)
    stderr = round(stderr, decimal_places)
    if decimal_places > 0:
        return f"{estimate:0.{decimal_places}f} ({err_label} {stderr:0.{decimal_places}f})"
    else:
        return f"{estimate:.0f} ({err_label} {stderr:.0f})"


def format_pval(pval: float, alpha: float, sigmarker: str = "*", decimal_places: int = 3) -> str:
    """
    Format a p value into a nice string. By default, if the p value is less than 0.001, it
    will be reported as "< 0.001 *". Otherwise, it will be reported as a number
    with 3 decimal places and a star if it is less than the alpha level. You can change the
    number of decimal places and the significance marker if you want.

    Parameters
    ----------
    pval : float
        The p value to format.

    alpha : float
        The alpha level to use for the significance test.

    sigmarker : str
        The marker to use for significance. The default is "*".

    decimal_places : int
        The number of decimal places to use for the p value. The default is 3.

    Returns
    -------
    str
        The nice-looking string.
    """
    if decimal_places < 1:
        raise ValueError("decimal_places must be a positive integer")
    if pval < 10**(-decimal_places):
        return f"< {10**(-decimal_places):0.{decimal_places}f} {sigmarker}"
    sig = sigmarker if (pval < alpha) else " "
    return f"{round(pval, decimal_places):0.{decimal_places}f} {sig}"

