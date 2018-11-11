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

""" Test KodiGameAddon """

import os

from unittest import mock

import pytest

from kodi_game_scripting.process_game_addons import KodiGameAddon
from kodi_game_scripting.git_access import GitHubRepo

pytestmark = [pytest.mark.unit]


# pylint: disable=redefined-outer-name

@pytest.fixture(autouse=True)
def configmock(mocker):
    """ Setup mocked config object """
    return mocker.patch.dict(
        'kodi_game_scripting.config.ADDONS', {
            'mygame': (
                'mygame-repo', 'mygame-makefile', 'mygame-makefile-dir',
                'mygame-makefile-jni-dir', {}
            )
        }
    )


@pytest.fixture(autouse=True)
def gitrepomock(mocker):
    """ Setup mocked GitRepo """
    return mocker.patch('kodi_game_scripting.process_game_addons.GitRepo',
                        autospec=True)


@pytest.fixture(autouse=True)
def libretrowrappermock(mocker):
    """ Setup mocked LibretroWrapper """
    return mocker.patch('kodi_game_scripting.libretro_ctypes.LibretroWrapper',
                        autospec=True)


@pytest.fixture(autouse=True)
def templateprocessormock(mocker):
    """ Setup mocked TemplateProcessor """
    return mocker.patch('kodi_game_scripting.template_processor'
                        '.TemplateProcessor', autospec=True)


GITHUBREPO = GitHubRepo('name', 'clone_url', 'ssh_url')


@pytest.fixture
def kodigameaddon():
    """ Initialize a KodiGameAddon """
    return KodiGameAddon('game.mygame', 'mygame', GITHUBREPO, 'tmpdir',
                         'master')


def test_kodigameaddon_init(kodigameaddon, gitrepomock):
    """ Test initializing KodiGameAddon """
    assert kodigameaddon.name == 'game.mygame'
    assert kodigameaddon.game_name == 'mygame'
    gitrepomock.assert_called_once_with(GITHUBREPO, 'tmpdir')


def test_kodigameaddon_processdescription(kodigameaddon,
                                          templateprocessormock):
    """ Test processing addon description """
    kodigameaddon.process_description_files('kodidir')
    templateprocessormock.process.assert_called_once_with(
        'description',
        os.path.join('kodidir', 'cmake', 'addons', 'addons', 'game.mygame'),
        mock.ANY)


def test_kodigameaddon_processaddon(kodigameaddon, templateprocessormock):
    """ Test processing addon files """
    kodigameaddon.process_addon_files()
    templateprocessormock.process.assert_called_once_with(
        'addon', os.path.join('tmpdir', 'game.mygame'), mock.ANY)


def test_kodigameaddon_loadlibraryfile(kodigameaddon, libretrowrappermock):
    """ Test loading info from compiled library """
    libretrowrappermock.return_value.system_info = 'system_info'
    var1 = mock.Mock()
    var1.id = 1
    var2 = mock.Mock()
    var2.id = 2
    libretrowrappermock.return_value.variables = [var2, var1]
    libretrowrappermock.return_value.opengl_linkage = False
    kodigameaddon.load_library_file()
    assert kodigameaddon.info['library']['loaded']
    assert not kodigameaddon.info['library']['opengl']
    assert kodigameaddon.info['settings'] == [var1, var2]
    assert kodigameaddon.info['system_info'] == 'system_info'


def test_kodigameaddon_loadlibraryfileerr(kodigameaddon, libretrowrappermock):
    """ Test failure loading info from compiled library """
    libretrowrappermock.side_effect = OSError()
    kodigameaddon.load_library_file()
    assert not kodigameaddon.info['library']['loaded']
    assert kodigameaddon.info['library']['error']


def test_kodigameaddon_loadinfofile(kodigameaddon, mocker):
    """ Test loading info files from libretro-super """
    isfilemock = mocker.patch('os.path.isfile', return_value=True)
    mocker.patch('builtins.open', mock.mock_open(read_data='#comment\na=1'))
    kodigameaddon.load_info_file()
    assert kodigameaddon.info['libretro_info']['a'] == '1'
    assert isfilemock.mock_calls


def test_kodigameaddon_loadinfofilenofile(kodigameaddon, mocker):
    """ Test failure loading info files from libretro-super """
    isfilemock = mocker.patch('os.path.isfile', return_value=False)
    kodigameaddon.load_info_file()
    assert not kodigameaddon.info['libretro_info']
    assert isfilemock.mock_calls


def test_kodigameaddon_loadassets(kodigameaddon, mocker):
    """ Test loading asset files """
    mocker.patch('kodi_game_scripting.utils.list_all_files', return_value=[
        'noimage.txt', 'unknownimage.png',
        os.path.join('game.mygame', 'resources', 'icon.png'),
        os.path.join('game.mygame', 'resources', 'fanart.jpg'),
        os.path.join('game.mygame', 'resources', 'screenshot1.jpg'),
        os.path.join('game.mygame', 'resources', 'screenshot2.jpg'),
    ])
    kodigameaddon.load_assets()
    assert kodigameaddon.info['assets'] == {
        'icon': 'resources/icon.png',
        'fanart': 'resources/fanart.jpg',
        'screenshots': [
            'resources/screenshot1.jpg',
            'resources/screenshot2.jpg',
        ],
    }


def test_kodigameaddon_gitrevision(kodigameaddon, gitrepomock):
    """ Test loading git revision """
    gitrepomock.is_git_repo.return_value = True
    gitrepomock.return_value.get_hexsha.return_value = '1234567'
    kodigameaddon.load_git_revision()
    assert kodigameaddon.info['libretro_repo']['hexsha'] == '1234567'


def test_kodigameaddon_gitrevisionnorepo(kodigameaddon, gitrepomock):
    """ Test loading git revision when not a Git repository """
    gitrepomock.is_git_repo.return_value = False
    assert not kodigameaddon.info['libretro_repo']['hexsha']


def test_kodigameaddon_loadgameversion(kodigameaddon, gitrepomock):
    """ Test loading game version """
    kodigameaddon.info['system_info']['version'] = '1.2.3'
    gitrepomock.return_value.describe.return_value = '1.2.3.4-2-g1234567'
    kodigameaddon.load_game_version()
    assert kodigameaddon.info['game']['version'] == '1.2.3.4'


def test_kodigameaddon_loadgameversioninitial(kodigameaddon, gitrepomock):
    """ Test loading initial game version """
    kodigameaddon.info['system_info']['version'] = '1.2.3'
    gitrepomock.return_value.describe.return_value = 'g1234567'
    kodigameaddon.load_game_version()
    assert kodigameaddon.info['game']['version'] == '1.2.3.-1'


def test_kodigameaddon_bumpversion(kodigameaddon):
    """ Test bumping game version """
    kodigameaddon.info['game']['version'] = '1.2.3.-1'
    kodigameaddon.bump_version()
    assert kodigameaddon.info['game']['version'] == '1.2.3.0'


def test_kodigameaddon_fetchreset(kodigameaddon, gitrepomock):
    """ Test fetching and resetting from Git """
    kodigameaddon.fetch_and_reset(reset=True)
    gitrepomock.return_value.fetch_and_reset.assert_called_once_with(
        reset=True)


def test_kodigameaddon_commit(kodigameaddon, gitrepomock):
    """ Test committing changes to Git """
    kodigameaddon.commit(squash=True)
    gitrepomock.return_value.commit.assert_called_once_with(
        mock.ANY, squash=True)


def test_kodigameaddon_tag(kodigameaddon, gitrepomock):
    """ Test tagging a release in Git """
    kodigameaddon.info['game']['version'] = '1.2.3.4'
    kodigameaddon.tag()
    assert gitrepomock.return_value.tag.call_args[0][0].startswith('1.2.3.4-')


def test_kodigameaddon_push(kodigameaddon, gitrepomock):
    """ Test pushing changes (master branch) """
    kodigameaddon.push()
    gitrepomock.return_value.push.assert_called_once_with('master', tags=True)


def test_kodigameaddon_pushbranch(kodigameaddon, gitrepomock):
    """ Test pushing changes (other branch) """
    kodigameaddon.info['game']['branch'] = 'testbranch'
    kodigameaddon.push()
    gitrepomock.return_value.push.assert_called_once_with(
        'testbranch', tags=False)
