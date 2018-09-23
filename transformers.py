#!/usr/bin/env python3

from collections.abc import Mapping

class SequenceIndexer:
    def __init__(self, data):
        self._data = list(data)
        self._mapping = self._make_mapping()

    def _make_mapping(self):
        return {item: idx for (idx, item) in enumerate(self._data)}

    def __getitem__(self, key):
        return self._mapping[key]

    def __delitem__(self, key):
        del self._data[self._mapping[key]]
        self._mapping = self._make_mapping()

    def __contains__(self, key):
        return key in self._mapping


class MirrorDict(Mapping):
    def __init__(self, *args, **kwargs):
        self._data = dict(*args, **kwargs)

    def __getitem__(self, key):
        if key not in self._data:
            return key
        return self._data[key]

    def __iter__(self):
        return iter(self._data)

    def __len__(self):
        return len(self._data)
