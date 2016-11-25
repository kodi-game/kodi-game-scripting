#!/usr/bin/env python3

# Copyright (C) 2016 Christian Fetzer
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

""" Process Kodi Game addons and unify project files """

import argparse
import os
import shutil

import jinja2

DIR = os.path.dirname(os.path.realpath(__file__))


def main():
    """ Process Kodi Game addons and unify project files """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--game-addons-dir', dest='working_directory',
                        type=str, required=True,
                        help='Directory where the game addons reside')

    args = parser.parse_args()
    process(os.path.abspath(args.working_directory))


def process(working_directory):
    """ Process Kodi Game addons and unify project files """
    template_dir = os.path.join(DIR, 'template')
    working_dir = os.path.abspath(working_directory)

    template_env = jinja2.Environment(
        loader=jinja2.FileSystemLoader(template_dir))

    for addon in next(os.walk(working_dir))[1]:
        print("Processing addon: {}".format(addon))
        addon_dir = os.path.join(working_dir, addon)
        template_vars = {'game': {'name': addon.rsplit('.', 1)[1]},
                         'makefile': {}}

        for infile in list_all_files(template_dir):
            if '{{' in infile and '}}' in infile:
                outfile = jinja2.Template(infile).render(template_vars)
            else:
                outfile = infile
            outfile_name, extension = os.path.splitext(outfile)

            ensure_directory_exists(
                os.path.dirname(os.path.join(addon_dir, outfile)))
            if extension == '.j2':
                print("  Generating {}".format(outfile_name))
                template = template_env.get_template(infile)
                template.stream(template_vars).dump(
                    os.path.join(addon_dir, outfile_name))
            else:
                print("  Copying {}".format(outfile_name))
                shutil.copyfile(os.path.join(template_dir, infile),
                                os.path.join(addon_dir, outfile))


def ensure_directory_exists(path):
    """ Ensure that the given path exists """
    try:
        if not os.path.exists(path):
            os.makedirs(path)
    except OSError:
        pass


def list_all_files(path):
    """ Get a list with relative paths for all files in the given path """
    all_files = []
    for dirpath, dirs, filenames in os.walk(path):
        # Don't process hidden files
        dirs[:] = [d for d in dirs if not d[0] == '.']
        filenames = [f for f in filenames if not f[0] == '.']

        relpath = os.path.relpath(dirpath, path)
        for filename in filenames:
            all_files.append(os.path.normpath(os.path.join(relpath, filename)))
    return all_files


if __name__ == '__main__':
    main()
