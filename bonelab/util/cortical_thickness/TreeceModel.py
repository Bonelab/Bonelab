from __future__ import annotations

from typing import Union, Tuple
import numpy as np
from scipy.special import erf


class TreeceModel:
    '''
    Class to compute the intensities and their derivatives along a
    parameterized line normal to the cortical surface based on a
    function with two step functions and some blurring.
    '''

    def __init__(self, rho_c: Union[float, np.ndarray]) -> None:
        '''
        Initiailization function

        Parameters
        ----------
        rho_c : Union[float, np.ndarray]
            The intensity of the cortical bone. Can be specified
            globally, or at each point.
        '''
        self._rho_c = rho_c
        self._sqrt2 = np.sqrt(2)
        self._sqrt2pi = np.sqrt(2 * np.pi)


    @property
    def rho_c(self) -> Union[float, np.ndarray]:
        '''
        Get the intensity of the cortical bone.

        Returns
        -------
        Union[float, np.ndarray]
            The intensity of the cortical bone.
        '''
        return self._rho_c


    @property
    def sqrt2(self) -> float:
        '''
        Get the square root of 2.

        Returns
        -------
        float
            The square root of 2.
        '''
        return self._sqrt2


    @property
    def sqrt2pi(self) -> float:
        '''
        Get the square root of 2 times pi.

        Returns
        -------
        float
            The square root of 2 times pi.
        '''
        return self._sqrt2pi


    def compute_intensities(
        self,
        x: np.ndarray,
        m: float,
        t: float,
        rho_s: float,
        rho_b: float,
        sigma: float
    ) -> np.ndarray:
        '''
        Compute the intensities at a given location on a parameterized
        line normal to the cortical surface based on a function with two
        step functions and some blurring. Also compute the Jacobian of
        the intensities along the line with respect to the free
        parameters in the model.

        Parameters
        ----------
        x : np.ndarray
            The locations along the parameterized line where the intensities are measured.

        m : float
            The middle of the cortical bone.

        t : float
            The thickness of the cortical bone.

        rho_s : float
            The intensity of the tissue outside the cortical bone.

        rho_b : float
            The intensity of the tissue past the cortical bone.

        sigma : float
            The standard deviation of the Gaussian blur approximating

        Returns
        -------
        np.ndarray
            The predicted intensities at the locations x.
        '''
        cort_start = x - m + t/2
        cort_end = x - m - t/2

        term1 = ((self._rho_c - rho_s) / 2) * (1 + erf(cort_start / (sigma * self._sqrt2)))
        term2 = ((rho_b - self._rho_c) / 2) * (1 + erf(cort_end / (sigma * self._sqrt2)))
        return rho_s + term1 + term2


    def compute_intensities_and_derivatives(
        self,
        x: np.ndarray,
        m: float,
        t: float,
        rho_s: float,
        rho_b: float,
        sigma: float
    ) -> Tuple[np.ndarray, Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]]:
        '''
        Compute the intensities at a given location on a parameterized
        line normal to the cortical surface based on a function with two
        step functions and some blurring. Also compute the Jacobian of
        the intensities along the line with respect to the free
        parameters in the model.

        Parameters
        ----------
        x : np.ndarray
            The locations along the parameterized line where the intensities are measured.

        m : float
            The middle of the cortical bone.

        t : float
            The thickness of the cortical bone.

        rho_s : float
            The intensity of the tissue outside the cortical bone.

        rho_b : float
            The intensity of the tissue past the cortical bone.

        sigma : float
            The standard deviation of the Gaussian blur approximating

        Returns
        -------
        Tuple[np.ndarray, Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]]
            The predicted intensities at the locations x, and the Jacobian of the intensities
            with respect to the parameters m, t, s, b, and sigma.
        '''
        cort_start = x - m + t/2
        cort_end = x - m - t/2

        term1 = ((self._rho_c - rho_s) / 2) * (1 + erf(cort_start / (sigma * self._sqrt2)))
        term2 = ((rho_b - self._rho_c) / 2) * (1 + erf(cort_end / (sigma * self._sqrt2)))
        f = rho_s + term1 + term2

        df_drhos = 0.5 * ( 1 - erf(cort_start / (sigma * self._sqrt2)) )
        df_drhob = 0.5 * ( 1 + erf(cort_end / (sigma * self._sqrt2)) )

        df_dm = (
            -(self._rho_c - rho_s) / (sigma * self._sqrt2pi) * np.exp(-(cort_start**2) / (2 * sigma**2))
            - (rho_b - self._rho_c) / (sigma * self._sqrt2pi) * np.exp(-(cort_end**2) / (2 * sigma**2))
        )

        df_dt = (
            (self._rho_c - rho_s) / (2 * sigma * self._sqrt2pi) * np.exp(
                -(cort_start**2) / (2 * sigma**2)
            )
            - (rho_b - self._rho_c) / (2 * sigma * self._sqrt2pi) * np.exp(
                -(cort_end**2) / (2 * sigma**2)
            )
        )

        df_dsigma = (
            -(self._rho_c - rho_s) * cort_start / (sigma**2 * self._sqrt2pi) * np.exp(
                -(cort_start**2) / (2 * sigma**2)
            )
            - (rho_b - self._rho_c) * cort_end / (sigma**2 * self._sqrt2pi) * np.exp(
                -(cort_end**2) / (2 * sigma**2)
            )
        )

        return f, (df_dm, df_dt, df_drhos, df_drhob, df_dsigma)
