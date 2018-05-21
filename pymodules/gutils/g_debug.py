""" Debugging Utilities """


def trace(func):
    """ Decorator that prints signature of function calls.

    Useful when debugging recursive functions.
    """
    def wrapper(*args, **kwargs):
        result = func(*args, **kwargs)

        pretty_args = ''
        for arg in args:
            if pretty_args:
                pretty_args = '{}, {}'.format(pretty_args, arg)
            else:
                pretty_args = str(arg)

        pretty_kwargs = ''
        for key, value in kwargs.items():
            if pretty_kwargs or pretty_args:
                pretty_kwargs = '{}, {}={}'.format(pretty_kwargs, key, value)
            else:
                pretty_kwargs = '{}={}'.format(key, value)

        print('{0}({1}{2}) -> {3}'.format(func.__name__, pretty_args, pretty_kwargs, result))
        return result
    return wrapper
