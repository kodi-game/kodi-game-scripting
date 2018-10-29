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

""" Libretro Wrapper """

import os
import subprocess

import pytest

from kodi_game_scripting.libretro_ctypes import LibretroWrapper

pytestmark = [pytest.mark.integration]


def compile_testlibrary():
    """ Compile libretro_test """
    test_dir = os.path.join(
        os.path.dirname(os.path.realpath(__file__)),
        'test_data', os.path.splitext(os.path.basename(__file__))[0])
    test_file = os.path.join(test_dir, 'libretro_test.{}'.format(
        LibretroWrapper.EXT))

    subprocess.run([os.environ.get('CMAKE', 'cmake'), test_dir], cwd=test_dir)
    subprocess.run([os.environ.get('CMAKE', 'cmake'), '--build', '.'],
                   cwd=test_dir)
    assert os.path.isfile(test_file)
    return test_file


def test_load_library():
    """ Test LibretroWrapper """
    lib = LibretroWrapper(compile_testlibrary())
    print(lib.system_info)
    assert lib.system_info.name == 'libraryname'
    print(lib.variables)
    assert len(lib.variables) == 2

    lib2 = LibretroWrapper(compile_testlibrary())
    print(lib2.system_info)
    assert lib2.system_info.name == 'libraryname'
    print(lib2.variables)
    assert len(lib2.variables) == 2
