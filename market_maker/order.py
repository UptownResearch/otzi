from __future__ import absolute_import

import collections



# Find code directory relative to our directory
from os.path import dirname, abspath, join
import sys
THIS_DIR = dirname(__file__)
CODE_DIR = abspath(join(THIS_DIR, '..' ))
sys.path.insert(0, CODE_DIR)




class Order(collections.MutableMapping):
    """A class that represents an order"""

    def __init__(self, *args, **kwargs):
        self.store = dict()
        self.update(dict(*args, **kwargs))  # use the free update to set keys

    def __getitem__(self, key):
        return self.store[self.keytransform(key)]

    def __setitem__(self, key, value):
        self.store[self.keytransform(key)] = value

    def __delitem__(self, key):
        del self.store[self.keytransform(key)]

    def __iter__(self):
        return iter(self.store)

    def __len__(self):
        return len(self.store)

    def keytransform(self, key):
        return key