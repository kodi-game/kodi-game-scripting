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

""" Common utility functions """

import os
import re
import shutil
from typing import Any
from typing import Dict
import xml.etree.ElementTree
import xmljson


def ensure_directory_exists(path, clean=False):
    """ Ensure that the given path exists """
    try:
        if clean and os.path.exists(path):
            shutil.rmtree(path)

        if not os.path.exists(path):
            os.makedirs(path)
    except OSError:
        pass


def get_xml_data(xml_path: str) -> Dict[str, Any]:
    if not os.path.exists(xml_path):
        return {}

    with open(xml_path, 'r') as xmlfile_ctx:
        xml_content = xmlfile_ctx.read()

    # Remove variables from xml.in files
    xml_content = re.sub(r'@([A-Za-z0-9_]+)@', r'AT_\1_AT',
                         xml_content)
    xml_data: Dict[str, Any] = {}
    try:
        # Like Yahoo converter, but don't omit 'content' if
        # there are no attributes.
        converter = xmljson.XMLData(
            xml_fromstring=False,
            simple_text=False,
            text_content="content"
        )
        root = xml.etree.ElementTree.fromstring(xml_content)
        xml_data = converter.data(root)

        # Parsed XML Data will contain OrderedDict() as empty
        # value which converts to 'OrderedDict()' instead of ''
        # in the templates. Remove empty fields instead.
        xml_data = purify(xml_data)
    except xml.etree.ElementTree.ParseError as err:
        print("Failed to parse {}: {}".format(
            xml_path, err))

    return xml_data


def list_all_files(path):
    """ Get a list with relative paths for all files in the given path """
    all_files = []
    for dirpath, _, filenames in os.walk(path):
        relpath = os.path.relpath(dirpath, path)
        for filename in filenames:
            all_files.append(os.path.normpath(os.path.join(relpath, filename)))
    return all_files


def purify(obj):
    """ Recursively strip empty elements from dicts, lists and others """
    def _is_not_empty(val):
        return val not in [[], {}, (), None]

    if isinstance(obj, dict):
        return type(obj)((k, purify(v)) for k, v in obj.items()
                         if _is_not_empty(v) and purify(v))
    if isinstance(obj, (list, tuple, set)):
        return type(obj)(purify(v) for v in obj
                         if _is_not_empty(v) and purify(v))
    return obj


def xstr(string):
    """ Convert string to UTF-8, (NoneType as '') """
    if string is None:
        return ''
    return str(string, 'utf-8')
