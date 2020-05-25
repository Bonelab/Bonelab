'''Utility function for printing a message with a time stamp'''

import os
import time

start_time = time.time()

def message(msg, *additionalLines):
    """Print message with time stamp.
    
    The first argument is printed with a time stamp.
    Subsequent arguments are printed one to a line without a timestamp.
    
    Put this next line at the start of your program before using
    start_time = time.time()
    """
    print(f'{(time.time()-start_time):8.2f} {msg}')
    for line in additionalLines:
        print(" " * 9 + line)
