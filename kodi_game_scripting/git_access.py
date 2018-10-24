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

""" Access GitHub API and Git Repos """

import collections
import functools
import os
import re

import git
import github

from . import credentials
from . import utils

GitHubRepo = collections.namedtuple('GitHubRepo', 'name clone_url ssh_url')


class GitHubOrg:
    """ Access GitHub Organization API """
    def __init__(self, org, auth=False):
        """ Initialize GitHub API instance """
        try:
            apitoken = os.environ.get('GITHUB_ACCESS_TOKEN', None)
            if apitoken:
                self._github = github.Github(apitoken)
            else:
                if auth:
                    cred = credentials.Credentials('github')
                    username, password = cred.load()
                else:
                    username, password = None, None
                self._github = github.Github(username, password)
            rate = self._github.get_rate_limit().core
            print("GitHub API Rate: limit: {}, remaining: {}, reset: {}"
                  .format(rate.limit, rate.remaining, rate.reset.isoformat()))
            if auth and not apitoken:
                cred.save(username, password)
            self._org = self._github.get_organization(org)
        except github.BadCredentialsException:
            if auth and not apitoken:
                cred.clean()
            raise ValueError("Authentication to GitHub failed")

    @functools.lru_cache()
    def get_repos(self, regex):
        """ Query all GitHub repos of the given organization that matches
            the given regex. Since API calls are limited, cache results. """
        repos = {
            repo.name: GitHubRepo(repo.name, repo.clone_url, repo.ssh_url)
            for repo in self._org.get_repos() if re.search(regex, repo.name)
        }
        return repos

    def create_repo(self, name):
        """ Create a new repo on GitHub """
        repo = self._org.create_repo(name, auto_init=True)
        self.get_repos.cache_clear()  # pylint: disable=no-member
        return GitHubRepo(repo.name, repo.clone_url, repo.ssh_url)


class GitRepo:
    """ Access to Git repository """
    def __init__(self, repo, path):
        self._repo = repo
        self._path = os.path.join(path, repo.name)

    def is_git_repo(self):
        """ Determine if repo is a Git repository """
        try:
            _ = git.Repo(self._path).git_dir  # noqa
            return True
        except git.exc.InvalidGitRepositoryError:  # pylint: disable=no-member
            return False

    def clone(self, reset=True):
        """ Clone repo into directory

            If the repo exists all changes will be discarded. """
        utils.ensure_directory_exists(self._path)
        if not self.is_git_repo():
            print("New repo, creating {}".format(self._repo.name))
            gitrepo = git.Repo.init(self._path)
            origin = gitrepo.create_remote('origin', self._repo.clone_url)
        else:
            print("Existing repo {}".format(self._repo.name))
            gitrepo = git.Repo(self._path)
            origin = gitrepo.remotes.origin
        origin.set_url(self._repo.ssh_url, push=True)
        print("Fetching {}".format(self._repo.name))
        origin.fetch('master')
        if reset:
            print("Resetting {}".format(self._repo.name))
            gitrepo.git.reset('--hard', 'origin/master')
        else:
            print("Rebasing {}".format(self._repo.name))
            gitrepo.git.rebase('origin/master')
        print("Cleaning local changes {}".format(self._repo.name))
        gitrepo.git.reset()
        gitrepo.git.clean('-xffd')

    def commit(self, message, directory=None, force=False, squash=False):
        """ Create commit in repo """
        gitrepo = git.Repo(self._path)
        if directory:
            gitrepo.git.add(directory, force=force)
        else:
            gitrepo.git.add(all=True, force=force)
        if squash:
            gitrepo.git.reset('origin/master', soft=True)
        if gitrepo.is_dirty():
            gitrepo.index.commit(message)

    def diff(self):
        """ Diff commits in repo """
        gitrepo = git.Repo(self._path)
        return gitrepo.git.diff("origin/master", gitrepo.head.commit)

    def push(self, branch):
        """ Push commit in remote """
        gitrepo = git.Repo(self._path)
        if gitrepo.is_dirty():
            raise ValueError("Skipping, repository is dirty")
        origin = gitrepo.remotes.origin
        origin.push('HEAD:{}'.format(branch),
                    force=False if branch == 'master' else True)
