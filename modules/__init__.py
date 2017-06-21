#thanks https://stackoverflow.com/a/16853487/1430838 !

import pkgutil
import inspect

__all__ = []

print("Importing modules")
for loader, name, is_pkg in pkgutil.walk_packages(__path__):
    print("Importing " + name)
    module = loader.find_module(name).load_module(name)

    globals()[name] = module
    __all__.append(name)

    for name, value in inspect.getmembers(module):
        if name.startswith('__'):
            continue
