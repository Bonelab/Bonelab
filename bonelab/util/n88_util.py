'''Helper functions for extracting n88 results'''

import numpy as np
from netCDF4 import Dataset
import os

def valid_fields():
    '''List of valid element field names

    Because fields do not have the same range (scalars vs
    matricies), some care is taken to allow these fields to
    be extracted from a single name

    Args:
        None

    Returns:
        list:              valid names
    '''
    return [
        'StrainEnergyDensity', 'VonMisesStress',
        'StressXX', 'StressYY', 'StressZZ',
        'StressXY', 'StressYZ', 'StressXZ',
        'StrainXX', 'StrainYY', 'StrainZZ',
        'StrainXY', 'StrainYZ', 'StrainXZ'
    ]

def grab_field(solution, field_name):
    '''Given a solution group and field_name, extract the field

    Because fields do not have the same range (scalars vs
    matricies), some care is taken to allow these fields to
    be extracted from a field name.

    See `valid_fields` for which fields are expected

    Args:
        solution (root.groups["Solutions"]):    The solution
        field_name (string):                    Field name

    Returns:
        np.ndarray: Field
    '''
    # Structure some preamble
    name_map = {
        'StrainEnergyDensity': 'StrainEnergyDensity',
        'VonMisesStress': 'VonMisesStress',
    }

    matrix_values = ['Strain', 'Stress']

    direction_map = {
        'XX':0, 'YY':1, 'ZZ':2,
        'XY':3, 'YZ':4, 'XZ':5,
    }

    for matrix_name in matrix_values:
        for direction in direction_map.keys():
            name_map[matrix_name+direction] = matrix_name

    # Check input
    if field_name not in name_map.keys():
        raise IndexError('Could find fine field named {} from available keys {}. A typo?'.format(field_name, ', '.join(name_map.keys())))

    # Determine if element even exists
    elementValues = solution.groups["ElementValues"]
    element_name = name_map[field_name]
    if element_name not in elementValues.variables.keys():
        raise IndexError('Could find fine field named {} from available keys {}. Is the model solved?'.format(element_name, ', '.join(elementValues.variables.keys())))

    # Read out
    if element_name in matrix_values:
        index = direction_map[field_name[-2:]]

        field = np.zeros(elementValues.variables[element_name].shape[0], np.float64)
        field[:] = elementValues.variables[element_name][:, index]
    else:
        field = np.zeros(elementValues.variables[element_name].shape, np.float64)
        field[:] = elementValues.variables[element_name][:]

    return field

def field_to_image(filename, field_name, outside_value=0.0):
    '''Extract an element field into an image

    Because fields do not have the same range (scalars vs
    matricies), some care is taken to allow these fields to
    be extracted from a field name.

    See `valid_fields` for which fields are expected

    Args:
        filename (str):         N88 model filename on disk
        field_name (string):    Which field to extract
        outside_value (float):  Value to voxels outside FE domain

    Returns:
        np.ndarray: Field
    '''
    # Read file
    root = Dataset(filename, "r")

    # Check if solved
    if "Solutions" not in root.groups:
        raise IndexError('No solutions available in model. Is the model solved?')

    # Get active groups
    activeSolution = root.groups["Solutions"].groups[root.ActiveSolution]
    activeProblem = root.groups["Problems"].groups[activeSolution.Problem]
    activePart = root.groups["Parts"].groups[activeProblem.Part]

    # Grab field
    field = grab_field(activeSolution, field_name)
    n_elements = len(field)

    # Grab hexahedrons and nodes for reading back into image
    hexahedrons = activePart.groups["Elements"].groups["Hexahedrons"]

    node_numbers = np.zeros(hexahedrons.variables["NodeNumbers"].shape, np.int32)
    node_numbers[:] = hexahedrons.variables["NodeNumbers"][:]

    node_coords = np.zeros(activePart.variables["NodeCoordinates"].shape, np.float64)
    node_coords[:] = activePart.variables["NodeCoordinates"][:]

    # Determine spacing
    spacing = np.array([np.Inf, np.Inf, np.Inf])
    for i in range(8):
        node1 = node_coords[node_numbers[0, i]-1, :]
        for j in range(i+1, 8):
            node2 = node_coords[node_numbers[0, j]-1, :]
            d_node = np.abs(node2 - node1)
            d_node[d_node == 0] = np.Inf
            spacing = np.minimum(spacing, d_node)

    # Determine origin
    origin = np.array([np.Inf, np.Inf, np.Inf])
    bounds_max = np.array([-np.Inf, -np.Inf, -np.Inf])
    for k in range(hexahedrons.dimensions["NumberOfElements"].size):
        center = np.array([0.0, 0.0, 0.0])
        for i in range(8):
            node = node_coords[node_numbers[k, i]-1, :]
            center += node
        center /= 8.0

        origin = np.minimum(origin, center)
        bounds_max = np.maximum(bounds_max, center)
    dimensions = 1+np.round((bounds_max - origin)/spacing).astype(int)

    # Read out field
    n = 0
    image = outside_value*np.ones(dimensions)
    for k in range(hexahedrons.dimensions["NumberOfElements"].size):
        center = np.array([0.0, 0.0, 0.0])
        for i in range(8):
            node = node_coords[node_numbers[k, i]-1, :]
            center += node
        center /= 8.0
        image_index = np.round((center - origin)/spacing).astype(int)
        image[tuple(image_index)] = field[k]
        n+=1

    return image, spacing, origin, n_elements
