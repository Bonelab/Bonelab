'''Utility function for writing and reading points'''
import os

def write_points(points, filename, delimiter=',', precision=None):
    '''Read in points from a file

    This function utilizes the factory method classes in VTK with
    some added functionality for working with the AIM, nifti, and
    dicom readers.

    Args:
        points (list):      The points in a list of list
        filename (string):  Image to be read in
        delimiter (string): Delimiter string
        precision (int):    Number of decimal points of precision

    Returns:
        None
    '''
    if precision:
        formatter = '{{:.{}f}}'.format(precision)
    else:
        formatter = '{}'
        
    print(formatter)

    with open(filename, 'w') as fp:
        for point in points:
            entry = delimiter.join([formatter.format(float(x)) for x in point])
            entry += os.linesep
            fp.write(entry)

def read_points(filename, delimiter=','):
    '''Read in points from a file

    This function utilizes the factory method classes in VTK with
    some added functionality for working with the AIM, nifti, and
    dicom readers.

    Args:
        filename (string):  Image to be read in
        delimiter (string): Delimiter string

    Returns:
        points (list):      The points in a list of list
    '''
    points = []
    with open(filename, 'r') as fp:
        for cnt, line in enumerate(fp):
            points.append([float(x) for x in line.split(delimiter)])
    return points
