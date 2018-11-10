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

import pytest

from kodi_game_scripting import config
from kodi_game_scripting.git_access import GitHubOrg, GitHubRepo, GitRepo

pytestmark = [pytest.mark.integration]


def test_git_fetchresetsinglerepo(tmpdir):
    """ Tests fetching and resetting a single repo """
    gitrepo = GitRepo(
        GitHubRepo('kodi-game-scripting',
                   'https://github.com/fetzerch/kodi-game-scripting', ''),
        str(tmpdir))
    gitrepo.fetch_and_reset()


def test_github_repos():
    """ Tests getting a repo list """
    github = GitHubOrg(config.GITHUB_ORGANIZATION)
    repos = github.get_repos(config.GITHUB_ADDON_PREFIX)
    print(repos)
    assert repos
