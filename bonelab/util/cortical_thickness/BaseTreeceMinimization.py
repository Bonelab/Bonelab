from __future__ import annotations

from abc import ABCMeta, abstractmethod
import numpy as np
from typing import Tuple, Optional

from bonelab.util.cortical_thickness.TreeceModel import TreeceModel


class BaseTreeceMinimization(metaclass=ABCMeta):
    def __init__(
        self,
        rho_c: Optional[float],
        f_ij: np.ndarray,
        x_j: np.ndarray,
        residual_boost_factor: float,
        t_initial_guess: Optional[float],
        rho_s_initial_guess: float,
        rho_b_initial_guess: float,
        sigma_initial_guess: float,
        t_bounds: Optional[Tuple[float, float]],
        rho_s_bounds: Tuple[float, float],
        rho_b_bounds: Tuple[float, float],
        sigma_bounds: Tuple[float, float],
        silent: bool
    ) -> None:
        '''
        Parameters
        ----------
        rho_c : float
            The density of the cortical bone.

        f_ij : np.ndarray
            The intensity profiles to fit.

        x_j : np.ndarray
            The x values of the intensity profiles.

        residual_boost_factor : float
            The factor to boost the residuals by where x_j=0

        t_initial_guess : Optional[float]
            The initial guess for the parameter t.

        rho_s_initial_guess : float
            The initial guess for the parameter rho_s.

        rho_b_initial_guess : float
            The initial guess for the parameter rho_b.

        sigma_initial_guess : float
            The initial guess for the parameter sigma.

        t_bounds : Optional[Tuple[float, float]]
            The bounds for the parameter t.

        rho_s_bounds : Tuple[float, float]
            The bounds for the parameter rho_s.

        rho_b_bounds : Tuple[float, float]
            The bounds for the parameter rho_b.

        sigma_bounds : Tuple[float, float]
            The bounds for the parameter sigma.

        silent : bool
            Whether to suppress output.
        '''
        self._f_ij = f_ij
        self._x_j = x_j
        self._rho_c = (
            rho_c
            if rho_c is not None
            else f_ij.max(axis=0)
        )
        self._create_treece_model()
        self._residual_boost_factor = residual_boost_factor
        self._compute_residual_multiplier()
        self._t_bounds = (
            t_bounds
            if t_bounds is not None
            else (x_j[1] - x_j[0], x_j.max() - x_j.min())
        )
        self._t_initial_guess = (
            t_initial_guess
            if t_initial_guess is not None
            else (self.t_bounds[0] + self.t_bounds[1]) / 2
        )
        self._rho_s_initial_guess = rho_s_initial_guess
        self._rho_b_initial_guess = rho_b_initial_guess
        self._sigma_initial_guess = sigma_initial_guess
        self._rho_s_bounds = rho_s_bounds
        self._rho_b_bounds = rho_b_bounds
        self._sigma_bounds = sigma_bounds
        self._silent = silent


    @property
    def rho_c(self) -> float:
        return self._rho_c


    @property
    def treece_model(self) -> TreeceModel:
        return self._treece_model


    @property
    def f_ij(self) -> np.ndarray:
        return self._f_ij


    @property
    def x_j(self) -> np.ndarray:
        return self._x_j


    @property
    def residual_boost_factor(self) -> float:
        return self._residual_boost_factor


    @property
    def gamma_j(self) -> np.ndarray:
        return self._gamma_j


    @property
    def t_bounds(self) -> Tuple[float, float]:
        return self._t_bounds


    @property
    def t_initial_guess(self) -> float:
        return self._t_initial_guess


    @property
    def rho_s_initial_guess(self) -> float:
        return self._rho_s_initial_guess


    @property
    def rho_b_initial_guess(self) -> float:
        return self._rho_b_initial_guess


    @property
    def sigma_initial_guess(self) -> float:
        return self._sigma_initial_guess


    @property
    def rho_s_bounds(self) -> Tuple[float, float]:
        return self._rho_s_bounds


    @property
    def rho_b_bounds(self) -> Tuple[float, float]:
        return self._rho_b_bounds


    @property
    def sigma_bounds(self) -> Tuple[float, float]:
        return self._sigma_bounds


    @property
    def silent(self) -> bool:
        return self._silent


    def _create_treece_model(self) -> None:
        '''
        Create the Treece model using the current cortical density.
        '''
        self._treece_model = TreeceModel(self._rho_c)


    def _compute_residual_multiplier(self) -> None:
        '''
        Update the residual multiplier using the current
        sampling locations and residual boost factor.
        '''
        self._gamma_j = (
            self.residual_boost_factor
            + (
                (1 - self.residual_boost_factor)
                / np.abs(self.x_j).max()
            ) * np.abs(self.x_j)
        )


    @abstractmethod
    def fit(self) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        pass
