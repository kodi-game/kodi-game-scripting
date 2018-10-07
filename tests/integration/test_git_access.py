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

""" Test access GitHub API and Git Repos """

import os

from kodi_game_scripting import utils
from kodi_game_scripting.git_access import Git, GitRepo


def test_clone_single_repo():
    """ Tests cloning a single repo """
    test_dir = os.path.join(
        os.path.dirname(os.path.realpath(__file__)),
        'test_data', os.path.splitext(os.path.basename(__file__))[0])
    utils.ensure_directory_exists(test_dir, clean=True)

    gitaccess = Git()
    gitaccess.clone_repo(
        GitRepo('kodi-game-scripting',
                'https://github.com/fetzerch/kodi-game-scripting', ''),
        test_dir)
    gitaccess.clone_repos(
        [GitRepo('kodi-game-scripting',
                 'https://github.com/fetzerch/kodi-game-scripting', '')],
        test_dir)


def test_github_repos():
    """ Tests getting a repo list """
    gitaccess = Git()
    repos = gitaccess.get_repos('kodi-game', r'game\.libretro\.')
    print(repos)
    assert repos
