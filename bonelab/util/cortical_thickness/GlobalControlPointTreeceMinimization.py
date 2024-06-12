from __future__ import annotations

from typing import List, Optional, Tuple
import numpy as np
from scipy.spatial import KDTree
from scipy.sparse import csr_matrix
from scipy.optimize import minimize
from scipy.interpolate import RBFInterpolator
from tqdm import trange

from bonelab.util.time_stamp import message
from bonelab.util.cortical_thickness.BaseTreeceMinimization import BaseTreeceMinimization


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
        use_rbf_spline: bool,
        rbf_smooth: float,
        rbf_degree: int,
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

        use_rbf_spline : bool
            Whether to use a radial basis function spline for
            interpolation between / after optimizations.

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
        self._use_rbf_spline = use_rbf_spline
        self._rbf_smooth = rbf_smooth
        self._rbf_degree = rbf_degree


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
    def use_rbf_spline(self) -> bool:
        '''
        Whether to use a radial basis function spline for
        interpolation between / after optimizations.

        Returns
        -------
        bool
        '''
        return self._use_rbf_spline


    @property
    def rbf_smooth(self) -> float:
        '''
        The smoothing parameter for the RBF spline.

        Returns
        -------
        float
        '''
        return self._rbf_smooth


    @property
    def rbf_degree(self) -> int:
        '''
        The degree of the RBF spline.

        Returns
        -------
        int
        '''
        return self._rbf_degree


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
        neighbours = min(self.interpolation_neighbours, self.q)

        kdtree = KDTree(self.control_points)
        distances, cols = kdtree.query(self.points, neighbours)
        rows = (
            np.ones((1, neighbours), dtype=int)
            * np.arange(self.n).reshape(self.n, 1)
        )
        vals = (
            ( 1 / (sigma * np.sqrt(2 * np.pi)) )
            * np.exp( -0.5 * (distances / sigma)**2 )
        )

        self._a = csr_matrix(
            (
                (vals / vals.sum(axis=1)[:,None]).flatten(),
                (rows.flatten(), cols.flatten())
            ),
            shape=(self.n, self.q)
        )

        self._a_t = self._a.T


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
        rho_s = control_params[2 * self.q].reshape(1,1)
        rho_b = control_params[2 * self.q + 1].reshape(1,1)
        sigma = self.a @ control_params[(-self.q):].reshape(self.q, 1)
        fhat_ij, dfhat_ij_gradient = self.treece_model.compute_intensities_and_derivatives(
            self.x_j, m, t, rho_s, rho_b, sigma
        )
        r_ij = fhat_ij - self.f_ij
        loss = 0.5 * (self.gamma_j * np.power(r_ij, 2)).mean(axis=1).mean(axis=0)
        jacobian = np.concatenate([
            self.a_t @ (self.gamma_j * r_ij * dfhat_ij_gradient[0]).mean(axis=1) / self.n,
            self.a_t @ (self.gamma_j * r_ij * dfhat_ij_gradient[1]).mean(axis=1) / self.n,
            np.asarray([
                (self.gamma_j * r_ij * dfhat_ij_dp).mean() / self.n
                for dfhat_ij_dp in dfhat_ij_gradient[2:4]
            ]),
            self.a_t @ (self.gamma_j * r_ij * dfhat_ij_gradient[4]).mean(axis=1) / self.n,
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


    def fit(self) -> Tuple[np.ndarray, np.ndarray, float, float, np.ndarray]:
        '''
        Fit the model to the data.

        Returns
        -------
        Tuple[np.ndarray, np.ndarray, float, float, np.ndarray]
            The fitted parameters: m, t, rho_s, rho_b, sigma.
        '''
        m, t, rho_s, rho_b, sigma = self._initial_fit()
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
                    [self.x_bounds[0]] * self.q
                    + [self.t_bounds[0]] * self.q
                    + [self.rho_s_bounds[0], self.rho_b_bounds[0]]
                    + [self.sigma_bounds[0]] * self.q
                ),
                (
                    [self.x_bounds[1]] * self.q
                    + [self.t_bounds[1]] * self.q
                    + [self.rho_s_bounds[1], self.rho_b_bounds[1]]
                    + [self.sigma_bounds[1]] * self.q
                )
            ))
            initial_guess = np.concatenate([
                m[self.control_point_idxs],
                t[self.control_point_idxs],
                np.array([rho_s, rho_b]),
                sigma[self.control_point_idxs]
            ])
            result = minimize(
                self._compute_loss_and_jacobian,
                x0=initial_guess,
                bounds=bounds,
                method="L-BFGS-B",
                options=self.minimize_options,
                jac=True
            )
            if self.use_rbf_spline:
                m = RBFInterpolator(
                    self.control_points,
                    result.x[:self.q],
                    neighbors=self.interpolation_neighbours,
                    kernel="thin_plate_spline",
                    smoothing=self.rbf_smooth,
                    degree=self.rbf_degree
                )(self.points)
                t = RBFInterpolator(
                    self.control_points,
                    result.x[self.q:(2 * self.q)],
                    neighbors=self.interpolation_neighbours,
                    kernel="thin_plate_spline",
                    smoothing=self.rbf_smooth,
                    degree=self.rbf_degree
                )(self.points)
                sigma = RBFInterpolator(
                    self.control_points,
                    result.x[(-self.q):],
                    neighbors=self.interpolation_neighbours,
                    kernel="thin_plate_spline",
                    smoothing=self.rbf_smooth,
                    degree=self.rbf_degree
                )(self.points)
            else:
                m = self.a @ result.x[:self.q]
                t = self.a @ result.x[self.q:(2 * self.q)]
                sigma = self.a @ result.x[(-self.q):]
            rho_s = result.x[2 * self.q]
            rho_b = result.x[2 * self.q + 1]

        return (m, t, rho_s, rho_b, sigma)
