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

""" Test converting addon version into Kodi format """

import pytest

from kodi_game_scripting.versions import AddonVersion

pytestmark = [pytest.mark.unit]


def test_versions():
    """ Test some verson patterns """
    assert AddonVersion.get('GIT') == '1.0.0'
    assert AddonVersion.get('v081') == '0.81.0'
    assert AddonVersion.get('v10BETAXY') == '10.0.0'
    assert AddonVersion.get('v1.3e') == '1.3.0'
    assert AddonVersion.get('v12 ALPHA') == '12.0.0'
    assert AddonVersion.get('v2.5.0') == '2.5.0'
    assert AddonVersion.get('2') == '2.0.0'
    assert AddonVersion.get('2.3') == '2.3.0'
    assert AddonVersion.get('2.3.4') == '2.3.4'
