# Copyright (C) 2016-2018 Christian Fetzer
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.

""" Test common utility functions """

import pytest

from kodi_game_scripting.template_processor import get_list, regex_replace

pytestmark = [pytest.mark.unit]


# pylint: disable=redefined-outer-name

def test_getlist():
    """ Test the get_list filter """
    assert get_list([]) == []
    assert get_list(None) == [None]
    assert get_list('') == ['']
    assert get_list('test') == ['test']
    assert get_list(['test1', 'test2']) == ['test1', 'test2']


def test_regexreplace():
    """ Test the regex_replace filter """
    assert(regex_replace('aabbcc', r'(b+)', '-\\1-')) == 'aa-bb-cc'


def test_regexreplace_multiline():
    """ Test the regex_replace filter with a multiline string """
    assert(regex_replace('a\nbb\nc', r'(b+)\n', '', multiline=True)) == 'a\nc'
