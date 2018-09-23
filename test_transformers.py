#!/usr/bin/env python3

from transformers import SequenceIndexer, MirrorDict


def test_sequence_indexer_getitem():
    tuple_transformer = SequenceIndexer(('a', 'b', 'c'))
    assert tuple_transformer['a'] == 0
    assert tuple_transformer['b'] == 1
    assert tuple_transformer['c'] == 2


def test_sequence_indexer_delitem():
    tuple_transformer = SequenceIndexer(('a', 'b', 'c'))
    del tuple_transformer['b']
    assert tuple_transformer['a'] == 0
    assert tuple_transformer['c'] == 1


def test_sequence_indexer_contains():
    tuple_transformer = SequenceIndexer(('a', 'b', 'c'))
    assert 'a' in tuple_transformer


def test_mirror_dict_getitem():
    mirror = MirrorDict(a=1)
    assert mirror['a'] == 1
    assert mirror['b'] == 'b'
