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


def compile_testlibrary(build_dir, variant=''):
    """ Compile libretro_test """
    test_file = os.path.join(build_dir, 'libretro_test{}.{}'.format(
        variant, LibretroWrapper.EXT))

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
    assert lib.system_info.version == '123-ver'
    assert lib.system_info.extensions == ['a', 'bb', 'ccc']
    assert lib.system_info.need_fullpath is True
    assert lib.system_info.supports_no_game is True
    print(lib.options)
    assert len(lib.options) == 2


def test_core_options_v2(tmpdir):
    """ Test that a core hands over categories, help text and value labels """
    lib = LibretroWrapper(compile_testlibrary(str(tmpdir)))

    assert [(c.key, c.description, c.info) for c in lib.categories] == \
        [('video', 'Video', 'Change what the picture looks like.')]

    setting1, setting2 = lib.options

    assert setting1.id == 'setting1'
    assert setting1.description == 'Setting 1'
    assert setting1.info == 'What setting 1 does.'
    assert setting1.category == 'video'
    assert setting1.values == [('enabled', 'On'), ('disabled', 'Off')]
    # The core names a default that isn't the first value
    assert setting1.default == 'disabled'

    # An option is allowed to leave out everything that's optional
    assert setting2.id == 'setting2'
    assert setting2.info == ''
    assert setting2.category == ''
    assert setting2.values == [('0', ''), ('1', ''), ('2', ''), ('3', '')]
    assert setting2.default == '0'


def test_set_variables_fallback(tmpdir):
    """ Test the oldest API, which cores still fall back to """
    lib = LibretroWrapper(compile_testlibrary(str(tmpdir), '_variables'))

    assert lib.categories == []
    assert [(o.id, o.description, o.info, o.category) for o in lib.options] == \
        [('setting1', 'Setting 1', '', ''), ('setting2', 'Setting 2', '', '')]

    setting1 = lib.options[0]
    assert setting1.values == [('enabled', ''), ('disabled', '')]
    # This API has no way to name a default, so it's the first value
    assert setting1.default == 'enabled'


def test_options_registered_in_retro_init(tmpdir):
    """ Test a core that doesn't register its options until retro_init

    Cores that do this used to produce no settings.xml at all. """
    lib = LibretroWrapper(compile_testlibrary(str(tmpdir), '_init'))

    assert len(lib.categories) == 1
    assert [o.id for o in lib.options] == ['setting1', 'setting2']


def test_load_missing_library(tmpdir):
    """ Test that a library that can't be loaded says why """
    missing = os.path.join(str(tmpdir), 'does-not-exist.so')
    with pytest.raises(OSError) as excinfo:
        LibretroWrapper(missing)

    # A core that won't load is the everyday case, so the reason has to
    # survive the trip back from the helper process
    assert missing in str(excinfo.value)
    assert 'No such file' in str(excinfo.value)
