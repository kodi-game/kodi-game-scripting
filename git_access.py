#!/usr/bin/env python3

# Copyright (C) 2016 Christian Fetzer
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

""" Access GitHub API and Git Repos """

import collections
import os
import shutil

import github
import git


GitRepo = collections.namedtuple('GitRepo', 'name url')


class Git:
    """ Access GitHub API and Git Repos """
    def __init__(self):
        """ Initialize Git instance """
        self._github = github.Github()

    def get_repos(self, organization, repo_filter):
        """ Get all repos of the given organization """
        return [GitRepo(repo.name, repo.clone_url) for repo in
                self._github.get_organization(organization).get_repos()
                if repo_filter in repo.name]

    def clone_repos(self, repos, directory):
        """ Clone list of repos into directory

            If the repos exist all changes will be discarded. """
        for repo in repos:
            self.clone_repo(repo, directory)

    @classmethod
    def clone_repo(cls, repo, directory):
        """ Clone repo into directory

            If the repo exists all changes will be discarded. """
        git_dir = os.path.join(directory, repo.name)
        if not os.path.isdir(git_dir):
            gitrepo = git.Repo.init(git_dir)
            origin = gitrepo.create_remote('origin', repo.url)
        else:
            gitrepo = git.Repo(git_dir)
            origin = gitrepo.remotes.origin
        origin.fetch()
        gitrepo.git.reset('--hard', 'origin/master')
        gitrepo.git.clean('-xffd')


ORGANIZATION = 'kodi-game'
FILTER = 'game.libretro.'


def test_clone_single_repo():
    """ Tests cloning a single repo """
    test_dir = os.path.join(
        os.path.dirname(os.path.realpath(__file__)),
        "tests", os.path.splitext(os.path.basename(__file__))[0])
    if os.path.exists(test_dir):  # pragma: no cover
        shutil.rmtree(test_dir)

    gitaccess = Git()
    gitaccess.clone_repo(
        GitRepo('kodi-game-scripting',
                'https://github.com/fetzerch/kodi-game-scripting'), test_dir)
    gitaccess.clone_repos([
        GitRepo('kodi-game-scripting',
                'https://github.com/fetzerch/kodi-game-scripting')], test_dir)


def test_github_repos():
    """ Tests getting a repo list """
    gitaccess = Git()
    repos = gitaccess.get_repos(ORGANIZATION, FILTER)
    print(repos)
    assert len(repos) > 0
