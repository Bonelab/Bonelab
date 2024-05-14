from __future__ import annotations


from typing import Tuple, Optional
import numpy as np
from scipy.optimize import minimize
from scipy.spatial import KDTree
from scipy.sparse import csr_matrix

from bonelab.util.cortical_thickness.BaseTreeceMinimization import BaseTreeceMinimization
from bonelab.util.cortical_thickness.ctth_util import compute_gaussian_distance_weighting_transformation


def compute_gaussian_distance_weighting_transformation(
    points: np.ndarray,
    control_points: np.ndarray,
    sigma: float,
    neighbours: int,
    eps: float = 1e-8
) -> csr_matrix:
    '''
    Compute the nearest-neighbour Gaussian distance weighting
    transformation matrix.

    Parameters
    ----------
    points : np.ndarray
        The points of the PolyData object.

    control_points : np.ndarray
        The control points.

    sigma : float
        The power of the inverse distance weighting.

    neighbours : int
        The number of neighbours to consider.

    diagonal_value : Optional[int]
        The value to set the diagonal elements to. If None, the diagonal
        elements are left as is.

    eps : float
        A small value to avoid division by zero.

    Returns
    -------
    csr_matrix
        The inverse distance weighting transformation matrix.
        Usage: y = A @ c
        y : (P,) np.ndarray
            Data values on the points
        A : (P,Q) csr_matrix
            The inverse distance weighting transformation matrix
        c : (Q,) np.ndarray
            The control point values
    '''
    n_points = points.shape[0]
    n_control_points = control_points.shape[0]

    neighbours = min(neighbours, n_control_points)

    kdtree = KDTree(control_points)
    distances, cols = kdtree.query(points, neighbours)
    rows = (
        np.ones((1, neighbours), dtype=int)
        * np.arange(n_points).reshape(n_points, 1)
    )
    distances = (
        ( 1 / (sigma * np.sqrt(2 * np.pi)) )
        * np.exp( -0.5 * (distances / sigma)**2 )
    )

    if diagonal_value is not None:
        npts, nnbrs = distances.shape
        use_distance = (cols != rows)
        distances = distances[use_distance].reshape(npts, nnbrs - 1)
        cols = cols[use_distance].reshape(npts, nnbrs - 1)
        rows = rows[use_distance].reshape(npts, nnbrs - 1)


    vals = distances / distances.sum(axis=1)[:,None]

    if diagonal_value is not None:
        vals = np.hstack([vals, np.ones((n_points, 1)) * diagonal_value])
        cols = np.hstack([cols, np.arange(n_control_points)])
        rows = np.hstack([rows, np.arange(n_points)])

    return csr_matrix(
        (vals.flatten(), (rows.flatten(), cols.flatten())),
        shape=(n_points, n_control_points)
    )



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
            + self.lambda_regularization * (
                np.power(self.a @ m.reshape(self.n), 2).mean()
                + np.power(self.a @ t.reshape(self.n), 2).mean()
            )
        )
        jacobian = np.concatenate([
            (1 / self.n) * (
                (self.gamma_j * r_ij * dfhat_ij_gradient[0]).mean(axis=1)
                + self.lambda_regularization * self.a_t @ (self.a @ m.reshape(self.n))
            ),
            (1 / self.n) * (
                (self.gamma_j * r_ij * dfhat_ij_gradient[1]).mean(axis=1)
                + self.lambda_regularization * self.a_t @ (self.a @ t.reshape(self.n))
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
