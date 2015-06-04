import inspect


# functions
def whoami():
    return inspect.stack()[1][3]


def whosdaddy():
    return inspect.stack()[2][3]
