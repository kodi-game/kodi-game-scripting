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


def assert_option_labels_are_all_or_none(settings):
    """Assert that each setting labels either every option or no options."""
    for setting in settings:
        labels = [value['label'] is not None for value in setting['values']]
        assert all(labels) or not any(labels)


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
         'values': [{'value': 'enabled', 'label': 305},
                    {'value': 'disabled', 'label': 13106}]},
        {'id': 'setting2', 'label': 30002, 'help': None, 'default': '0',
         'values': [{'value': '0', 'label': None},
                    {'value': '1', 'label': None}]},
    ]
    assert kodigameaddon.info['strings'] == [
        {'id': 30001, 'content': 'Setting 1', 'obsolete': False},
        {'id': 30002, 'content': 'Setting 2', 'obsolete': False},
    ]
    assert_option_labels_are_all_or_none(kodigameaddon.info['settings'])


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
        {'id': 30001, 'content': 'Loose', 'obsolete': False},
        {'id': 30002, 'content': 'Bogus', 'obsolete': False},
        {'id': 30003, 'content': 'Video', 'obsolete': False},
        {'id': 30004, 'content': 'What it looks like.', 'obsolete': False},
        {'id': 30005, 'content': 'VSync', 'obsolete': False},
        {'id': 30006, 'content': 'Filter', 'obsolete': False},
        {'id': 30007, 'content': 'Audio', 'obsolete': False},
        {'id': 30008, 'content': 'Volume', 'obsolete': False},
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
        {'id': 30001, 'content': 'VSync', 'obsolete': False},
        {'id': 30002, 'content': 'Wait for the display.', 'obsolete': False},
        {'id': 30003, 'content': 'Enabled', 'obsolete': False},
        {'id': 30004, 'content': 'Disabled', 'obsolete': False},
        {'id': 30005, 'content': 'Filter', 'obsolete': False},
    ]


def test_kodigameaddon_unlabelled_generic_values(kodigameaddon,
                                                 libretrowrappermock):
    """Test that common unlabelled values use Kodi's built-in strings."""
    setup_library(libretrowrappermock, [
        make_option('generic', 'Generic',
                    ['disabled', 'enabled', 'Disabled', 'none', 'auto',
                     'default', 'off', 'on', 'On', 'no', 'yes', 'true',
                     'false', 'always', 'never'], 'disabled'),
    ])

    kodigameaddon.load_library_file()

    assert kodigameaddon.info['settings'][0]['values'] == [
        {'value': 'disabled', 'label': 13106},
        {'value': 'enabled', 'label': 305},
        {'value': 'Disabled', 'label': 13106},
        {'value': 'none', 'label': 231},
        {'value': 'auto', 'label': 16316},
        {'value': 'default', 'label': 571},
        {'value': 'off', 'label': 351},
        {'value': 'on', 'label': 16041},
        {'value': 'On', 'label': 16041},
        {'value': 'no', 'label': 106},
        {'value': 'yes', 'label': 107},
        {'value': 'true', 'label': 20122},
        {'value': 'false', 'label': 20424},
        {'value': 'always', 'label': 34122},
        {'value': 'never', 'label': 34123},
    ]
    assert kodigameaddon.info['strings'] == [
        {'id': 30001, 'content': 'Generic', 'obsolete': False},
    ]


def test_kodigameaddon_explicit_value_label_takes_precedence(
        kodigameaddon, libretrowrappermock):
    """Test that a core's explicit label overrides a built-in string."""
    setup_library(libretrowrappermock, [
        make_option('power', 'Power', [('disabled', 'Core Disabled')],
                    'disabled'),
    ])

    kodigameaddon.load_library_file()

    assert kodigameaddon.info['settings'][0]['values'] == [
        {'value': 'disabled', 'label': 30002},
    ]
    assert kodigameaddon.info['strings'] == [
        {'id': 30001, 'content': 'Power', 'obsolete': False},
        {'id': 30002, 'content': 'Core Disabled', 'obsolete': False},
    ]


def test_kodigameaddon_arbitrary_unlabelled_values(kodigameaddon,
                                                   libretrowrappermock):
    """Test that an entirely unlabelled list stays literal."""
    setup_library(libretrowrappermock, [
        make_option('revision', 'Revision', ['foo', 'bar'], 'bar'),
    ])

    kodigameaddon.load_library_file()

    setting = kodigameaddon.info['settings'][0]
    assert setting['default'] == 'bar'
    assert setting['values'] == [{'value': 'foo', 'label': None},
                                 {'value': 'bar', 'label': None}]
    assert kodigameaddon.info['strings'] == [
        {'id': 30001, 'content': 'Revision', 'obsolete': False},
    ]
    assert_option_labels_are_all_or_none(kodigameaddon.info['settings'])


def test_kodigameaddon_generic_value_completes_option_labels(
        kodigameaddon, libretrowrappermock):
    """A built-in label makes every value in its setting receive a label."""
    setup_library(libretrowrappermock, [
        make_option('quality', 'Quality',
                    ['None', 'Low', 'Medium', 'High'], 'Medium'),
    ])

    kodigameaddon.load_library_file()

    setting = kodigameaddon.info['settings'][0]
    assert setting['default'] == 'Medium'
    assert setting['values'] == [
        {'value': 'None', 'label': 231},
        {'value': 'Low', 'label': 30002},
        {'value': 'Medium', 'label': 30003},
        {'value': 'High', 'label': 30004},
    ]
    assert kodigameaddon.info['strings'] == [
        {'id': 30001, 'content': 'Quality', 'obsolete': False},
        {'id': 30002, 'content': 'Low', 'obsolete': False},
        {'id': 30003, 'content': 'Medium', 'obsolete': False},
        {'id': 30004, 'content': 'High', 'obsolete': False},
    ]
    assert_option_labels_are_all_or_none(kodigameaddon.info['settings'])

    # Regenerating from the resulting table keeps every add-on ID stable.
    kodigameaddon.info['oldstrings'] = kodigameaddon.info['strings']
    kodigameaddon.load_library_file()
    assert kodigameaddon.info['settings'][0] == setting


def test_kodigameaddon_explicit_label_completes_option_labels(
        kodigameaddon, libretrowrappermock):
    """A core label takes precedence and labels arbitrary peers as raw text."""
    setup_library(libretrowrappermock, [
        make_option('speed', 'Speed',
                    [('Disabled', 'Core Disabled'), 'Normal', 'Very Fast'],
                    'Very Fast'),
    ])

    kodigameaddon.load_library_file()

    setting = kodigameaddon.info['settings'][0]
    assert setting['default'] == 'Very Fast'
    assert setting['values'] == [
        {'value': 'Disabled', 'label': 30002},
        {'value': 'Normal', 'label': 30003},
        {'value': 'Very Fast', 'label': 30004},
    ]
    assert kodigameaddon.info['strings'] == [
        {'id': 30001, 'content': 'Speed', 'obsolete': False},
        {'id': 30002, 'content': 'Core Disabled', 'obsolete': False},
        {'id': 30003, 'content': 'Normal', 'obsolete': False},
        {'id': 30004, 'content': 'Very Fast', 'obsolete': False},
    ]
    assert_option_labels_are_all_or_none(kodigameaddon.info['settings'])


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


@pytest.mark.parametrize(('changed_files', 'expected'), [
    (['depends/common/mygame/CMakeLists.txt'], False),
    (['depends/common/mygame/mygame.txt'], True),
    (['depends/common/mygame/CMakeLists.txt',
      'depends/common/mygame/mygame.txt'], True),
    (['game.mygame/addon.xml.in', 'CMakeLists.txt'], False),
])
def test_kodigameaddon_needsversionbump(kodigameaddon, changed_files,
                                        expected):
    """ Test identifying dependency changes that need a version bump """
    kodigameaddon.info['git']['diff'] = '\n'.join(
        'diff --git a/{0} b/{0}'.format(path) for path in changed_files)
    assert kodigameaddon.needs_version_bump() is expected


def test_kodigameaddon_needsversionbump_ignores_diff_content(kodigameaddon):
    """ Test that dependency paths in patch content do not trigger a bump """
    kodigameaddon.info['git']['diff'] = """\
diff --git a/game.mygame/addon.xml.in b/game.mygame/addon.xml.in
--- a/game.mygame/addon.xml.in
+++ b/game.mygame/addon.xml.in
@@ -1 +1 @@
-depends/common/mygame/mygame.txt
+depends/common/mygame/CMakeLists.txt
"""
    assert not kodigameaddon.needs_version_bump()


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
