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
import functools
import os
import re

import git
import github

from . import credentials
from . import utils

GitRepo = collections.namedtuple('GitRepo', 'name url')


class Git:
    """ Access GitHub API and Git Repos """
    def __init__(self, auth=False):
        """ Initialize Git instance """
        try:
            if auth:
                cred = credentials.Credentials('github')
                username, password = cred.load()
            else:
                username, password = None, None
            self._github = github.Github(username, password)
            rate = self._github.get_rate_limit().rate
            print("GitHub API Rate: limit: {}, remaining: {}, reset: {}"
                  .format(rate.limit, rate.remaining, rate.reset.isoformat()))
            if auth:
                cred.save(username, password)
        except github.BadCredentialsException:
            if auth:
                cred.clean()
            raise ValueError("Authentication to GitHub failed")

    @functools.lru_cache()
    def get_repos(self, organization, repo_filter):
        """ Query all GitHub repos of the given organization that matches
            the given filter. Since API calls are limited, cache results. """
        repos = {
            repo.name: GitRepo(repo.name, repo.clone_url)
            for repo in self._github.get_organization(organization).get_repos()
            if re.search(repo_filter, repo.name)
        }
        return repos

    def clone_repos(self, repos, directory):
        """ Clone list of repos into directory

            If the repos exist all changes will be discarded. """
        for repo in repos:
            self.clone_repo(repo, directory)

    @classmethod
    def is_git_repo(cls, path):
        """ Determine if a path is a Git repository """
        try:
            _ = git.Repo(path).git_dir  # flake8: noqa
            return True
        except git.exc.InvalidGitRepositoryError:
            return False

    @classmethod
    def clone_repo(cls, repo, path):
        """ Clone repo into directory

            If the repo exists all changes will be discarded. """
        git_dir = os.path.join(path, repo.name)
        utils.ensure_directory_exists(git_dir)
        if not cls.is_git_repo(git_dir):
            print("New repo, creating {}".format(repo.name))
            gitrepo = git.Repo.init(git_dir)
            origin = gitrepo.create_remote('origin', repo.url)
        else:
            print("Existing repo, updating {}".format(repo.name))
            gitrepo = git.Repo(git_dir)
            origin = gitrepo.remotes.origin
        print("Fetching {}".format(repo.name))
        origin.fetch()
        print("Resetting {}".format(repo.name))
        gitrepo.git.reset('--hard', 'origin/master')
        gitrepo.git.clean('-xffd')

    @classmethod
    def commit_repo(cls, repo, path, message):
        """ Create commit in repo """
        git_dir = os.path.join(path, repo.name)
        gitrepo = git.Repo(git_dir)
        gitrepo.git.add(all=True)
        gitrepo.index.commit(message)


def test_clone_single_repo():
    """ Tests cloning a single repo """
    test_dir = os.path.join(
        os.path.dirname(os.path.realpath(__file__)),
        "tests", os.path.splitext(os.path.basename(__file__))[0])
    utils.ensure_directory_exists(test_dir, clean=True)

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
    repos = gitaccess.get_repos('kodi-game', r'game\.libretro\.')
    print(repos)
    assert len(repos) > 0
