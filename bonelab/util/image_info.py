"""Shared aix-style image information output without loading the image again."""
import math
import os


def print_image_info(infile, image):
    """Print the standard aix header for an already loaded VTK image."""
    guard = '!-------------------------------------------------------------------------------'
    phys_dim = [x*y for x,y in zip(image.GetDimensions(), image.GetSpacing())]
    position = [math.floor(x/y) for x,y in zip(image.GetOrigin(), image.GetSpacing())]
    size = os.path.getsize(infile)
    names = ['Bytes', 'KBytes', 'MBytes', 'GBytes']
    i = 0
    while int(size) > 1024 and i < len(names) - 1:
        i+=1
        size = size / 2.0**10

    # Print header
    print('')
    print(guard)
    print('!>')
    print('!> dim                            {: >6}  {: >6}  {: >6}'.format(*image.GetDimensions()))
    print('!> off                                 x       x       x')
    print('!> pos                            {: >6}  {: >6}  {: >6}'.format(*position))
    print('!> element size in mm             {:.4f}  {:.4f}  {:.4f}'.format(*image.GetSpacing()))
    print('!> phys dim in mm                 {:.4f}  {:.4f}  {:.4f}'.format(*phys_dim))
    print('!>')
    print('!> Type of data               {}'.format(image.GetScalarTypeAsString()))
    print('!> Total memory size          {:.1f} {: <10}'.format(size, names[i]))
    print(guard)

