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

from kodi_game_scripting import config
from kodi_game_scripting.process_game_addons import \
    KodiAddonDescriptions, KodiGameAddon
from kodi_game_scripting.git_access import GitHubRepo
from kodi_game_scripting.libretro_ctypes import LibretroWrapper

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
def githuborgmock(mocker):
    """ Setup mocked GitHubOrg """
    return mocker.patch('kodi_game_scripting.process_game_addons.GitHubOrg',
                        autospec=True)


@pytest.fixture(autouse=True)
def gitrepomock(mocker):
    """ Setup mocked GitRepo """
    return mocker.patch('kodi_game_scripting.process_game_addons.GitRepo',
                        autospec=True)


@pytest.fixture(autouse=True)
def libretrowrappermock(mocker):
    """ Setup mocked LibretroWrapper """
    return mocker.patch('kodi_game_scripting.process_game_addons'
                        '.LibretroWrapper', autospec=True)


@pytest.fixture(autouse=True)
def templateprocessormock(mocker):
    """ Setup mocked TemplateProcessor """
    return mocker.patch('kodi_game_scripting.process_game_addons'
                        '.TemplateProcessor', autospec=True)


GITHUBREPO = GitHubRepo('name', 'clone_url', 'ssh_url')


def test_kodiaddondescriptions_clean(mocker):
    """ Test cleaning addon descriptions """
    game1 = '{}game1'.format(config.GITHUB_ADDON_PREFIX)
    game2 = '{}game2'.format(config.GITHUB_ADDON_PREFIX)
    kodi_directory = os.path.join('path', 'repo')
    mocker.patch('os.walk', return_value=iter([
        ('dir', (game1, game2, 'other'), ('file1', 'file2')),
    ]), autospec=True)
    rmmock = mocker.patch('shutil.rmtree', autospec=True)
    KodiAddonDescriptions(kodi_directory).clean()
    rmmock.assert_has_calls([
        mock.call(os.path.join(
            kodi_directory, KodiAddonDescriptions.DESCRIPTION_PATH, game1)),
        mock.call(os.path.join(
            kodi_directory, KodiAddonDescriptions.DESCRIPTION_PATH, game2)),
    ])
    assert mock.call(os.path.join(
        kodi_directory, KodiAddonDescriptions.DESCRIPTION_PATH, 'other')) \
        not in rmmock.mock_calls


def test_kodiaddondescriptions_push(gitrepomock):
    """ Test pushing addon descriptions """
    KodiAddonDescriptions('path/repo').push('branch')
    gitrepomock.assert_called_once_with(GitHubRepo('repo', '', ''), 'path')
    gitrepomock.return_value.commit.assert_called_once_with(
        mock.ANY, KodiAddonDescriptions.DESCRIPTION_PATH, force=True)
    gitrepomock.return_value.push.assert_called_once_with('branch')


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
    print(templateprocessormock.mock_calls)

    templateprocessormock.process.assert_called_once_with(
        'description',
        os.path.join('kodidir', 'cmake', 'addons', 'addons', 'game.mygame'),
        mock.ANY)


def test_kodigameaddon_processaddon(kodigameaddon, templateprocessormock):
    """ Test processing addon files """
    kodigameaddon.process_addon_files()
    templateprocessormock.process.assert_called_once_with(
        'addon', os.path.join('tmpdir', 'game.mygame'), mock.ANY)


def make_option(key, description, values, default, **kwargs):
    """ Build an option as LibretroWrapper reports it

    values is a list of (value, label) pairs, or of plain values. """
    return LibretroWrapper.Option(
        key, description, kwargs.get('info', ''), kwargs.get('category', ''),
        [LibretroWrapper.OptionValue(*value)
         if isinstance(value, tuple) else LibretroWrapper.OptionValue(value, '')
         for value in values], default)


SYSTEM_INFO = {
    'name': 'libraryname', 'version': '123-ver', 'extensions': ['a'],
    'need_fullpath': True, 'block_extract': False,
    'supports_no_game': False, 'supports_disc_control': True,
}


def setup_library(libretrowrappermock, options, categories=()):
    """ Point the mocked wrapper at a set of options """
    system_info = LibretroWrapper.SystemInfo(dict(SYSTEM_INFO))
    libretrowrappermock.return_value.system_info = system_info
    libretrowrappermock.return_value.options = options
    libretrowrappermock.return_value.categories = [
        LibretroWrapper.Category(*category) for category in categories]
    libretrowrappermock.return_value.opengl_linkage = False
    return system_info


def test_kodigameaddon_loadlibraryfile(kodigameaddon, libretrowrappermock):
    """ Test loading info from compiled library """
    system_info = setup_library(libretrowrappermock, [
        make_option('setting1', 'Setting 1', ['enabled', 'disabled'],
                    'disabled'),
        make_option('setting2', 'Setting 2', ['0', '1'], '0'),
    ])
    kodigameaddon.load_library_file()
    assert kodigameaddon.info['library']['loaded']
    assert not kodigameaddon.info['library']['opengl']
    assert kodigameaddon.info['system_info'] is system_info

    # A core with no categories of its own gets the one category settings.xml
    # has always used: Kodi's own string 128, "General"
    categories = kodigameaddon.info['categories']
    assert [(c['id'], c['label']) for c in categories] == [('general', 128)]

    assert kodigameaddon.info['settings'] == [
        {'id': 'setting1', 'label': 30001, 'help': None,
         'default': 'disabled',
         'values': [{'value': 'enabled', 'label': None},
                    {'value': 'disabled', 'label': None}]},
        {'id': 'setting2', 'label': 30002, 'help': None, 'default': '0',
         'values': [{'value': '0', 'label': None},
                    {'value': '1', 'label': None}]},
    ]
    assert kodigameaddon.info['strings'] == [
        {'id': 30001, 'content': 'Setting 1'},
        {'id': 30002, 'content': 'Setting 2'},
    ]


def test_kodigameaddon_settingscategories(kodigameaddon, libretrowrappermock):
    """ Test that options are grouped into the categories a core declares """
    setup_library(libretrowrappermock, [
        make_option('vsync', 'VSync', ['on', 'off'], 'on', category='video'),
        make_option('loose', 'Loose', ['on', 'off'], 'on'),
        make_option('volume', 'Volume', ['0', '1'], '0', category='audio'),
        make_option('filter', 'Filter', ['on', 'off'], 'on', category='video'),
        make_option('bogus', 'Bogus', ['on', 'off'], 'on', category='nope'),
    ], categories=[('video', 'Video', 'What it looks like.'),
                   ('audio', 'Audio', '')])

    kodigameaddon.load_library_file()

    categories = kodigameaddon.info['categories']
    assert [(c['id'], c['label'], c['help'],
             [s['id'] for s in c['settings']]) for c in categories] == [
        # Uncategorised first, including an option naming a category the core
        # never declared, so they stay where users last saw them
        ('general', 128, None, ['loose', 'bogus']),
        ('video', 30003, 30004, ['vsync', 'filter']),
        ('audio', 30007, None, ['volume']),
    ]

    # IDs are allocated in the order the strings are met, category name and
    # description before the settings under it
    assert kodigameaddon.info['strings'] == [
        {'id': 30001, 'content': 'Loose'},
        {'id': 30002, 'content': 'Bogus'},
        {'id': 30003, 'content': 'Video'},
        {'id': 30004, 'content': 'What it looks like.'},
        {'id': 30005, 'content': 'VSync'},
        {'id': 30006, 'content': 'Filter'},
        {'id': 30007, 'content': 'Audio'},
        {'id': 30008, 'content': 'Volume'},
    ]


def test_kodigameaddon_settingshelpandlabels(kodigameaddon,
                                             libretrowrappermock):
    """ Test that help text and value labels get IDs of their own """
    setup_library(libretrowrappermock, [
        make_option('vsync', 'VSync', [('on', 'Enabled'), ('off', 'Disabled')],
                    'on', info='Wait for the display.'),
        make_option('filter', 'Filter', [('on', 'Enabled')], 'on'),
    ])

    kodigameaddon.load_library_file()

    vsync, filtering = kodigameaddon.info['settings']
    assert (vsync['label'], vsync['help']) == (30001, 30002)
    assert vsync['values'] == [{'value': 'on', 'label': 30003},
                               {'value': 'off', 'label': 30004}]

    # "Enabled" is the same string wherever it turns up, so it's translated
    # once rather than once per setting
    assert filtering['values'] == [{'value': 'on', 'label': 30003}]
    assert filtering['help'] is None

    assert kodigameaddon.info['strings'] == [
        {'id': 30001, 'content': 'VSync'},
        {'id': 30002, 'content': 'Wait for the display.'},
        {'id': 30003, 'content': 'Enabled'},
        {'id': 30004, 'content': 'Disabled'},
        {'id': 30005, 'content': 'Filter'},
    ]


def test_kodigameaddon_loadlibraryfileerr(kodigameaddon, libretrowrappermock):
    """ Test failure loading info from compiled library """
    libretrowrappermock.side_effect = OSError()
    kodigameaddon.load_library_file()
    assert not kodigameaddon.info['library']['loaded']
    assert kodigameaddon.info['library']['error']


def test_kodigameaddon_loadinfofile(kodigameaddon, mocker):
    """ Test loading info files from libretro-super """
    libretrosupermock = mocker.patch(
        'kodi_game_scripting.process_game_addons.LibretroSuper', autspec=True)
    kodigameaddon.load_info_file()
    libretrosupermock.return_value.parse_info_file \
        .assert_called_once_with('mygame_libretro')


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


def test_kodigameaddon_gittag(kodigameaddon, githuborgmock):
    """ Test loaing git tag """
    tagmock = mock.MagicMock()
    tagnamemock = mock.PropertyMock(return_value='mytag')
    type(tagmock).name = tagnamemock
    githuborgmock.return_value.get_repo.return_value.get_tags.return_value \
        .__getitem__.return_value = tagmock
    kodigameaddon.info['libretro_repo']['git_tag'] = False
    kodigameaddon.load_git_tag()
    assert kodigameaddon.info['libretro_repo']['branch'] == 'master'
    kodigameaddon.info['libretro_repo']['git_tag'] = True
    kodigameaddon.load_git_tag()
    tagnamemock.assert_called_once_with()
    assert kodigameaddon.info['libretro_repo']['branch'] == 'mytag'


def test_kodigameaddon_gitrevision(kodigameaddon, gitrepomock):
    """ Test loading git revision """
    gitrepomock.is_git_repo.return_value = True
    gitrepomock.return_value.get_hexsha.return_value = '1234567'
    kodigameaddon.load_git_revision()
    gitrepomock.assert_has_calls([
        mock.call(GitHubRepo(kodigameaddon.game_name, '', ''), mock.ANY)
    ])
    assert kodigameaddon.info['libretro_repo']['hexsha'] == '1234567'


def test_kodigameaddon_gitrevisionnorepo(kodigameaddon, gitrepomock):
    """ Test loading git revision when not a Git repository """
    gitrepomock.is_git_repo.return_value = False
    kodigameaddon.load_git_revision()
    assert mock.call(GitHubRepo(kodigameaddon.game_name, '', ''), mock.ANY) \
        not in gitrepomock.mock_calls
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
    assert kodigameaddon.info['game']['version'] == '1.2.3.0'


def test_kodigameaddon_bumpversion(kodigameaddon):
    """ Test bumping game version """
    kodigameaddon.info['game']['version'] = '1.2.3.1'
    kodigameaddon.bump_version()
    assert kodigameaddon.info['game']['version'] == '1.2.3.2'


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
    gitrepomock.return_value.push.assert_called_once_with(
        'master', tags=True, sleep=mock.ANY)


def test_kodigameaddon_pushbranch(kodigameaddon, gitrepomock):
    """ Test pushing changes (other branch) """
    kodigameaddon.info['game']['branch'] = 'testbranch'
    kodigameaddon.push()
    gitrepomock.return_value.push.assert_called_once_with(
        'testbranch', tags=False, sleep=mock.ANY)
