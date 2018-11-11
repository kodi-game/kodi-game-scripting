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

from pkg_resources import parse_version

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

    @staticmethod
    def is_git_repo(path):
        """ Determine if repo is a Git repository """
        try:
            _ = git.Repo(path).git_dir  # noqa
            return True
        except (git.InvalidGitRepositoryError,
                git.NoSuchPathError):
            return False

    def __init__(self, repo, path):
        self._githubrepo = repo
        self._gitrepo = None
        self._path = os.path.join(path, repo.name)

        if not GitRepo.is_git_repo(self._path):
            utils.ensure_directory_exists(self._path)
            print("New repo, creating {}".format(self._githubrepo.name))
            self._gitrepo = git.Repo.init(self._path)
        else:
            print("Existing repo {}".format(self._githubrepo.name))
            self._gitrepo = git.Repo(self._path)
        if self._githubrepo.clone_url:
            try:
                origin = self._gitrepo.remotes.origin
            except AttributeError:
                origin = self._gitrepo.create_remote(
                    'origin', self._githubrepo.clone_url)
            origin.set_url(self._githubrepo.ssh_url, push=True)

    def fetch_and_reset(self, reset=True):
        """ Fetch repo and reset it """
        try:
            origin = self._gitrepo.remotes.origin
            print("Fetching {}".format(self._githubrepo.name))
            origin.fetch('master')
            if (parse_version('.'.join(map(
                    str, self._gitrepo.git.version_info))) >=
                    parse_version('2.17.0')):
                origin.fetch(tags=True, prune=True, prune_tags=True)
            else:
                origin.fetch(tags=True, prune=True)
            if reset:
                print("Resetting {}".format(self._githubrepo.name))
                self._gitrepo.git.reset('--hard', 'origin/master')
            else:
                print("Rebasing {}".format(self._githubrepo.name))
                self._gitrepo.git.rebase('origin/master')
        except AttributeError:
            print("Skipping fetching {}".format(self._githubrepo.name))
        print("Cleaning local changes {}".format(self._githubrepo.name))
        self._gitrepo.git.reset()
        self._gitrepo.git.clean('-xffd')

    def get_hexsha(self):
        """ Get HEAD revision """
        return self._gitrepo.head.object.hexsha

    def commit(self, message, directory=None, force=False, squash=False):
        """ Create commit in repo """
        if directory:
            self._gitrepo.git.add(directory, force=force)
        else:
            self._gitrepo.git.add(all=True, force=force)
        if squash:
            try:
                self._gitrepo.git.reset('origin/master', soft=True)
            except git.GitCommandError:
                self._gitrepo.git.update_ref('-d', 'HEAD')
        if self._gitrepo.is_dirty():
            self._gitrepo.index.commit(message)

    def tag(self, tag, message=None):
        """ Create tag in repo """
        self._gitrepo.create_tag(tag, message, force=True)

    def diff(self):
        """ Diff commits in repo """
        try:
            return self._gitrepo.git.diff("origin/master",
                                          self._gitrepo.head.commit)
        except git.GitCommandError:
            return self._gitrepo.git.show()

    def describe(self):
        """ Describe current version """
        try:
            return self._gitrepo.git.describe('--tags', '--always')
        except git.GitCommandError:
            return ''

    def push(self, branch, tags=False):
        """ Push commit to remote """
        if self._gitrepo.is_dirty():
            raise ValueError("Skipping, repository is dirty")
        self._gitrepo.remotes.origin.push(
            'HEAD:{}'.format(branch),
            force=(branch != 'master'))
        if tags:
            self._gitrepo.git.push('--tags')
