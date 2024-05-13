from __future__ import annotations

from typing import List, Optional, Tuple
import numpy as np
from scipy.sparse import csr_matrix
from scipy.optimize import minimize
from tqdm import trange

from bonelab.util.time_stamp import message
from bonelab.util.cortical_thickness.BaseTreeceMinimization import BaseTreeceMinimization
from bonelab.util.cortical_thickness.ctth_util import compute_gaussian_distance_weighting_transformation


class GlobalControlPointTreeceMinimization(BaseTreeceMinimization):
    '''
    Class to perform the global Treece minimization using a
    hierarchical multiscale control point interpolation approach.
    '''

    def __init__(
        self,
        points: np.ndarray,
        control_point_separations: List[float],
        interpolation_neighbours: int,
        max_iterations: int,
        f_tol: float,
        g_tol: float,
        *args,
        **kwargs
    ) -> None:
        '''
        Initialization function

        Parameters
        ----------
        points : (N, 3) np.ndarray
            The points on which intensities are measured. Model
            parameters will be interpolated from control points
            to the points.

        control_point_separations : List[float]
            The separations between control points.

        interpolation_neighbours : int
            The number of nearest neighbours to use.

        max_iterations : int
            The maximum number of iterations to perform.

        f_tol : float
            The tolerance for convergence of the function value.

        g_tol : float
            The tolerance for convergence of the gradient.

        *args, **kwargs
            Additional arguments to pass to the Base
        '''
        super().__init__(*args, **kwargs)
        self._points = points
        self._n = points.shape[0]
        self._m = self.x_j.shape[0]
        self._q = 0
        self._control_point_separations = control_point_separations
        self._a = None
        self._a_t = None
        self._control_points = None
        self._control_point_idxs = []
        self._interpolation_neighbours = interpolation_neighbours
        self._max_iterations = max_iterations
        self._f_tol = f_tol
        self._g_tol = g_tol


    @property
    def q(self) -> int:
        '''
        The number of control points.

        Returns
        -------
        int
        '''
        return self._q


    @property
    def n(self) -> int:
        '''
        The number of points.

        Returns
        -------
        int
        '''
        return self._n


    @property
    def m(self) -> int:
        '''
        The number of sampling locations.

        Returns
        -------
        int
        '''
        return self._m


    @property
    def control_point_separations(self) -> List[float]:
        '''
        The separations between control points.

        Returns
        -------
        List[float]
        '''
        return self._control_point_separations


    @property
    def control_points(self) -> Optional[np.ndarray]:
        '''
        The control points for the optimization.

        Returns
        -------
        Optional[np.ndarray]
        '''
        return self._control_points


    @property
    def control_point_idxs(self) -> List[int]:
        '''
        The indices of the control points.

        Returns
        -------
        List[int]
        '''
        return self._control_point_idxs


    @property
    def points(self) -> np.ndarray:
        '''
        The points on which intensities are measured and
        residuals are computed.

        Returns
        -------
        np.ndarray
        '''
        return self._points



    @property
    def interpolation_neighbours(self) -> int:
        '''
        The number of nearest neighbours to use in the IDW
        interpolation.

        Returns
        -------
        int
        '''
        return self._interpolation_neighbours


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
    def a(self) -> Optional[csr_matrix]:
        '''
        The interpolation matrix.

        Returns
        -------
        (N, Q) Optional[csr_matrix]
        '''
        return self._a


    @property
    def a_t(self) -> Optional[csr_matrix]:
        '''
        The transpose of the interpolation matrix.

        Returns
        -------
        (Q, N) Optional[csr_matrix]
        '''
        return self._a_t


    def _update_interpolation_matrix(self, sigma: float) -> None:
        '''
        Update the interpolation matrix using the current
        points, control points, distance power, and number
        of nearest neighbours.

        Parameters
        ----------
        sigma : float
            The standard deviation of the Gaussian weighting
        '''
        self._a = compute_gaussian_distance_weighting_transformation(
            self._points, self._control_points,
            sigma, self._interpolation_neighbours,
        )

        self._a_t = self._a.T



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


    def _compute_loss_and_jacobian(
        self,
        control_params: np.ndarray
    ) -> Tuple[float, np.ndarray]:
        '''
        Compute the loss and Jacobian of the loss with respect to
        the control parameters for the optimization step, where
        there are separate sets of model parameters applied to
        each point.

        Parameters
        ----------
        control_params : ((2 * Q) + 3, 1) np.ndarray
            The control parameters: [m_1, ..., m_Q, t_1, ..., t_Q, s, b, sigma]

        Returns
        -------
        Tuple[float, ((2 * Q) + 3,) np.ndarray]
            The loss and Jacobian of the loss with respect to the
            control parameters.
        '''
        m = self.a @ control_params[:self.q].reshape(self.q, 1)
        t = self.a @ control_params[self.q:(2 * self.q)].reshape(self.q, 1)
        rho_s = control_params[-3].reshape(1,1)
        rho_b = control_params[-2].reshape(1,1)
        sigma = control_params[-1].reshape(1,1)
        fhat_ij, dfhat_ij_gradient = self.treece_model.compute_intensities_and_derivatives(
            self.x_j, m, t, rho_s, rho_b, sigma
        )
        r_ij = fhat_ij - self.f_ij
        loss = 0.5 * (self._gamma_j * np.power(r_ij, 2)).mean(axis=1).mean(axis=0)
        jacobian = np.concatenate([
            self.a_t @ (self._gamma_j * r_ij * dfhat_ij_gradient[0]).mean(axis=1) / self.n,
            self.a_t @ (self._gamma_j * r_ij * dfhat_ij_gradient[1]).mean(axis=1) / self.n,
            np.asarray([
                (self._gamma_j * r_ij * dfhat_ij_dp).mean() / self.n
                for dfhat_ij_dp in dfhat_ij_gradient[2:]
            ])
        ])
        return loss, jacobian


    def _update_control_points(self, separation: float) -> None:
        '''
        Update the control points using a random sampling
        strategy.

        Parameters
        ----------
        separation : float
            The minimum separation between control points.
        '''
        self._control_point_idxs = []
        candidates = set(range(len(self.points)))
        for i in trange(len(candidates)):
            p = np.random.choice(list(candidates))
            self._control_point_idxs.append(p)
            d = np.linalg.norm(self.points[p,:] - self.points, ord=2, axis=1)
            candidates -= set(np.where(d < separation)[0])
            if not candidates:
                break
        self._control_points = self.points[self._control_point_idxs, :]
        self._q = len(self._control_point_idxs)
        self._update_interpolation_matrix(separation)


    def fit(self) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        '''
        Fit the model to the data.

        Returns
        -------
        Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]
            The fitted parameters: m, t, rho_s, rho_b, sigma.
        '''

        bounds = list(zip(
            [
                self.x_j.min(), self.t_bounds[0],
                self.rho_s_bounds[0], self.rho_b_bounds[0], self.sigma_bounds[0]
            ],
            [
                self.x_j.max(), self.t_bounds[1],
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

        m = result.x[0] * np.ones((self.n,))
        t = result.x[1] * np.ones((self.n,))
        rho_s = result.x[-3]
        rho_b = result.x[-2]
        sigma = result.x[-1]

        for si, separation in enumerate(self.control_point_separations):
            if ~self.silent:
                message(
                    f"Multiscale global model fit "
                    f"{si + 1} / {len(self.control_point_separations)}: "
                    f"separation = {separation:0.3e}"
                )

            self._update_control_points(separation)

            bounds = list(zip(
                (
                    [self.x_j.min()] * self.q
                    + [self.t_bounds[0]] * self.q
                    + [self.rho_s_bounds[0], self.rho_b_bounds[0], self.sigma_bounds[0]]
                ),
                (
                    [self.x_j.max()] * self.q
                    + [self.t_bounds[1]] * self.q
                    + [self.rho_s_bounds[1], self.rho_b_bounds[1], self.sigma_bounds[1]]
                )
            ))

            initial_guess = np.concatenate([
                m[self.control_point_idxs],
                t[self.control_point_idxs],
                result.x[-3:]
            ])

            result = minimize(
                self._compute_loss_and_jacobian,
                x0=initial_guess,
                bounds=bounds,
                method="L-BFGS-B",
                options=minimize_options,
                jac=True
            )
            m = self.a @ result.x[:self.q]
            t = self.a @result.x[self.q:(2 * self.q)]
            rho_s = result.x[-3]
            rho_b = result.x[-2]
            sigma = result.x[-1]

        return (m, t, rho_s, rho_b, sigma)
