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

"""Test the Template Processor"""

import filecmp
import os

import pytest

from kodi_game_scripting.template_processor import TemplateProcessor, \
    TEMPLATE_DIR

pytestmark = [pytest.mark.integration]


# pylint: disable=redefined-outer-name

REFERENCE_DIR = os.path.join(
    os.path.dirname(os.path.realpath(__file__)),
    'test_data', os.path.splitext(os.path.basename(__file__))[0])


def test_process_template(tmpdir):
    """Test the Template Processor"""
    data = {
        'game': {
            'name': 'mygame',
            'addon': 'game.libretro.mygame',
            'debian_package': 'game-libretro-mygame',
            'branch': 'master',
            'version': '2.10.3',
        },
        'libretro_repo': {
            'branch': 'master',
        },
    }
    extdata = {
        'system_info': {
            'extensions': ['ext1', 'ext2']
        },
        'settings': [
            {'id': 1, 'description': 'mysetting1',
             'values': ['value1', 'value2'], 'default': 'value1'},
            {'id': 2, 'description': 'mysetting2',
             'values': ['value1', 'value2'], 'default': 'value2'},
        ],
    }

    print('Template dir: file://{}'.format(TEMPLATE_DIR))
    print('Reference dir: file://{}'.format(REFERENCE_DIR))
    print('Test dir: file://{}'.format(tmpdir))

    template_processor = TemplateProcessor()

    # First generation step skips reading previously generated data.
    # Also don't yet provide all data so that we execute more branches.
    template_processor.process(TEMPLATE_DIR, str(tmpdir), data)

    # Add more data and run generation again.
    data.update(extdata)
    template_processor.process(TEMPLATE_DIR, str(tmpdir), data)

    # Run the generation and include data from the previously generated files.
    template_processor.process(TEMPLATE_DIR, str(tmpdir), data)

    def assert_identical(dircmp):
        assert not dircmp.right_only and not dircmp.diff_files
        for subdircmp in dircmp.subdirs.values():
            assert_identical(subdircmp)

    assert_identical(filecmp.dircmp(str(tmpdir), REFERENCE_DIR))
