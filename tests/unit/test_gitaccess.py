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

from unittest import mock

import git
import github
import pytest

from kodi_game_scripting.git_access import GitHubOrg, GitHubRepo, GitRepo
from kodi_game_scripting.git_access import EMPTY_SHA

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
def gitmock(mocker):
    """ Setup mocked git.Repo """
    mocker.patch('kodi_game_scripting.utils.ensure_directory_exists')
    return mocker.patch('git.Repo')


def test_gitrepo_isgitrepo(gitmock):
    """ Test that repo is a Git repo """
    assert GitRepo.is_git_repo('testpath')
    gitmock.assert_called_once_with('testpath')


def test_gitrepo_isnogitrepo(gitmock):
    """ Test that repo is not a Git repo """
    gitmock.side_effect = git.InvalidGitRepositoryError()
    assert not GitRepo.is_git_repo('testpath')
    gitmock.assert_called_once_with('testpath')


GITHUBREPO = GitHubRepo('name', 'clone_url', 'ssh_url')


def test_gitrepo_init(gitmock):
    """ Test initializing a new repository """
    with mock.patch('kodi_game_scripting.git_access.GitRepo.is_git_repo',
                    return_value=False):
        GitRepo(GITHUBREPO, 'tmpdir')
    gitmock.init.assert_called_once_with(
        os.path.join('tmpdir', 'name'))
    gitmock.init.return_value.remotes.origin.set_url.assert_called_once_with(
        'ssh_url', push=True)


def test_gitrepo_initexisting(gitmock):
    """ Test initializing an existing repository """
    with mock.patch('kodi_game_scripting.git_access.GitRepo.is_git_repo',
                    return_value=True):
        GitRepo(GITHUBREPO, 'tmpdir')
    gitmock.assert_called_once_with(
        os.path.join('tmpdir', 'name'))
    gitmock.return_value.remotes.origin.set_url.assert_called_once_with(
        'ssh_url', push=True)


def test_gitrepo_initnocloneurl(gitmock):
    """ Test initializing a new repository without clone url """
    with mock.patch('kodi_game_scripting.git_access.GitRepo.is_git_repo',
                    return_value=False):
        GitRepo(GitHubRepo('empty', '', ''), 'tmpdir')
    gitmock.init.return_value.remotes.origin.set_url.assert_not_called()


def test_gitrepo_initnoorigin(gitmock):
    """ Test initializing a new repository, create new remote """
    del gitmock.init.return_value.remotes.origin
    with mock.patch('kodi_game_scripting.git_access.GitRepo.is_git_repo',
                    return_value=False):
        GitRepo(GITHUBREPO, 'tmpdir')
    gitmock.init.return_value.create_remote.assert_called_once_with(
        'origin', 'clone_url')


@pytest.fixture
def gitrepo(gitmock, mocker):
    """ Setup mocked GitRepo """
    mocker.patch('kodi_game_scripting.git_access.GitRepo.is_git_repo',
                 return_value=True)
    gitrepo = GitRepo(GITHUBREPO, 'tmpdir')
    gitmock.reset_mock()
    return gitrepo


def test_gitrepo_fetchreset(gitrepo, gitmock):
    """ Test fetching & resetting a repository """
    gitmock.return_value.remotes.__contains__.return_value = True
    gitmock.return_value.git.version_info = (2, 17, 0)
    gitrepo.fetch_and_reset()
    gitmock.return_value.remotes.origin.fetch.assert_has_calls([
        mock.call('master'),
        mock.call(tags=True, prune=True, prune_tags=True)
    ])
    gitmock.return_value.git.reset.assert_has_calls([
        mock.call('--hard', 'origin/master'),
        mock.call()
    ])
    gitmock.return_value.git.clean.assert_called_once_with('-xffd')


def test_gitrepo_fetchresetoldgit(gitrepo, gitmock):
    """ Test fetching & resetting a repository (old git) """
    gitmock.return_value.remotes.__contains__.return_value = True
    gitmock.return_value.git.version_info = (2, 16, 0)
    gitmock.return_value.git.tag.return_value = 'tag'
    gitrepo.fetch_and_reset()
    print(gitmock.return_value.mock_calls)
    gitmock.return_value.git.tag.assert_has_calls([
        mock.call(list=True),
        mock.call('--delete', ['tag'])
    ])
    gitmock.return_value.remotes.origin.fetch.assert_has_calls([
        mock.call('master'),
        mock.call(tags=True, prune=True)
    ])
    gitmock.return_value.git.reset.assert_has_calls([
        mock.call('--hard', 'origin/master'),
        mock.call()
    ])
    gitmock.return_value.git.clean.assert_called_once_with('-xffd')


def test_gitrepo_fetchresetoldgitnotag(gitrepo, gitmock):
    """ Test fetching & resetting a repository (old git, no tags) """
    gitmock.return_value.remotes.__contains__.return_value = True
    gitmock.return_value.git.version_info = (2, 16, 0)
    gitmock.return_value.git.tag.return_value = ''
    gitrepo.fetch_and_reset()
    print(gitmock.return_value.mock_calls)
    gitmock.return_value.git.tag.assert_has_calls([
        mock.call(list=True),
    ])
    gitmock.return_value.remotes.origin.fetch.assert_has_calls([
        mock.call('master'),
        mock.call(tags=True, prune=True)
    ])
    gitmock.return_value.git.reset.assert_has_calls([
        mock.call('--hard', 'origin/master'),
        mock.call()
    ])
    gitmock.return_value.git.clean.assert_called_once_with('-xffd')


def test_gitrepo_fetchresetlocal(gitrepo, gitmock):
    """ Test resetting a repository that has no remote """
    gitmock.return_value.remotes.__contains__.return_value = False
    gitrepo.fetch_and_reset()
    gitmock.return_value.git.reset.assert_called_once_with()
    gitmock.return_value.git.clean.assert_called_once_with('-xffd')


def test_gitrepo_fetchrebase(gitrepo, gitmock):
    """ Test fetching and rebasing a repo """
    gitmock.return_value.remotes.__contains__.return_value = True
    gitmock.return_value.git.version_info = (2, 17, 0)
    gitrepo.fetch_and_reset(reset=False)
    gitmock.return_value.remotes.origin.fetch.assert_has_calls([
        mock.call('master'),
        mock.call(tags=True, prune=True, prune_tags=True)
    ])
    gitmock.return_value.git.reset.assert_has_calls([
        mock.call()
    ])
    gitmock.return_value.git.rebase.assert_called_once_with('origin/master')
    gitmock.return_value.git.clean.assert_called_once_with('-xffd')


def test_gitrepo_gethexsha(gitrepo, gitmock):
    """ Test getting the hexsha """
    gitmock.return_value.head.is_valid.return_value = True
    gitmock.return_value.head.object.hexsha = '1234567'
    assert gitrepo.get_hexsha() == '1234567'


def test_gitrepo_gethexshanohead(gitrepo, gitmock):
    """ Test getting the hexsha when there is no HEAD """
    gitmock.return_value.head.is_valid.return_value = False
    assert gitrepo.get_hexsha() == ''


def test_gitrepo_commit(gitrepo, gitmock):
    """ Test commit """
    gitmock.return_value.is_dirty.return_value = True
    gitrepo.commit('msg')
    gitmock.return_value.git.add.assert_called_once_with(all=True, force=False)
    gitmock.return_value.index.commit.assert_called_once_with('msg')


def test_gitrepo_commitpath(gitrepo, gitmock):
    """ Test commit only a specific directory """
    gitmock.return_value.is_dirty.return_value = True
    gitrepo.commit('msg', directory='dir')
    gitmock.return_value.git.add.assert_called_once_with('dir', force=False)
    gitmock.return_value.index.commit.assert_called_once_with('msg')


def test_gitrepo_commitforce(gitrepo, gitmock):
    """ Test force commit """
    gitmock.return_value.is_dirty.return_value = True
    gitrepo.commit('msg', force=True)
    gitmock.return_value.git.add.assert_called_once_with(all=True, force=True)
    gitmock.return_value.index.commit.assert_called_once_with('msg')


def test_gitrepo_commitsquash(gitrepo, gitmock):
    """ Test commit and squash """
    gitmock.return_value.remotes.__contains__.return_value = True
    gitmock.return_value.is_dirty.return_value = True
    gitrepo.commit('msg', squash=True)
    gitmock.return_value.git.reset.assert_called_once_with(
        'origin/master', soft=True)
    gitmock.return_value.index.commit.assert_called_once_with('msg')


def test_gitrepo_commitsquashlocal(gitrepo, gitmock):
    """ Test commit and squash """
    gitmock.return_value.remotes.__contains__.return_value = False
    gitmock.return_value.is_dirty.return_value = True
    gitmock.return_value.git.reset.side_effect = git.GitCommandError([''], '')
    gitrepo.commit('msg', squash=True)
    gitmock.return_value.git.update_ref.assert_called_once_with('-d', 'HEAD')
    gitmock.return_value.index.commit.assert_called_once_with('msg')


def test_gitrepo_commitskip(gitrepo, gitmock):
    """ Test nothing to commit """
    gitmock.return_value.is_dirty.return_value = False
    gitrepo.commit('msg')
    gitmock.return_value.index.commit.assert_not_called()


def test_gitrepo_tag(gitrepo, gitmock):
    """ Test creating a tag """
    gitmock.return_value.head.is_valid.return_value = True
    gitrepo.tag('1.0.0', 'message')
    gitmock.return_value.create_tag.assert_called_once_with(
        '1.0.0', 'message', force=True)


def test_gitrepo_tagnohead(gitrepo, gitmock):
    """ Test creating a tag """
    gitmock.return_value.head.is_valid.return_value = False
    gitrepo.tag('1.0.0', 'message')
    gitmock.return_value.create_tag.assert_not_called()


def test_gitrepo_diff(gitrepo, gitmock):
    """ Test Git diff """
    gitmock.return_value.head.is_valid.return_value = True
    gitmock.return_value.remotes.__contains__.return_value = True
    assert gitrepo.diff()
    gitmock.return_value.git.diff.assert_called_once_with(
        'origin/master', gitmock.return_value.head.commit)


def test_gitrepo_diffnoorigin(gitrepo, gitmock):
    """ Test Git diff without origin """
    gitmock.return_value.head.is_valid.return_value = True
    gitmock.return_value.remotes.__contains__.return_value = False
    assert gitrepo.diff()
    gitmock.return_value.git.diff.assert_called_once_with(
        EMPTY_SHA, gitmock.return_value.head.commit)


def test_gitrepo_diffnohead(gitrepo, gitmock):
    """ Test Git diff without HEAD """
    gitmock.return_value.head.is_valid.return_value = False
    gitmock.return_value.remotes.__contains__.return_value = False
    assert not gitrepo.diff()
    gitmock.return_value.git.diff.assert_not_called()


def test_gitrepo_describe(gitrepo, gitmock):
    """ Test describing current version """
    gitmock.return_value.head.is_valid.return_value = True
    assert gitrepo.describe()
    gitmock.return_value.git.describe.assert_called_once_with(
        '--tags', '--always')


def test_gitrepo_describenohead(gitrepo, gitmock):
    """ Test describing current version """
    gitmock.return_value.head.is_valid.return_value = False
    assert not gitrepo.describe()
    gitmock.return_value.git.describe.assert_not_called()


def test_gitrepo_push(gitrepo, gitmock):
    """ Test push change """
    gitmock.return_value.is_dirty.return_value = False
    gitrepo.push('branch')
    gitmock.return_value.remotes.origin.push.assert_called_once_with(
        'HEAD:branch', force=True)


def test_gitrepo_pushdirty(gitrepo, gitmock):
    """ Test nothing to push """
    gitmock.return_value.is_dirty.return_value = True
    with pytest.raises(ValueError):
        gitrepo.push('branch')


def test_gitrepo_pushtags(gitrepo, gitmock):
    """ Test push tags """
    gitmock.return_value.is_dirty.return_value = False
    gitrepo.push('branch', tags=True)
    gitmock.return_value.git.push.assert_called_once_with('--tags')
