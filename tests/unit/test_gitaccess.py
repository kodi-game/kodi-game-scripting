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

""" Test Git and GitHub access """

import os

import git
import github
import pytest

from kodi_game_scripting.git_access import GitHubOrg, GitHubRepo, GitRepo

pytestmark = [pytest.mark.unit]


# pylint: disable=redefined-outer-name

@pytest.fixture
def githuborg_fixture(mocker):
    """ Setup mocks for GitHub tests """
    githuborg_mock = mocker.patch('github.Github')
    cred_mock = mocker.patch('kodi_game_scripting.credentials.Credentials')
    env_mock = mocker.patch('os.environ.get')
    env_mock.return_value = None
    return githuborg_mock, cred_mock, env_mock


def test_githuborg_init(githuborg_fixture):
    """ Test initializing GitHub API without authentication """
    githuborg_mock, _, _ = githuborg_fixture
    GitHubOrg('org')
    githuborg_mock.assert_called_once_with(None, None)


def test_githuborg_initauth(githuborg_fixture):
    """ Test initializing GitHub API with authentication """
    githuborg_mock, cred_mock, _ = githuborg_fixture
    cred_mock.return_value.load.return_value = ('user', 'pass')
    GitHubOrg('org', auth=True)
    cred_mock.assert_called_once_with('github')
    cred_mock.return_value.load.assert_called_once_with()
    githuborg_mock.assert_called_once_with('user', 'pass')
    cred_mock.return_value.save.assert_called_once_with('user', 'pass')


def test_githuborg_initenv(githuborg_fixture):
    """ Test initializing GitHub API with environment token """
    githuborg_mock, _, env_mock = githuborg_fixture
    env_mock.return_value = 'token'
    GitHubOrg('org', auth=False)
    githuborg_mock.assert_called_once_with('token')


def test_githuborg_initenvauth(githuborg_fixture):
    """ Test initializing GitHub API with environment token """
    githuborg_mock, _, env_mock = githuborg_fixture
    env_mock.return_value = 'token'
    GitHubOrg('org', auth=True)
    githuborg_mock.assert_called_once_with('token')


def test_githuborg_initerror(githuborg_fixture):
    """ Test initializing GitHub API failed """
    githuborg_mock, _, _ = githuborg_fixture
    githuborg_mock.side_effect = github.BadCredentialsException('', '')
    with pytest.raises(ValueError):
        GitHubOrg('org', auth=False)


def test_githuborg_initautherror(githuborg_fixture):
    """ Test initializing GitHub API with failed authentication """
    githuborg_mock, cred_mock, _ = githuborg_fixture
    cred_mock.return_value.load.return_value = ('user', 'pass')
    githuborg_mock.side_effect = github.BadCredentialsException('', '')
    with pytest.raises(ValueError):
        GitHubOrg('org', auth=True)
    cred_mock.assert_called_once_with('github')
    cred_mock.return_value.load.assert_called_once_with()
    cred_mock.return_value.clean.assert_called_once_with()


def test_githuborg_getrepos(githuborg_fixture):
    """ Test getting GitHub repos """
    githuborg_mock, _, _ = githuborg_fixture
    githubrepo1 = GitHubRepo('repo1', 'clone_url1', 'ssh_url1')
    githubrepo2 = GitHubRepo('repo2', 'clone_url2', 'ssh_url2')
    githuborg_mock.return_value.get_organization.return_value \
        .get_repos.return_value = [githubrepo1, githubrepo2]
    githuborg = GitHubOrg('org')
    repos = githuborg.get_repos(r'repo1')
    assert repos == {'repo1': githubrepo1}


def test_githuborg_createrepo(githuborg_fixture):
    """ Test creating a repo on GitHub """
    githuborg_mock, _, _ = githuborg_fixture
    githubrepo = GitHubRepo('repo', 'clone_url', 'ssh_url')
    githuborg_mock.return_value.get_organization.return_value \
        .create_repo.return_value = githubrepo
    githuborg = GitHubOrg('org')
    repo = githuborg.create_repo('repo')
    assert repo == githubrepo


@pytest.fixture
def gitrepo(mocker, tmpdir):
    """ Setup mocked GitRepo """
    gitmock = mocker.patch('git.Repo')
    repo = GitRepo(GitHubRepo('name', 'clone_url', 'ssh_url'), str(tmpdir))
    repo.gitmock = gitmock
    repo.tmpdir = tmpdir
    return repo


def test_gitrepo_isgitrepo(gitrepo):
    """ Test that repo is a Git repo """
    assert gitrepo.is_git_repo()


def test_gitrepo_isnogitrepo(gitrepo):
    """ Test that repo is not a Git repo """
    gitrepo.gitmock.side_effect = \
        git.exc.InvalidGitRepositoryError()  # pylint: disable=no-member
    assert not gitrepo.is_git_repo()


def test_gitrepo_clone(gitrepo):
    """ Test cloning a repository """
    gitrepo.clone()
    gitrepo.gitmock.return_value.remotes.origin.fetch.assert_called_once_with(
        'master')
    gitrepo.gitmock.return_value.git.reset.assert_any_call(
        '--hard', 'origin/master')
    gitrepo.gitmock.return_value.git.reset.assert_any_call()
    gitrepo.gitmock.return_value.git.clean.assert_called_once_with('-xffd')


def test_gitrepo_cloneinit(gitrepo):
    """ Test init a new repository """
    gitrepo.gitmock.side_effect = \
        git.exc.InvalidGitRepositoryError()  # pylint: disable=no-member
    gitrepo.clone()
    gitrepo.gitmock.init.assert_called_once_with(
        os.path.join(str(gitrepo.tmpdir), 'name'))
    gitrepo.gitmock.init.return_value.create_remote.return_value \
        .fetch.assert_called_once_with('master')
    gitrepo.gitmock.init.return_value.git.reset.assert_any_call(
        '--hard', 'origin/master')
    gitrepo.gitmock.init.return_value.git.reset.assert_any_call()
    gitrepo.gitmock.init.return_value.git.clean.assert_called_once_with(
        '-xffd')


def test_gitrepo_clonenoreset(gitrepo):
    """ Test clone a repo, don't reset """
    gitrepo.clone(reset=False)
    gitrepo.gitmock.return_value.remotes.origin.fetch.assert_called_once_with(
        'master')
    gitrepo.gitmock.return_value.git.rebase.assert_any_call('origin/master')
    gitrepo.gitmock.return_value.git.reset.assert_any_call()
    gitrepo.gitmock.return_value.git.clean.assert_called_once_with('-xffd')


def test_gitrepo_commit(gitrepo):
    """ Test commit """
    gitrepo.gitmock.return_value.is_dirty.return_value = True
    gitrepo.commit('msg')
    gitrepo.gitmock.return_value.git.add.assert_called_once_with(
        all=True, force=False)
    gitrepo.gitmock.return_value.index.commit.assert_called_once_with('msg')


def test_gitrepo_commitpath(gitrepo):
    """ Test commit only a specific directory """
    gitrepo.gitmock.return_value.is_dirty.return_value = True
    gitrepo.commit('msg', directory='dir')
    gitrepo.gitmock.return_value.git.add.assert_called_once_with(
        'dir', force=False)
    gitrepo.gitmock.return_value.index.commit.assert_called_once_with('msg')


def test_gitrepo_commitforce(gitrepo):
    """ Test force commit """
    gitrepo.gitmock.return_value.is_dirty.return_value = True
    gitrepo.commit('msg', force=True)
    gitrepo.gitmock.return_value.git.add.assert_called_once_with(
        all=True, force=True)
    gitrepo.gitmock.return_value.index.commit.assert_called_once_with('msg')


def test_gitrepo_commitsquash(gitrepo):
    """ Test commit and squash """
    gitrepo.gitmock.return_value.is_dirty.return_value = True
    gitrepo.commit('msg', squash=True)
    gitrepo.gitmock.return_value.git.reset.assert_called_once_with(
        'origin/master', soft=True)
    gitrepo.gitmock.return_value.index.commit.assert_called_once_with('msg')


def test_gitrepo_commitskip(gitrepo):
    """ Test nothing to commit """
    gitrepo.gitmock.return_value.is_dirty.return_value = False
    gitrepo.commit('msg')
    gitrepo.gitmock.return_value.index.commit.assert_not_called()


def test_gitrepo_diff(gitrepo):
    """ Test Git diff """
    gitrepo.diff()
    gitrepo.gitmock.return_value.git.diff.assert_called_once_with(
        'origin/master', gitrepo.gitmock.return_value.head.commit)


def test_gitrepo_push(gitrepo):
    """ Test push change """
    gitrepo.gitmock.return_value.is_dirty.return_value = False
    gitrepo.push('branch')
    gitrepo.gitmock.return_value.remotes.origin.push.assert_called_once_with(
        'HEAD:branch', force=True)


def test_gitrepo_pushdirty(gitrepo):
    """ Test nothing to push """
    gitrepo.gitmock.return_value.is_dirty.return_value = True
    with pytest.raises(ValueError):
        gitrepo.push('branch')
