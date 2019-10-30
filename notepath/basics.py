#!/usr/bin/env python3
# The function annotations in this module require Python 3.5 or higher.

import os
import textwrap

from itertools import chain
from typing import Dict, List, Union

# Type aliases
FilePath = str
NotePath = str
SQLSelectStatement = str


def get_data_path(filename: str) -> FilePath:
    path = os.path.dirname(os.path.dirname(__file__))
    path = os.path.join(path, 'data', filename)
    return path

def sort_notepaths(notepaths: List[NotePath]) -> List[NotePath]:
    '''Sort notepaths so that parents and children are never separated.
    
    The problem is this: We use the slash character ('/', chr(47)) to
    separate the parts of a notepath, so that 'a' is the parent of 'a/b'.
    If a notepath contains characters that sort before the slash, such as
    the space (chr(32)) or the comma (chr(44)), then after the list of
    notepaths is sorted, such a notepath may wind up separating a parent
    with a similar name from its children, when a parent's children should
    immediately follow the parent.
    
    Example: if the items are ['a/b', 'a', and 'a(b)'], then items.sort()
    produces ['a', 'a(b)', 'a/b']. We want ['a', 'a/b', 'a(b)'] instead.
    
    So we ask the sort method to replace each slash character with a
    character that is (1) guaranteed to sort before any other character
    that is ever likely to be found in a text file and (2) unlikely to
    ever appear in a text file itself (much less in any of the parts of a
    notepath). The character with the smallest codepoint value is the null
    character, which Python allows in strings.
    
    (We also ask the sort method to ignore case.)
    '''
    notepaths.sort(key=lambda s: s.lower().replace('/', chr(0)))
    return notepaths


class Object():
    def _error(self, *args, **kwargs):
        '''Print message to stderr instead of stdout.'''
        print(*args, file=sys.stderr, **kwargs)
    
    def _flatten_arg(self, arg) -> Union[List, None]:
        try:
            flat = list(chain.from_iterable(arg))
        except TypeError:
            flat = None
        return flat

    def _wrap(self, text: str): # I may get rid of this if I don't use it.
        lines = textwrap.wrap(text, width=80)
        for line in lines:
            print(line)


