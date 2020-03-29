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


# pylint: disable=redefined-outer-name

REFERENCE_DIR = os.path.join(
    os.path.dirname(os.path.realpath(__file__)),
    'test_data', os.path.splitext(os.path.basename(__file__))[0])


def compile_testlibrary(build_dir):
    """ Compile libretro_test """
    test_file = os.path.join(build_dir, 'libretro_test.{}'.format(
        LibretroWrapper.EXT))

    subprocess.run([os.environ.get('CMAKE', 'cmake'), REFERENCE_DIR],
                   cwd=build_dir, check=True)
    subprocess.run([os.environ.get('CMAKE', 'cmake'), '--build', '.'],
                   cwd=build_dir, check=True)
    assert os.path.isfile(test_file)
    return test_file


def test_load_library(tmpdir):
    """ Test LibretroWrapper """
    lib = LibretroWrapper(compile_testlibrary(str(tmpdir)))
    print(lib.system_info)
    assert lib.system_info.name == 'libraryname'
    assert lib.system_info['name'] == 'libraryname'
    print(lib.variables)
    assert len(lib.variables) == 2
