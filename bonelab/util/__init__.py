"""
.. module:: bonelab.util
    :synopsis: Utility functions for common tasks
"""

# Imports
import os
import time

def echo_arguments(title, args):
    '''Echo the arguments passed to a function.

    Given the arguments as a dictionary, echo
    those arguments. This used in three instances:
        Local variables     echo_arguments('My function', locals())
        Argument parsing    echo_arguments('My script', vars(args))
        As a raw dictionary echo_arguments('My dict', dict)

    Args:
        title (string): Title to be printed
        args (dict):    Dictionary to be printed
    '''
    # Title
    message = title + ':' + os.linesep

    # Determine padding size
    max_length = 0
    for key in args:
        max_length = max(max_length, len(key))
    formatter = '  {{arg:<{spacing}}}{{value}}'.format(spacing=max_length+2)

    # Print arguments and values
    for key in args:
        message += formatter.format(arg=key, value=args[key]) + os.linesep

    # Display
    print(message)

