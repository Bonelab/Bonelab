from __future__ import annotations

from typing import Tuple, Callable, Optional
import numpy as np
from tqdm import tqdm
from scipy.optimize import least_squares

from bonelab.util.cortical_thickness.BaseTreeceMinimization import BaseTreeceMinimization
from bonelab.util.cortical_thickness.TreeceModel import TreeceModel


class LocalTreeceMinimization(BaseTreeceMinimization):

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._idx = None


    @property
    def idx(self) -> Optional[int]:
        return self._idx


    def _compute_residuals(self, args: Tuple[float, float, float, float, float]) -> np.ndarray:
        '''
        Compute the residuals between the model and the measured intensities.

        Parameters
        ----------
        args : Tuple[float, float, float, float, float]
            The parameters to fit the model: x0, x1, y0, y2, sigma.

        Returns
        -------
        np.ndarray
            The residuals between the modelled and the sampled intensities.
        '''
        modelled_intensities = self.treece_model.compute_intensities(self.x_j, *args)
        return self.gamma_j * (modelled_intensities - self.f_ij[self.idx, :])


    def fit(self) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        '''
        Fit the Treece model to the measured intensities and return the fitted parameters.
        The model is fit to each intensity profile in the f_ij array individually.

        Returns
        -------
        Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]
            The fitted parameters: m, t, rho_s, rho_b, sigma.
        '''

        lower_bounds = [
            self.x_j.min(), self.t_bounds[0],
            self.rho_s_bounds[0], self.rho_b_bounds[0], self.sigma_bounds[0]
        ]

        upper_bounds = [
            self.x_j.max(), self.t_bounds[1],
            self.rho_s_bounds[1], self.rho_b_bounds[1], self.sigma_bounds[1]
        ]

        initial_guess = [
            0, # we always guess '0' for the m parameter
            self.t_initial_guess,
            self.rho_s_initial_guess,
            self.rho_b_initial_guess,
            self.sigma_initial_guess
        ]

        m = np.zeros((self.f_ij.shape[0],))
        t = np.zeros((self.f_ij.shape[0],))
        rho_s = np.zeros((self.f_ij.shape[0],))
        rho_b = np.zeros((self.f_ij.shape[0],))
        sigma = np.zeros((self.f_ij.shape[0],))

        for i in tqdm(range(self.f_ij.shape[0]), disable=self.silent):
            self._idx = i

            result = least_squares(
                fun=self._compute_residuals,
                x0=initial_guess,
                bounds=(lower_bounds, upper_bounds),
                method="trf"
            )

            m[i], t[i], rho_s[i], rho_b[i], sigma[i] = result.x

        return m, t, rho_s, rho_b, sigma
