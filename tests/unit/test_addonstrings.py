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

""" Test string ID allocation """

import os

import polib
import pytest

from kodi_game_scripting.addon_strings import (
    KODI_LANGUAGES, SOURCE_LANGUAGE, STRINGS_PO_PATH, StringTable,
    by_kodi_language, read_strings, strings_po_path, write_translations)
from kodi_game_scripting.libretro_ctypes import RETRO_LANGUAGE_TAGS

pytestmark = [pytest.mark.unit]


PO_HEADER = '''msgid ""
msgstr ""
"Project-Id-Version: game.libretro.test\\n"
"MIME-Version: 1.0\\n"
"Content-Type: text/plain; charset=UTF-8\\n"
"Content-Transfer-Encoding: 8bit\\n"
"Language: en_gb\\n"

'''


def write_po(addon_path, body):
    """ Write a strings.po for an add-on """
    strings_path = os.path.join(addon_path, STRINGS_PO_PATH)
    os.makedirs(os.path.dirname(strings_path), exist_ok=True)
    with open(strings_path, 'w', encoding='utf-8') as strings_file:
        strings_file.write(PO_HEADER + body)
    return strings_path


def test_allocates_from_30001():
    """ Test that a new add-on starts at 30001, leaving 30000 empty """
    table = StringTable()
    assert table.get('Setting 1') == 30001
    assert table.get('Setting 2') == 30002


def test_empty_text_gets_no_id():
    """ Test that text a core didn't supply doesn't consume an ID """
    table = StringTable()
    assert table.get('') is None
    assert table.get(None) is None
    assert table.get('Setting 1') == 30001


def test_reuses_ids_for_known_text():
    """ Test that text keeps its ID, so translations stay attached """
    table = StringTable([{'id': 30001, 'content': 'Setting 1'},
                         {'id': 30002, 'content': 'Setting 2'}])
    assert table.get('Setting 2') == 30002
    assert table.get('Setting 1') == 30001
    # New text goes above everything, not into the gap it would fit
    assert table.get('Setting 3') == 30003


def test_same_text_in_a_different_role_keeps_its_id():
    """ Test that an option label reused as a value label shares its ID """
    table = StringTable([{'id': 30005, 'content': 'Enabled'}])
    assert table.get('Enabled') == 30005
    assert table.get('Enabled') == 30005


def test_allocates_above_the_highest_id_not_the_last():
    """ Test that a file listing IDs out of order still grows upwards """
    table = StringTable([{'id': 30009, 'content': 'Setting 9'},
                         {'id': 30002, 'content': 'Setting 2'}])
    assert table.get('Setting 10') == 30010


def test_never_reuses_the_id_of_dropped_text():
    """ Test the rule that protects sixty other translation files

    A core dropping an option must not free its ID for different text: the
    translations of the old string are still out there, keyed by number. """
    table = StringTable([{'id': 30001, 'content': 'Setting 1'},
                         {'id': 30002, 'content': 'Dropped by the core'}])
    assert table.get('Setting 1') == 30001
    assert table.get('Brand new setting') == 30003

    # And the dropped text stays in the file as an obsolete entry, so the next
    # run still sees 30002 as taken while Weblate no longer offers it
    assert table.strings() == [
        {'id': 30001, 'content': 'Setting 1', 'obsolete': False},
        {'id': 30002, 'content': 'Dropped by the core', 'obsolete': True},
        {'id': 30003, 'content': 'Brand new setting', 'obsolete': False},
    ]


def test_strings_come_back_sorted_by_id():
    """ Test that output order is stable, whatever order text arrives in """
    table = StringTable()
    table.get('Second')
    table.get('First')
    assert [string['id'] for string in table.strings()] == [30001, 30002]


def test_generating_twice_is_a_no_op(tmpdir):
    """ Test the property that protects every add-on repo: idempotence """
    first = StringTable(read_strings(str(tmpdir)))
    for text in ['Setting 1', 'What setting 1 does.', 'Enabled', 'Disabled']:
        first.get(text)

    write_po(str(tmpdir), '\n'.join(
        'msgctxt "#{}"\nmsgid "{}"\nmsgstr ""\n'.format(
            string['id'], string['content'])
        for string in first.strings()))

    second = StringTable(read_strings(str(tmpdir)))
    for text in ['Setting 1', 'What setting 1 does.', 'Enabled', 'Disabled']:
        second.get(text)

    assert second.strings() == first.strings()


def test_reads_text_that_would_break_a_line_based_parser(tmpdir):
    """ Test round-tripping the help text this whole change is about

    Core help text has newlines and quotes in it, and .po wraps long
    strings over several lines. """
    helptext = ('Joystick and Console Key mappings for\n"Atari Keyboard". '
                'This one is deliberately long enough that a writer is '
                'entitled to wrap it over several lines in the file.')
    write_po(str(tmpdir),
             'msgctxt "#30001"\n'
             'msgid ""\n'
             '"Joystick and Console Key mappings for\\n"\n'
             '"\\"Atari Keyboard\\". This one is deliberately long enough '
             'that a writer is "\n'
             '"entitled to wrap it over several lines in the file."\n'
             'msgstr ""\n')

    strings = read_strings(str(tmpdir))
    assert strings == [{'id': 30001, 'content': helptext, 'obsolete': 0}]

    # And having read it back, it keeps its ID rather than getting a new one
    assert StringTable(strings).get(helptext) == 30001


def test_missing_file_is_not_an_error(tmpdir):
    """ Test that an add-on being created for the first time reads as empty """
    assert not read_strings(str(tmpdir))


def test_non_numeric_entries_are_ignored(tmpdir):
    """ Test that the add-on metadata strings don't take part in numbering """
    write_po(str(tmpdir),
             'msgctxt "Addon Summary"\nmsgid "A core"\nmsgstr ""\n\n'
             'msgctxt "#30001"\nmsgid "Setting 1"\nmsgstr ""\n')
    assert read_strings(str(tmpdir)) == [
        {'id': 30001, 'content': 'Setting 1', 'obsolete': 0}]


def test_every_mapped_language_is_one_libretro_can_report():
    """ A typo here would quietly drop a language's translations """
    assert set(KODI_LANGUAGES) <= set(RETRO_LANGUAGE_TAGS.values())


def test_the_source_catalogue_is_never_a_target():
    """ A core's English must not overwrite what the add-on declares """
    assert 'en' not in KODI_LANGUAGES
    assert 'en-GB' not in KODI_LANGUAGES
    assert SOURCE_LANGUAGE not in KODI_LANGUAGES.values()


def test_no_two_languages_share_a_directory():
    """ Two mapped to one would have the second overwrite the first """
    targets = list(KODI_LANGUAGES.values())
    assert len(targets) == len(set(targets))


def test_translations_are_rekeyed_by_kodi_language():
    """ What the writer needs is the directory, not the libretro name """
    translated = by_kodi_language({'french': {'On': 'Activé'},
                                   'german': {'On': 'Ein'}})
    assert translated == {'fr_fr': {'On': 'Activé'},
                          'de_de': {'On': 'Ein'}}


def test_languages_kodi_cannot_hold_are_dropped():
    """ Irish and Catalan (Valencia) have no directory to write to """
    assert not by_kodi_language({'irish': {'On': 'Ar'},
                                 'catalan_valencia': {'On': 'Activat'},
                                 'british_english': {'On': 'On'}})


def test_the_strings_path_defaults_to_the_source_catalogue():
    """ Existing callers read en_gb and must keep doing so """
    assert strings_po_path() == STRINGS_PO_PATH
    assert strings_po_path('fr_fr') == os.path.join(
        'resources', 'language', 'resource.language.fr_fr', 'strings.po')


def test_a_language_kodi_cannot_store_is_dropped():
    """ Kodi has no directory for Irish or Valencian, so they go nowhere """
    assert not by_kodi_language({'irish': {'On': 'Ar'},
                                 'catalan_valencia': {'On': 'Actiu'}})


def test_the_script_is_what_libretro_names_not_the_country():
    """ zh-Hant is a script; Kodi happens to file it under a Taiwan locale """
    assert by_kodi_language({'chinese_traditional': {'On': '\u958b'}}) == \
        {'zh_tw': {'On': '\u958b'}}


TRANSLATED_PO = PO_HEADER + """
msgctxt "#30001"
msgid "On"
msgstr "Ein"

msgctxt "#30002"
msgid "Off"
msgstr ""
"""


def _write_language(tmpdir, language, body):
    path = os.path.join(str(tmpdir), strings_po_path(language))
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as handle:
        handle.write(body)
    return path


def _entries(path):
    return {e.msgctxt: e.msgstr for e in polib.pofile(path) if e.msgctxt}


def test_a_core_translation_wins_over_what_is_already_there(tmpdir):
    """ libretro is the source of truth for the strings it knows """
    path = _write_language(tmpdir, 'de_de', TRANSLATED_PO)
    strings = [{'id': 30001, 'content': 'On', 'obsolete': False}]

    written = write_translations(str(tmpdir), strings,
                                 {'german': {'On': 'An'}})

    assert written == ['de_de']
    assert _entries(path)['#30001'] == 'An'


def test_weblate_fills_what_the_core_has_no_translation_for(tmpdir):
    """ A string the core cannot translate keeps the work already done """
    path = _write_language(tmpdir, 'de_de', TRANSLATED_PO)
    strings = [{'id': 30001, 'content': 'On', 'obsolete': False},
               {'id': 30002, 'content': 'Off', 'obsolete': False}]

    write_translations(str(tmpdir), strings, {'german': {'Off': 'Aus'}})

    entries = _entries(path)
    assert entries['#30001'] == 'Ein'
    assert entries['#30002'] == 'Aus'


def test_a_string_the_file_has_never_seen_is_added(tmpdir):
    """ The English catalogue grows, and the translations follow it """
    path = _write_language(tmpdir, 'de_de', TRANSLATED_PO)
    strings = [{'id': 30003, 'content': 'Fast forward', 'obsolete': False}]

    write_translations(str(tmpdir), strings,
                       {'german': {'Fast forward': 'Vorspulen'}})

    assert _entries(path)['#30003'] == 'Vorspulen'


def test_a_language_the_addon_has_no_file_for_is_left_alone(tmpdir):
    """ Creating one means inventing a Plural-Forms header """
    _write_language(tmpdir, 'de_de', TRANSLATED_PO)
    strings = [{'id': 30001, 'content': 'On', 'obsolete': False}]

    written = write_translations(str(tmpdir), strings,
                                 {'french': {'On': 'Activé'}})

    assert not written
    assert not os.path.exists(os.path.join(str(tmpdir),
                                           strings_po_path('fr_fr')))


def test_nothing_is_written_when_nothing_changed(tmpdir):
    """ Rewriting every file each run would churn sixty of them for nothing """
    _write_language(tmpdir, 'de_de', TRANSLATED_PO)
    strings = [{'id': 30001, 'content': 'On', 'obsolete': False}]

    assert not write_translations(str(tmpdir), strings,
                                  {'german': {'On': 'Ein'}})


def test_the_source_catalogue_is_never_written(tmpdir):
    """ A core's English must not overwrite what the add-on declares """
    path = _write_language(tmpdir, SOURCE_LANGUAGE, TRANSLATED_PO)
    strings = [{'id': 30001, 'content': 'On', 'obsolete': False}]
    english = {'english': {'On': 'ON!'}, 'british_english': {'On': 'ON!'}}

    write_translations(str(tmpdir), strings, english)

    assert _entries(path)['#30001'] == 'Ein'


def test_a_long_line_is_not_rewrapped(tmpdir):
    """ Saving must not reflow the file, or the diff is the whole catalogue """
    long_text = ('Use High Level Emulation BIOS. Not recommended, as it is '
                 'causing more issues than it solves.')
    body = PO_HEADER + f"""
msgctxt "#30001"
msgid "{long_text}"
msgstr ""

msgctxt "#30002"
msgid "Off"
msgstr ""
"""
    path = _write_language(tmpdir, 'de_de', body)
    strings = [{'id': 30001, 'content': long_text, 'obsolete': False},
               {'id': 30002, 'content': 'Off', 'obsolete': False}]

    write_translations(str(tmpdir), strings, {'german': {'Off': 'Aus'}})

    with open(path, encoding='utf-8') as handle:
        written = handle.read()

    assert f'msgid "{long_text}"' in written
    assert 'msgid ""\n"Use High Level' not in written
