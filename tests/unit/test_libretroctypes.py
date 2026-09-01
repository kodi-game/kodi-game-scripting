# Copyright (C) 2026 Christian Fetzer
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

""" Test pairing a core's translated strings with the English """

import pytest

from kodi_game_scripting.libretro_ctypes import (
    RETRO_LANGUAGE_TAGS, RetroLanguage, _pair_strings)

pytestmark = [pytest.mark.unit]


def _option(key, description, info='', values=None):
    return {'key': key, 'description': description, 'info': info,
            'category': '', 'default': '',
            'values': [{'value': value, 'label': label}
                       for value, label in (values or [])]}


def test_pairs_descriptions_help_and_value_labels():
    """ Descriptions, help text and value labels all carry translations """
    english = {'options': [_option('region', 'System Region', 'Pick one',
                                   [('ntsc', 'NTSC')])],
               'categories': [{'key': 'video', 'description': 'Video',
                               'info': 'Video options'}]}
    french = {'options': [_option('region', 'Région du système', 'Choisissez',
                                  [('ntsc', 'NTSC-U')])],
              'categories': [{'key': 'video', 'description': 'Vidéo',
                              'info': 'Options vidéo'}]}

    assert _pair_strings(english, french) == {
        'System Region': 'Région du système',
        'Pick one': 'Choisissez',
        'NTSC': 'NTSC-U',
        'Video': 'Vidéo',
        'Video options': 'Options vidéo',
    }


def test_untranslated_strings_are_left_out():
    """ A core with no table for a language returns the English again """
    english = {'options': [_option('region', 'System Region')],
               'categories': []}

    assert not _pair_strings(english, english)


def test_options_are_matched_by_key_not_by_position():
    """ Cores are free to order the translated table differently """
    english = {'options': [_option('a', 'First'), _option('b', 'Second')],
               'categories': []}
    german = {'options': [_option('b', 'Zweitens'), _option('a', 'Erstens')],
              'categories': []}

    assert _pair_strings(english, german) == {'First': 'Erstens',
                                              'Second': 'Zweitens'}


def test_an_option_the_translation_drops_is_skipped():
    """ A table that has fallen behind the English is still usable """
    english = {'options': [_option('a', 'First'), _option('gone', 'Missing')],
               'categories': []}
    german = {'options': [_option('a', 'Erstens')], 'categories': []}

    assert _pair_strings(english, german) == {'First': 'Erstens'}


def test_languages_are_indexed_by_their_libretro_value():
    """ The index is what gets handed to the core, so it must not drift """
    assert RetroLanguage.ENGLISH == 0
    assert RetroLanguage.FRENCH == 2
    assert RetroLanguage.BRITISH_ENGLISH == 30
    assert RetroLanguage.THAI == 36
    assert len(RetroLanguage) == 37
    assert RetroLanguage.PORTUGUESE_BRAZIL.libretro_name == 'portuguese_brazil'


def test_every_language_has_a_tag():
    """ A new libretro language must not slip past the normalisation layer """
    assert set(RETRO_LANGUAGE_TAGS) == set(RetroLanguage)


def test_no_two_languages_share_a_tag():
    """ Two mapped to one would have the second overwrite the first """
    tags = list(RETRO_LANGUAGE_TAGS.values())
    assert len(tags) == len(set(tags))
