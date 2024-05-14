from __future__ import annotations

from typing import Optional, Tuple, List
import numpy as np
import pyvista as pv
from skimage.morphology import binary_erosion, binary_dilation
from tqdm import tqdm, trange


def dilate_mask(mask: pv.UniformGrid, dilate_amount: Tuple[int, int, int]) -> pv.UniformGrid:
    '''
    Dilate the mask.

    Parameters
    ----------
    mask : pv.UniformGrid
        The mask to dilate.

    dilate_amount : Tuple[int, int, int]
        The amount to dilate the mask by in each dimension.

    Returns
    -------
    pv.UniformGrid
        The dilated mask.
    '''
    mask_np = mask[mask.active_scalars_name].reshape(mask.dimensions, order="F")
    for i, d in enumerate(dilate_amount):
        dilation_shape = [1, 1, 1]
        dilation_shape[i] = 2 * d + 1
        dilation_shape = tuple(dilation_shape)
        mask_np = binary_dilation(mask_np, selem=np.ones(dilation_shape))
    mask[mask.active_scalars_name] = mask_np.flatten(order="F")
    return mask


def sample_all_intensity_profiles(
    image: pv.UniformGrid,
    points: np.ndarray,
    normals: np.ndarray,
    outside_dist: float,
    inside_dist: float,
    dx: float,
    constrain_normal_to_plane: Optional[int],
    silent: bool
):
    '''
    Sample intensity profiles along lines in the image.

    Parameters
    ----------
    image : pv.UniformGrid
        The image to sample from.

    points : np.ndarray
        The starting points of the lines.

    normals : np.ndarray
        The normal vectors for the lines.

    outside_dist : float
        The distance to start sampling from outside the points along the normals.

    inside_dist : float
        The distance to sample up to inside the points along the normals.

    dx : float
        The spacing between sample points.

    constrain_normal_to_plane : Optional[int]
        The index of the axis to constrain the normal vectors to. If None, no constraint is applied.

    silent : bool
        Set this flag to not show the progress bar.

    Returns
    -------
    Tuple[np.ndarray, np.ndarray]
        The sampled intensities and the x values of the sample points.
    '''
    if constrain_normal_to_plane:
        normals[:,constrain_normal_to_plane] = 0
    normals = normals / (np.sqrt((normals**2).sum(axis=-1))[:,np.newaxis] + 1e-6)
    x = np.arange(-outside_dist, inside_dist, dx)
    nx = x.shape[0]
    x = np.tile(x, points.shape[0])
    points = np.repeat(points, nx, axis=0)
    normals = np.repeat(normals, nx, axis=0)
    sample_points = pv.PolyData(points + x[:,np.newaxis]*normals)
    sample_points = sample_points.sample(image, progress_bar=~silent)
    intensities = np.array(sample_points["NIFTI"]).reshape(-1, nx)
    return intensities, x[:nx]


def compute_neighbours(pd: pv.PolyData, silent: bool) -> List[List[int]]:
    '''
    Compute the neighbours of each point in a PolyData object.

    Parameters
    ----------
    pd : pv.PolyData
        The PolyData object to compute the neighbours for.

    silent : bool
        Set this flag to not show the progress bar.

    Returns
    -------
    List[List[int]]
        The neighbours of each point.
    '''
    neighbours = []
    for i in trange(pd.n_points, disable=silent):
        neighbours.append([])
    for i in trange(pd.n_cells, disable=silent):
        cell_ids = pd.get_cell(i).point_ids
        for j in cell_ids:
            neighbours[j].extend(cell_ids)
    for i in trange(pd.n_points, disable=silent):
        neighbours[i] = list(set(neighbours[i]))
    return neighbours


def median_smooth_polydata(
    pd: pv.PolyData,
    scalar: str,
    flag_scalar: str,
    neighbours: Optional[List[List[int]]] = None,
    silent: bool = False
) -> pv.PolyData:
    '''
    Smooth the scalar values of a PolyData object using a median filter.

    Parameters
    ----------
    pd : pv.PolyData
        The PolyData object to smooth.

    scalar : str
        The name of the scalar to smooth.

    flag_scalar : str
        The name of the flag scalar that determines if the point is used.

    neighbours : Optional[List[List[int]]]
        The neighbours of each point in the PolyData object. If None, the neighbours are computed.

    silent : bool

    Returns
    -------
    pv.PolyData
        The smoothed PolyData object.
    '''
    if neighbours is None:
        neighbours = compute_neighbours(pd, silent)
    out = pd.copy()
    for i in tqdm(np.where(pd[flag_scalar] == 1)[0], disable=silent):
        flag = pd[flag_scalar][neighbours[i]] * (pd[scalar][neighbours[i]] > 0)
        vals = pd[scalar][neighbours[i]]
        out[scalar][i] = np.median(vals[flag==1])
    return out



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
