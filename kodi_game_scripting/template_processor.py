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

""" Process Jinja2 templates """

import os
import re
import shutil
import xml.sax.saxutils

import jinja2

from . import utils

TEMPLATE_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.realpath(__file__))),
    'templates')


def get_list(value):
    """ Filter: Returns a list (existing list or new single elemented list) """
    return value if isinstance(value, list) else [value]


def regex_replace(string, find, replace, *, multiline=False):
    """ Filter: Replace regex in string """
    flags = 0
    if multiline:
        flags += re.MULTILINE
    return re.sub(find, replace, string, flags=flags)


def escape_xml(string):
    """Filter: Replace unsafe XML characters with named references"""
    return (
        string.replace('&', '&amp;')
        .replace("'", '&apos;')
        .replace('"', '&quot;')
        .replace('<', '&lt;')
        .replace('>', '&gt;')
    )


class TemplateProcessor:
    """ Process Jinja2 templates """

    @classmethod
    def process(cls, template_dir, destination, template_vars):
        """ Process templates """

        class _TreeUndefined(jinja2.Undefined):
            def __getitem__(self, key):
                return self

            def __getattr__(self, key):
                return self

        template_dir = os.path.join(TEMPLATE_DIR, template_dir)
        template_env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(template_dir),
            trim_blocks=True, lstrip_blocks=True, keep_trailing_newline=True,
            undefined=_TreeUndefined)

        template_env.filters["regex_replace"] = regex_replace
        template_env.filters["get_list"] = get_list
        template_env.filters["escape_xml"] = escape_xml

        # Loop over all templates
        for infile in utils.list_all_files(template_dir):

            # Files may have templatized names
            if '{{' in infile and '}}' in infile:
                outfile = jinja2.Template(infile).render(template_vars)
            else:
                outfile = infile
            outfile_name, extension = os.path.splitext(outfile)

            # Files that end with .j2 are templates
            if extension == '.j2':
                print("  Generating {}".format(outfile_name))
                outfile_path = os.path.join(destination, outfile_name)

                # Make content of already existing XML files available in
                # the template. That way templates can decide what data to keep
                # or override.
                if '.xml' in infile and os.path.isfile(outfile_path):
                    xml_data = utils.get_xml_data(outfile_path)
                    template_vars.update({'xml': xml_data})

                # Make the datetime of strings files the existing datetime
                if '.po' in infile and os.path.isfile(outfile_path):
                    with open(outfile_path, 'r') as stringsfile_ctx:
                        strings_content = stringsfile_ctx.read()

                    datere = re.compile(r'"POT-Creation-Date: (.*)\\n"')
                    timestamp = datere.search(strings_content).group(1)
                    template_vars.update({'datetime': timestamp})

                template = template_env.get_template(infile)
                content = template.render(template_vars, regex_replace=regex_replace)
                if content:
                    utils.ensure_directory_exists(
                        os.path.dirname(os.path.join(destination, outfile)))
                    with open(outfile_path, 'w') as outfile_ctx:
                        outfile_ctx.write(content)
                elif os.path.exists(outfile_path):
                    os.remove(outfile_path)

            # Other files are just copied
            else:
                print("     Copying {}{}".format(outfile_name, extension))
                utils.ensure_directory_exists(
                    os.path.dirname(os.path.join(destination, outfile)))
                shutil.copyfile(os.path.join(template_dir, infile),
                                os.path.join(destination, outfile))
