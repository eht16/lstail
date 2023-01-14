# -*- coding: utf-8 -*-
#
# This software may be modified and distributed under the terms
# of the MIT license.  See the LICENSE file for details.


########################################################################
class SafeMunch:
    """
    Simplified version of Munch (https://github.com/Infinidat/munch).
    Stripped down to the bare minimum for what we need (e.g. no YAML support, no serialisation).
    Implemented not as a subclass of dict but as plain object with only a few supporting methods.
    This is to reduce naming conflicts in case the names of the standard dictionary methods
    (e.g. "items", "values" or "update") are part of the dictionary keys.
    Hence the implemented methods are prefixed to lower the risk of name clashes.
    """

    # ----------------------------------------------------------------------
    def __init__(self, *args, **kwargs):
        self._data = dict(*args, **kwargs)

    # ----------------------------------------------------------------------
    @property
    def __dict__(self):
        return self._data

    # ----------------------------------------------------------------------
    def __getattr__(self, key):
        # only called if key not found in normal places
        try:
            # Throws exception if not in prototype chain
            return object.__getattribute__(self, key)
        except AttributeError as exc:
            try:
                return self._data[key]
            except KeyError:
                raise AttributeError(key) from exc

    # ----------------------------------------------------------------------
    def __setattr__(self, key, value):
        try:
            if key != '_data':  # _data is our own dictionary, so set it using base' __setattr__
                # Throws exception if not in prototype chain
                object.__getattribute__(self, key)
        except AttributeError:
            try:
                self._data[key] = safe_munchify(value)
            except Exception as exc:
                raise AttributeError(key) from exc
        else:
            object.__setattr__(self, key, value)

    # ----------------------------------------------------------------------
    def __delattr__(self, key):
        try:
            # Throws exception if not in prototype chain
            object.__getattribute__(self, key)
        except AttributeError:
            try:
                del self._data[key]
            except KeyError as exc:
                raise AttributeError(key) from exc
        else:
            object.__delattr__(self, key)

    # ----------------------------------------------------------------------
    def __contains__(self, key):
        return key in self._data

    # ----------------------------------------------------------------------
    def __iter__(self):
        return iter(self._data)

    # ----------------------------------------------------------------------
    def __eq__(self, other):
        return self._data == other

    # ----------------------------------------------------------------------
    def __repr__(self):
        return f'{self.__class__.__name__}({self._data!r})'

    # ----------------------------------------------------------------------
    def __getitem__(self, key):
        return self._data[key]

    # ----------------------------------------------------------------------
    def __setitem__(self, key, value):
        self._data[key] = safe_munchify(value)

    # ----------------------------------------------------------------------
    def sm_dict_update(self, *args, **kwargs):
        self._data.update(*args, **kwargs)

    # ----------------------------------------------------------------------
    def keys(self):
        # unfortunately we need to keep the "keys" method as (C)Python requires it for
        # kwargs magic to detect a mapping if it is not a subclass of "dict"
        # this might lead to name clashes :(
        return self._data.keys()

    # ----------------------------------------------------------------------
    def sm_dict_keys_flattened(self, data=None, separator='.'):
        """Return all keys, resolved recursively into one list"""
        keys = []
        if data is None:
            data = self._data
        for key in data:
            value = data[key]
            if isinstance(value, (self.__class__, dict)):
                sub_keys = self.sm_dict_keys_flattened(value, separator=separator)
                for sub_key in sub_keys:
                    sub_key_full = separator.join((key, sub_key))
                    keys.append(sub_key_full)
            else:
                keys.append(key)
        return keys

    __hash__ = None  # disable hashing


########################################################################
class DefaultSafeMunch(SafeMunch):
    """
    A SafeMunch that returns a user-specified value for missing keys.
    """

    # ----------------------------------------------------------------------
    def __init__(self, *args, **kwargs):
        if args:
            default = args[0]
            args = args[1:]
        else:
            default = None

        super().__init__(*args, **kwargs)
        self.__default__ = default

    # ----------------------------------------------------------------------
    def __getattr__(self, key):
        try:
            return super().__getattr__(key)
        except AttributeError:
            return self.__default__

    # ----------------------------------------------------------------------
    def __setattr__(self, key, value):
        if key == '__default__':
            return object.__setattr__(self, key, value)

        return super().__setattr__(key, value)

    # ----------------------------------------------------------------------
    def __getitem__(self, key):
        try:
            return super().__getitem__(key)
        except KeyError:
            return self.__default__

    # ----------------------------------------------------------------------
    def __repr__(self):
        return f'{type(self).__name__}({self.__undefined__!r}, {self._data})'


# ----------------------------------------------------------------------
def safe_munchify(data, factory=SafeMunch, default=None):
    if isinstance(data, dict):
        if factory == DefaultSafeMunch:
            return factory(
                default,
                ((key, safe_munchify(value, factory, default)) for key, value in data.items()))

        return factory((key, safe_munchify(value, factory, default)) for key, value in data.items())
    elif isinstance(data, (list, tuple, set)):
        data_type = type(data)
        if factory == DefaultSafeMunch:
            return data_type(safe_munchify(value, factory, default) for value in data)

        return data_type(safe_munchify(value, factory) for value in data)

    return data
