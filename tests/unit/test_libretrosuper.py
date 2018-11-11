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

""" Test LibretroSuper """

from unittest import mock

import pytest

from kodi_game_scripting.libretro_super import LibretroSuper
from kodi_game_scripting.git_access import GitHubRepo

pytestmark = [pytest.mark.unit]


# pylint: disable=redefined-outer-name

def test_libretrosuper_fetchreset(mocker):
    """ Test fetching libretro-super repository """
    gitrepomock = mocker.patch(
        'kodi_game_scripting.libretro_super.GitRepo', autospec=True)
    LibretroSuper('dir').fetch_and_reset()
    gitrepomock.assert_called_once_with(
        GitHubRepo('libretro-super',
                   'https://github.com/libretro/libretro-super.git', ''),
        'dir')
    gitrepomock.return_value.fetch_and_reset.assert_called_once_with()


def test_libretrosuper_parseinfofile(mocker):
    """ Test loading info files from libretro-super """
    isfilemock = mocker.patch('os.path.isfile', return_value=True)
    mocker.patch('builtins.open', mock.mock_open(read_data='#comment\na=1'))
    info = LibretroSuper('').parse_info_file('mylib')
    assert info['a'] == '1'
    assert isfilemock.mock_calls


def test_libretrosuper_parseinfofilenofile(mocker):
    """ Test failure loading info files from libretro-super """
    isfilemock = mocker.patch('os.path.isfile', return_value=False)
    info = LibretroSuper('').parse_info_file('mylib')
    assert not info
    assert isfilemock.mock_calls
