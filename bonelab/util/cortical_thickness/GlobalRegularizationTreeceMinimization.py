from __future__ import annotations


from typing import Tuple, Optional
import numpy as np
from scipy.optimize import minimize
from scipy.spatial import KDTree
from scipy.sparse import csr_matrix

from bonelab.util.cortical_thickness.BaseTreeceMinimization import BaseTreeceMinimization


class GlobalRegularizationTreeceMinimization(BaseTreeceMinimization):
    '''
    Class to perform the global Treece minimization using a
    spatial regularization approach.
    '''

    def __init__(
        self,
        points: np.ndarray,
        neighbours_regularization: int,
        sigma_regularization: float,
        lambda_regularization: float,
        *args,
        **kwargs
    ) -> None:
        '''
        Initialization function.
        '''
        super().__init__(*args, **kwargs)
        self._points = points
        self._n = points.shape[0]
        self._m = self.x_j.shape[0]
        self._a = None
        self._a_t = None
        self._neighbours_regularization = neighbours_regularization
        self._sigma_regularization = sigma_regularization
        self._construct_regularization_matrix()
        self._lambda_regularization = lambda_regularization
        self._t0 = None
        self._rho_c_0 = None


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
    def neighbours_regularization(self) -> int:
        '''
        Get the number of neighbours to use for regularization.

        Returns
        -------
        int
            The number of neighbours to use for regularization.
        '''
        return self._neighbours_regularization


    @property
    def sigma_regularization(self) -> float:
        '''
        Get the standard deviation of the Gaussian weighting.

        Returns
        -------
        float
            The standard deviation of the Gaussian weighting.
        '''
        return self._sigma_regularization



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


    @property
    def lambda_regularization(self) -> float:
        '''
        Get the regularization coefficient.

        Returns
        -------
        float
            The regularization coefficient.
        '''
        return self._lambda_regularization

    @property
    def t0(self) -> Optional[float]:
        '''
        The thickness fit in the initial global optimization.

        Returns
        -------
        Optional[float]
        '''
        return self._t0

    @property
    def rho_c_0(self) -> Optional[float]:
        '''
        The cortical density value to use for regularization scaling.

        Returns
        -------
        Optional[float]
        '''
        return self._rho_c_0


    def _construct_regularization_matrix(self) -> None:
        '''
        Update the regularization matrix.
        '''

        kdtree = KDTree(self.points)
        distances, cols = kdtree.query(self.points, self.neighbours_regularization)
        rows = (
            np.ones((1, self.neighbours_regularization), dtype=int)
            * np.arange(self.n).reshape(self.n, 1)
        )
        vals = (
            ( 1 / (self.sigma_regularization * np.sqrt(2 * np.pi)) )
            * np.exp( -0.5 * (distances / self.sigma_regularization)**2 )
        )
        vals[rows==cols] = 0
        vals = -vals / vals.sum(axis=1)[:,None]
        vals[rows==cols] = 1
        self._a = csr_matrix(
            (vals.flatten(), (rows.flatten(), cols.flatten())),
            shape=(self.n, self.n)
        )
        self._a_t = self._a.T


    def _compute_loss_and_jacobian(
        self,
        params: np.ndarray
    ) -> Tuple[float, np.ndarray]:
        '''
        Compute the loss and the Jacobian of the loss.

        Parameters
        ----------
        params : np.ndarray
            The parameters to optimize.

        Returns
        -------
        Tuple[float, np.ndarray]
            The loss and the Jacobian of the loss.
        '''

        m = params[:self.n].reshape(self.n, 1)
        t = params[self.n:(2 * self.n)].reshape(self.n, 1)
        rho_s = params[-3].reshape(1,1)
        rho_b = params[-2].reshape(1,1)
        sigma = params[-1].reshape(1,1)
        fhat_ij, dfhat_ij_gradient = self.treece_model.compute_intensities_and_derivatives(
            self.x_j, m, t, rho_s, rho_b, sigma
        )
        r_ij = fhat_ij - self.f_ij

        loss = 0.5 * (
            (self._gamma_j * np.power(r_ij, 2)).mean()
            + self.lambda_regularization * (self._rho_c_0 ** 2) / (self._t0) * (
                np.power(self.a @ m.reshape(self.n), 2).mean()
                + np.power(self.a @ t.reshape(self.n), 2).mean()
            )
        )
        jacobian = np.concatenate([
            (1 / self.n) * (
                (self.gamma_j * r_ij * dfhat_ij_gradient[0]).mean(axis=1)
                + (
                    self.lambda_regularization * (self._rho_c_0 ** 2) / (self._t0)
                    * self.a_t @ (self.a @ m.reshape(self.n))
                )
            ),
            (1 / self.n) * (
                (self.gamma_j * r_ij * dfhat_ij_gradient[1]).mean(axis=1)
                + (
                    self.lambda_regularization * (self._rho_c_0 ** 2) / (self._t0)
                    * self.a_t @ (self.a @ t.reshape(self.n))
                )
            ),
            np.asarray([
                (self._gamma_j * r_ij * dfhat_ij_dp).mean() / self.n
                for dfhat_ij_dp in dfhat_ij_gradient[2:]
            ])
        ])
        return loss, jacobian


    def fit(self) -> Tuple[np.ndarray, np.ndarray, float, float, float]:
        '''
        Fit the Treece model to the intensity profiles.

        Returns
        -------
        Tuple[np.ndarray, np.ndarray, float float, float]
            The fitted parameters: m, t, rho_s, rho_b, sigma.
        '''
        m, t, rho_s, rho_b, sigma = self._initial_fit()
        self._t0 = t.mean()
        self._rho_c_0 = np.max(self.rho_c)
        initial_guess = np.concatenate([
            m, t, np.array([rho_s, rho_b, sigma])
        ])
        bounds = list(zip(
            (
                [self.x_j.min()] * self.n
                + [self.t_bounds[0]] * self.n
                + [self.rho_s_bounds[0], self.rho_b_bounds[0], self.sigma_bounds[0]]
            ),
            (
                [self.x_j.max()] * self.n
                + [self.t_bounds[1]] * self.n
                + [self.rho_s_bounds[1], self.rho_b_bounds[1], self.sigma_bounds[1]]
            )
        ))
        result = minimize(
            self._compute_loss_and_jacobian,
            x0=initial_guess,
            bounds=bounds,
            method="L-BFGS-B",
            options=self.minimize_options,
            jac=True
        )
        m = result.x[:self.n]
        t = result.x[self.n:(2 * self.n)]
        rho_s = result.x[-3]
        rho_b = result.x[-2]
        sigma = result.x[-1]
        return (m, t, rho_s, rho_b, sigma)
