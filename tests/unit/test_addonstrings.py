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

import pytest

from kodi_game_scripting.addon_strings import (
    STRINGS_PO_PATH, StringTable, read_strings)

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

    # And the dropped text stays in the file, so the next run still sees
    # 30002 as taken
    assert table.strings() == [
        {'id': 30001, 'content': 'Setting 1'},
        {'id': 30002, 'content': 'Dropped by the core'},
        {'id': 30003, 'content': 'Brand new setting'},
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
    assert strings == [{'id': 30001, 'content': helptext}]

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
        {'id': 30001, 'content': 'Setting 1'}]
