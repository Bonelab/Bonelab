from __future__ import annotations

from abc import ABCMeta, abstractmethod
import numpy as np
from typing import Tuple, Optional
from scipy.sparse import csr_matrix
from scipy.optimize import minimize

from bonelab.util.time_stamp import message
from bonelab.util.cortical_thickness.TreeceModel import TreeceModel


class BaseTreeceMinimization(metaclass=ABCMeta):
    '''
    Abstract base class for Treece minimization.
    '''

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
        x_bounds: Tuple[float, float],
        t_bounds: Optional[Tuple[float, float]],
        rho_s_bounds: Tuple[float, float],
        rho_b_bounds: Tuple[float, float],
        sigma_bounds: Tuple[float, float],
        silent: bool,
        max_iterations: int,
        f_tol: float,
        g_tol: float,
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

        x_bounds : Tuple[float, float]
            The bounds for the parameter x.

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

        max_iterations : int
            The maximum number of iterations to perform.

        f_tol : float
            The tolerance for convergence of the function value.

        g_tol : float
            The tolerance for convergence of the gradient.
        '''
        self._f_ij = f_ij
        self._x_j = x_j
        self._rho_c = (
            rho_c
            if rho_c is not None
            else f_ij.max(axis=1).reshape(f_ij.shape[0], 1)
        )
        self._create_treece_model()
        self._residual_boost_factor = residual_boost_factor
        self._compute_residual_multiplier()
        self._x_bounds = x_bounds
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
        self._max_iterations = max_iterations
        self._f_tol = f_tol
        self._g_tol = g_tol
        self._construct_minimize_options()


    @property
    def rho_c(self) -> float:
        '''
        The density of the cortical bone.

        Returns
        -------
        float
        '''
        return self._rho_c


    @property
    def treece_model(self) -> TreeceModel:
        '''
        The Treece model.

        Returns
        -------
        TreeceModel
        '''
        return self._treece_model


    @property
    def f_ij(self) -> np.ndarray:
        '''
        The intensity profiles to fit.

        Returns
        -------
        np.ndarray
        '''
        return self._f_ij


    @property
    def x_j(self) -> np.ndarray:
        '''
        The x values of the intensity profiles.

        Returns
        -------
        np.ndarray
        '''
        return self._x_j


    @property
    def residual_boost_factor(self) -> float:
        '''
        The factor to boost the residuals by where x_j=0.

        Returns
        -------
        float
        '''
        return self._residual_boost_factor


    @property
    def gamma_j(self) -> np.ndarray:
        '''
        The boost factor at each x_j.

        Returns
        -------
        np.ndarray
        '''
        return self._gamma_j


    @property
    def x_bounds(self) -> Tuple[float, float]:
        '''
        The bounds for the parameter x.

        Returns
        -------
        Tuple[float, float]
        '''
        return self._x_bounds


    @property
    def t_bounds(self) -> Tuple[float, float]:
        '''
        The bounds for the parameter t.

        Returns
        -------
        Tuple[float, float]
        '''
        return self._t_bounds


    @property
    def t_initial_guess(self) -> float:
        '''
        The initial guess for the parameter t.

        Returns
        -------
        float
        '''
        return self._t_initial_guess


    @property
    def rho_s_initial_guess(self) -> float:
        '''
        The initial guess for the parameter rho_s.

        Returns
        -------
        float
        '''
        return self._rho_s_initial_guess


    @property
    def rho_b_initial_guess(self) -> float:
        '''
        The initial guess for the parameter rho_b.

        Returns
        -------
        float
        '''
        return self._rho_b_initial_guess


    @property
    def sigma_initial_guess(self) -> float:
        '''
        The initial guess for the parameter sigma.

        Returns
        -------
        float
        '''
        return self._sigma_initial_guess


    @property
    def rho_s_bounds(self) -> Tuple[float, float]:
        '''
        The bounds for the parameter rho_s.

        Returns
        -------
        Tuple[float, float]
        '''
        return self._rho_s_bounds


    @property
    def rho_b_bounds(self) -> Tuple[float, float]:
        '''
        The bounds for the parameter rho_b.

        Returns
        -------
        Tuple[float, float]
        '''
        return self._rho_b_bounds


    @property
    def sigma_bounds(self) -> Tuple[float, float]:
        '''
        The bounds for the parameter sigma.

        Returns
        -------
        Tuple[float, float]
        '''
        return self._sigma_bounds


    @property
    def silent(self) -> bool:
        '''
        Whether to suppress output.

        Returns
        -------
        bool
        '''
        return self._silent


    @property
    def max_iterations(self) -> int:
        '''
        The maximum number of iterations for the optimization.

        Returns
        -------
        int
        '''
        return self._max_iterations


    @property
    def f_tol(self) -> float:
        '''
        The tolerance for the function value.

        Returns
        -------
        float
        '''
        return self._f_tol


    @property
    def g_tol(self) -> float:
        '''
        The tolerance for the gradient.

        Returns
        -------
        float
        '''
        return self._g_tol


    @property
    def minimize_options(self) -> Dict[str, Any]:
        '''
        The options for the optimization.

        Returns
        -------
        Dict[str, Any]
        '''
        return self._minimize_options


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


    def _construct_minimize_options(self) -> None:
        '''
        Construct the options for the optimization.
        '''
        self._minimize_options = {
            'maxiter': self._max_iterations,
            'disp': not self._silent,
            'ftol': self._f_tol,
            'gtol': self._g_tol
        }


    def _compute_loss_and_jacobian_initial(
        self, control_params: np.ndarray
    ) -> Tuple[float, np.ndarray]:
        '''
        Compute the loss and Jacobian of the loss with respect to
        the control parameters for the initial optimization step,
        where there is only one set of model parameters applied
        simultaneously to all points.

        Parameters
        ----------
        control_params : (5, 1) np.ndarray
            The control parameters: [m, t, s, b, sigma]

        Returns
        -------
        Tuple[float, (5,) np.ndarray]
            The loss and Jacobian of the loss with respect to the
            control parameters.
        '''
        m = control_params[0].reshape(1,1)
        t = control_params[1].reshape(1,1)
        rho_s = control_params[2].reshape(1,1)
        rho_b = control_params[3].reshape(1,1)
        sigma = control_params[4].reshape(1,1)
        fhat_ij, dfhat_ij_gradient = self.treece_model.compute_intensities_and_derivatives(
            self.x_j, m, t, rho_s, rho_b, sigma
        )
        r_ij = fhat_ij - self.f_ij
        loss = 0.5 * (self.gamma_j * np.power(r_ij, 2)).mean()
        jacobian = np.array([
            (self.gamma_j * r_ij * dfhat_ij_dp).mean()
            for dfhat_ij_dp in dfhat_ij_gradient
        ])
        return loss, jacobian


    def _initial_fit(self) -> Tuple[np.ndarray, np.ndarray, float, float, float]:
        '''
        Perform an initial fit to the data to determine the
        best initial guess for the next phase.

        Returns
        -------
        Tuple[np.ndarray, np.ndarray, float, float, float]
            The fitted parameters: m, t, rho_s, rho_b, sigma.
        '''
        bounds = list(zip(
            [
                self.x_bounds[0], self.t_bounds[0],
                self.rho_s_bounds[0], self.rho_b_bounds[0], self.sigma_bounds[0]
            ],
            [
                self.x_bounds[1], self.t_bounds[1],
                self.rho_s_bounds[1], self.rho_b_bounds[1], self.sigma_bounds[1]
            ]
        ))

        initial_guess = [
            0, # we always guess '0' for the m parameter
            self.t_initial_guess,
            self.rho_s_initial_guess,
            self.rho_b_initial_guess,
            self.sigma_initial_guess
        ]

        minimize_options = {
            "disp": (0 if self.silent else 2),
            "maxiter": self.max_iterations,
            "ftol": self.f_tol,
            "gtol": self.g_tol
        }

        if ~self.silent:
            message("Initial global model fit:")

        result = minimize(
            self._compute_loss_and_jacobian_initial,
            x0=initial_guess,
            bounds=bounds,
            method="L-BFGS-B",
            options=minimize_options,
            jac=True
        )

        m = result.x[0] * np.ones((self.f_ij.shape[0],))
        t = result.x[1] * np.ones((self.f_ij.shape[0],))
        rho_s = result.x[-3]
        rho_b = result.x[-2]
        sigma = result.x[-1]

        return m, t, rho_s, rho_b, sigma


    @abstractmethod
    def fit(self) -> Tuple[np.ndarray, np.ndarray, float, float, float]:
        '''
        Fit the Treece model to the intensity profiles.

        Returns
        -------
        Tuple[np.ndarray, np.ndarray, float, float, float]
            The fitted parameters: m, t, rho_s, rho_b, sigma.
        '''
        pass
