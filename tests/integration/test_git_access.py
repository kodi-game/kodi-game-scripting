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

import pytest

from kodi_game_scripting import config
from kodi_game_scripting import utils
from kodi_game_scripting.git_access import GitHubOrg, GitHubRepo, GitRepo

pytestmark = [pytest.mark.integration]


# pylint: disable=redefined-outer-name

def test_githuborg_getrepos():
    """ Tests getting a repo list """
    github = GitHubOrg(config.GITHUB_ORGANIZATION)
    repos = github.get_repos(config.GITHUB_ADDON_PREFIX)
    assert repos


def create_file(path, content=''):
    """ Create a file """
    utils.ensure_directory_exists(os.path.dirname(path))
    with open(path, 'w') as tmpfile:
        tmpfile.write(content)


def test_gitrepo_isgitrepo(tmpdir):
    """ Test if a directory is a git repository """
    assert not GitRepo.is_git_repo(os.path.join(str(tmpdir), 'local-repo'))
    GitRepo(GitHubRepo('local-repo', '', ''), str(tmpdir))
    assert GitRepo.is_git_repo(os.path.join(str(tmpdir), 'local-repo'))


@pytest.fixture
def gitrepo_remote(tmpdir):
    """ Setup a git repository serving as remote repository for other tests """
    gitrepo = GitRepo(GitHubRepo('remote-repo', '', ''), str(tmpdir))
    create_file(os.path.join(gitrepo.path, 'upstream-file'))
    gitrepo.commit('Commit upstream-file')
    # Allow pushing into a non-bare repository.
    with open(os.path.join(gitrepo.path, '.git', 'config'), 'a') as gitconfig:
        gitconfig.write('[receive]\ndenyCurrentBranch=updateInstead\n')
    return gitrepo


def test_gitrepo_remote(tmpdir, gitrepo_remote):
    """ Test operations on a git repository with a remote """
    url = 'file://{}'.format(gitrepo_remote.path)
    gitrepo = GitRepo(GitHubRepo('local-repo', url, url), str(tmpdir))
    gitrepo.fetch_and_reset()
    assert not gitrepo.diff()
    assert gitrepo.describe()
    assert gitrepo.get_hexsha()
    testfile = os.path.join(str(tmpdir), 'local-repo', 'testfile')
    create_file(testfile)
    gitrepo.commit('Commit testfile')
    assert gitrepo.diff()


def test_gitrepo_remote_rebase(tmpdir, gitrepo_remote):
    """ Test rebasing changes instead of resetting """
    url = 'file://{}'.format(gitrepo_remote.path)
    gitrepo = GitRepo(GitHubRepo('local-repo', url, url), str(tmpdir))
    testfile = os.path.join(gitrepo.path, 'testfile')
    gitrepo.fetch_and_reset()
    create_file(testfile)
    gitrepo.commit('Commit testfile')
    assert gitrepo.diff()
    gitrepo.fetch_and_reset(reset=False)
    assert gitrepo.diff()
    assert os.path.isfile(testfile)
    gitrepo.fetch_and_reset(reset=True)
    assert not gitrepo.diff()
    assert not os.path.isfile(testfile)


def test_gitrepo_remote_commitsquash(tmpdir, gitrepo_remote):
    """ Test squash commiting """
    url = 'file://{}'.format(gitrepo_remote.path)
    gitrepo = GitRepo(GitHubRepo('local-repo', url, url), str(tmpdir))
    testfile = os.path.join(gitrepo.path, 'testfile')
    gitrepo.fetch_and_reset()
    create_file(testfile)
    gitrepo.commit('Commit testfile', squash=True)
    create_file(testfile, 'modified content')
    gitrepo.commit('Commit modified testfile', squash=True)
    assert '/dev/null\n+++ b/{}\n'.format(
        os.path.basename(testfile)) in gitrepo.diff()


def test_gitrepo_remote_tag(tmpdir, gitrepo_remote):
    """ Test tags in git repository """
    url = 'file://{}'.format(gitrepo_remote.path)
    gitrepo = GitRepo(GitHubRepo('local-repo', url, url), str(tmpdir))
    gitrepo.fetch_and_reset()
    assert 'remote-tag' not in gitrepo.describe()
    gitrepo_remote.tag('remote-tag')
    gitrepo.fetch_and_reset()
    assert 'remote-tag' in gitrepo.describe()
    gitrepo.tag('local-tag')
    gitrepo.fetch_and_reset()
    assert 'local-tag' not in gitrepo.describe()


def test_gitrepo_remote_push(tmpdir, gitrepo_remote):
    """ Tests pushing changes to remote repository """
    url = 'file://{}'.format(gitrepo_remote.path)
    gitrepo = GitRepo(GitHubRepo('local-repo', url, url), str(tmpdir))
    testfile = os.path.join(gitrepo.path, 'testfile')
    gitrepo.fetch_and_reset()
    create_file(testfile)
    gitrepo.commit('Commit testfile')
    gitrepo.push('master')
    gitrepo.tag('tag')
    gitrepo.push('master', True)
    gitrepo.push('somebranch', True)
    create_file(testfile, 'modified content')
    with pytest.raises(ValueError):
        gitrepo.push('master')


def test_gitrepo_local(tmpdir):
    """ Test operations on a local git repository """
    gitrepo = GitRepo(GitHubRepo('local-repo', '', ''), str(tmpdir))
    testfile = os.path.join(gitrepo.path, 'testfile')
    gitrepo.fetch_and_reset()
    create_file(testfile)
    gitrepo.commit('Commit testfile')
    gitrepo.tag('tag')
    assert gitrepo.diff()
    assert gitrepo.describe()
    assert gitrepo.get_hexsha()
    gitrepo.fetch_and_reset()
    assert os.path.isfile(testfile)


def test_gitrepo_local_nohead(tmpdir):
    """ Test operations on an empty git repository (commit/tag noop) """
    gitrepo = GitRepo(GitHubRepo('local-repo', '', ''), str(tmpdir))
    gitrepo.fetch_and_reset()
    gitrepo.describe()
    gitrepo.commit('Try to commit without changes')
    gitrepo.tag('tag')
    assert not gitrepo.diff()
    assert not gitrepo.describe()
    assert not gitrepo.get_hexsha()


def test_gitrepo_local_existing(tmpdir):
    """ Test initializing an existing repository """
    gitrepo = GitRepo(GitHubRepo('local-repo', '', ''), str(tmpdir))
    gitrepo.fetch_and_reset()
    gitrepo = GitRepo(GitHubRepo('local-repo', '', ''), str(tmpdir))
    gitrepo.fetch_and_reset()


def test_gitrepo_local_commitdirectory(tmpdir):
    """ Test commiting limited to a directory """
    gitrepo = GitRepo(GitHubRepo('local-repo', '', ''), str(tmpdir))
    testfile = os.path.join(gitrepo.path, 'add', 'testfile')
    testfile_ignored = os.path.join(gitrepo.path, 'ignored')
    create_file(testfile)
    create_file(testfile_ignored)
    gitrepo.commit('Commit directory `add`', directory='add')
    gitrepo.fetch_and_reset()
    assert os.path.isfile(testfile)
    assert not os.path.isfile(testfile_ignored)


def test_gitrepo_local_commitforce(tmpdir):
    """ Test force committing to a git repository """
    gitrepo = GitRepo(GitHubRepo('local-repo', '', ''), str(tmpdir))
    gitignore = os.path.join(gitrepo.path, '.gitignore')
    testfile = os.path.join(gitrepo.path, 'testfile')
    create_file(gitignore, os.path.basename(testfile))
    gitrepo.commit('Commit gitignore')
    create_file(testfile)
    gitrepo.commit('Try to commit ignored file')
    gitrepo.fetch_and_reset()
    assert not os.path.isfile(testfile)
    create_file(testfile)
    gitrepo.commit('Force commit ignored file', force=True)
    gitrepo.fetch_and_reset()
    assert os.path.isfile(testfile)


def test_gitrepo_local_commitsquash(tmpdir):
    """ Test squash commiting to a git repository """
    gitrepo = GitRepo(GitHubRepo('local-repo', '', ''), str(tmpdir))
    testfile = os.path.join(gitrepo.path, 'testfile')
    create_file(testfile)
    gitrepo.commit('Commit testfile', squash=True)
    create_file(testfile, 'modified content')
    gitrepo.commit('Commit modified testfile', squash=True)
    assert '/dev/null\n+++ b/{}\n'.format(
        os.path.basename(testfile)) in gitrepo.diff()
