from __future__ import absolute_import

import importlib
import os
import sys

from market_maker.utils.dotdict import dotdict
import market_maker._settings_base as baseSettings
import json
import os.path





def import_path(fullpath):
    """
    Import a file with full path specification. Allows one to
    import from anywhere, something __import__ does not do.
    """
    path, filename = os.path.split(fullpath)
    filename, ext = os.path.splitext(filename)
    sys.path.insert(0, path)
    module = importlib.import_module(filename, path)
    importlib.reload(module)  # Might be out of date
    del sys.path[0]
    return module


userSettings = import_path(os.path.join('.', 'settings'))
symbolSettings = None
symbol = sys.argv[1] if len(sys.argv) > 1 else None
if symbol:
    print("Importing symbol settings for %s..." % symbol)
    try:
        symbolSettings = import_path(os.path.join('..', 'settings-%s' % symbol))
    except Exception as e:
        print("Unable to find settings-%s.py." % symbol)

#Load override file

#settings_file_location = os.path.join('.', 'settings.json')
path = os.path.abspath(__file__)
dir_path = os.path.dirname(path)
settings_file_location = os.path.join(dir_path , 'settings.json')
override_settings = {}
#if os.path.exists(settings_file_location):
#    print("IT DOES EXIST!")
print(settings_file_location)
with open(settings_file_location, 'r') as settings_file:
    override_settings = json.load(settings_file)


# Assemble settings.
settings = {}
settings.update(vars(baseSettings))
settings.update(vars(userSettings))
settings.update(vars(dotdict(override_settings)))
if symbolSettings:
    settings.update(vars(symbolSettings))

# Main export
settings = dotdict(settings)
