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

""" String IDs for add-on settings

    Every label a settings.xml refers to is a number, and the text behind that
    number lives in strings.po, which Weblate then translates into sixty-odd
    languages. Those translations are keyed by the number alone, so an ID that
    changes meaning silently mistranslates -- a German string attached to an
    English one it was never written for. This module exists to make that
    impossible. """

import os
import re

import polib


# Add-on strings are conventionally 30000-30999. 30000 itself is left empty.
FIRST_STRING_ID = 30000

STRINGS_PO_PATH = os.path.join('resources', 'language',
                               'resource.language.en_gb', 'strings.po')

_NUMERIC_MSGCTXT = re.compile(r'^#(\d+)$')


def read_strings(addon_path):
    """ Read the numbered strings out of an add-on's en_gb strings.po

    Returns a list of {'id', 'content'}, sorted by ID. Anything the file
    can't be read as is treated as no strings at all, which costs a
    regenerated set of IDs but never a wrong one. """
    strings_path = os.path.join(addon_path, STRINGS_PO_PATH)
    if not os.path.isfile(strings_path):
        return []

    try:
        entries = polib.pofile(strings_path)
    except (OSError, UnicodeDecodeError, IOError):
        return []

    strings = []
    for entry in entries:
        match = _NUMERIC_MSGCTXT.match(entry.msgctxt or '')
        if match:
            strings.append({'id': int(match.group(1)), 'content': entry.msgid})

    strings.sort(key=lambda string: string['id'])
    return strings


class StringTable:
    """ Hands out string IDs for the text a core declares

        Two rules, and everything else follows from them:

        - the same text always gets the same ID, so nothing needs retranslating
          just because a setting moved or gained help text
        - an ID is never handed out twice, not even one freed up when a core
          drops an option, because the translations for it still exist in
          sixty other files """

    def __init__(self, existing_strings=None):
        self._by_content = {}
        self._used = {}
        self._highest_id = FIRST_STRING_ID

        for string in existing_strings or []:
            content, string_id = string['content'], string['id']
            # First ID wins if a file somehow has the same text twice
            self._by_content.setdefault(content, string_id)
            self._highest_id = max(self._highest_id, string_id)

        self._orphans = dict(self._by_content)

    def get(self, content):
        """ The ID for this text, allocating one if it's new

        Returns None for text a core didn't supply, so callers can leave the
        attribute out rather than point at an empty string. """
        if not content:
            return None

        string_id = self._by_content.get(content)
        if string_id is None:
            self._highest_id += 1
            string_id = self._highest_id
            self._by_content[content] = string_id

        self._orphans.pop(content, None)
        self._used[string_id] = content
        return string_id

    def strings(self):
        """ Every string to write back, sorted by ID

        Text no core declares any more is kept rather than dropped. Dropping
        it would lower the highest ID the next run sees, and the run after
        that would hand the same ID to different text. """
        strings = [{'id': string_id, 'content': content}
                   for string_id, content in self._used.items()]
        strings.extend({'id': string_id, 'content': content}
                       for content, string_id in self._orphans.items())
        strings.sort(key=lambda string: string['id'])
        return strings
