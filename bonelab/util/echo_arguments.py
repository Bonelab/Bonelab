'''Utility function for echoing command line arguments'''

import os


def echo_arguments(title, args):
    '''Echo the arguments passed to a function

    This is a convenience utility used most often at the start
    of a command line interface.
    
    It would typically be called as such:
    ```python
    def my_fun(arg1, arg2):
        print(echo_arguments('my_fun', locals()))

        # ... Whatever else you want to do
    ```
    or from argparse as such:
    ```python
        parser = argparse.ArgumentParser()
        
        # ... Setup parser

        # Parse and display
        args = parser.parse_args()
        print(echo_arguments('ImageConverter', vars(args)))
    ```

    Args:
        title (string):     Title of the program
        args (dictionary):  Dictionary of arguments, typically acquired through `locals()`

    Returns:
        string:             The formatted message, to be printed by whatever source
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

    return message
