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

"""pytest configuration file"""

# pylint: disable=invalid-name

# pytest is configured to find tests in all *.py files. As it needs to import
# files, we have to exclude files that would cause import issues.
# See https://docs.pytest.org/en/latest/example/pythoncollection.html#
#     customizing-test-collection
collect_ignore = [
    'setup.py',
    'kodi_game_scripting/__main__.py',
    'process_game_addons.py'
]
