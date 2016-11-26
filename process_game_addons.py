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
import datetime
import os
import multiprocessing
import shutil
import subprocess

import jinja2

import git_access
import libretro_ctypes

import config

ADDONS = config.ADDONS
DIR = os.path.dirname(os.path.realpath(__file__))


def main():
    """ Process Kodi Game addons and unify project files """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--game-addons-dir', dest='working_directory',
                        type=str, required=True,
                        help="Directory where the game addons reside")
    parser.add_argument('--compile', action="store_true",
                        help="Compile libretro cores and read system info")
    parser.add_argument('--kodi-source-dir', dest='kodi_directory',
                        type=str,
                        help="Kodi's source directory")
    parser.add_argument('--git', action="store_true",
                        help="Clone / reset libretro cores from GitHub")
    parser.add_argument('--filter', type=str, default='',
                        help="Filter games (e.g. nes)")

    args = parser.parse_args()

    if args.git:
        print("Cloning git repositories")
        gitaccess = git_access.Git()
        addon_filter = 'game.libretro' + \
            '.' + args.filter if args.filter else ''
        repos = gitaccess.get_repos('kodi-game', addon_filter)
        gitaccess.clone_repos(repos, os.path.abspath(args.working_directory))

    util = KodiGameAddons(args)
    util.process_directory(os.path.abspath(args.working_directory))


class KodiGameAddons:
    """ Process Kodi Game addons and unify project files """
    def __init__(self, args):
        """ Initialize instance """
        self._args = args
        self._template_dir = os.path.join(DIR, 'template')

        self._template_env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(self._template_dir),
            trim_blocks=True, lstrip_blocks=True)

    def process_directory(self, directory):
        """ Process a full directory with Kodi Game addons """
        directory = os.path.abspath(directory)

        # Loop over all addons in the working directory
        for addon in next(os.walk(directory))[1]:
            if self._args.filter in addon:
                self.process_addon(addon, directory)
            else:
                print("Skipping addon {} due to filter".format(addon))

    def process_addon(self, addon, directory):
        """ Process a single Kodi Game addon """
        print("Processing addon: {}".format(addon))
        addon_name = addon.rsplit('.', 1)[1]  # game.libretro.<addon_name>
        template_vars = {'game': {'name': addon_name},
                         'makefile': {},
                         'datetime': '{0:%Y-%m-%d %H:%Mi%z}'.format(
                             datetime.datetime.now()),
                         'system_info': {}, 'settings': []}

        # Read addon config from config.py
        try:
            addon_config = config.ADDONS[addon_name]
            template_vars['repo'] = addon_config[0]
            template_vars['makefile'] = {'file': addon_config[1],
                                         'dir': addon_config[2]}
            print("  Ussing config.py entry")
        except KeyError:
            print("  Addon has no (or incorrect) config.py entry")

        # First iteration: Makefiles
        self._process_addon_files(addon, directory, template_vars)

        # Compile addons to read info from built library
        if self._args.compile:
            self._process_addondescription_files(addon, template_vars)
            library_file = os.path.join(directory, addon, 'install',
                                        addon, '{}.so'.format(addon))
            self._compile_addon(addon, directory)
            try:
                library = libretro_ctypes.LibretroWrapper(library_file)
                template_vars['system_info'] = library.system_info
                template_vars['settings'] = sorted(library.variables,
                                                   key=lambda x: x.id)

                # Second iteration: Read info from built library
                self._process_addon_files(addon, directory, template_vars)
            except OSError:
                print("Failed to compile addon, output library not found.")

    def _process_addondescription_files(self, addon, template_vars):
        self._process_templates(
            os.path.join(DIR, 'template_description'),
            os.path.join(self._args.kodi_directory, 'project', 'cmake',
                         'addons', 'addons', addon), template_vars)

    def _process_addon_files(self, addon, directory, template_vars):
        self._process_templates(
            os.path.join(DIR, 'template'),
            os.path.join(directory, addon), template_vars)

    @classmethod
    def _process_templates(cls, template_dir, destination, template_vars):
        """ Process templates """
        template_env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(template_dir),
            trim_blocks=True, lstrip_blocks=True)

        # Loop over all templates
        for infile in list_all_files(template_dir):

            # Files may have templatized names
            if '{{' in infile and '}}' in infile:
                outfile = jinja2.Template(infile).render(template_vars)
            else:
                outfile = infile
            outfile_name, extension = os.path.splitext(outfile)

            # Create directories if necessary
            ensure_directory_exists(
                os.path.dirname(os.path.join(destination, outfile)))

            # Files that end with .j2 are templates
            if extension.startswith('.j2'):
                print("  Generating {}".format(outfile_name))
                template = template_env.get_template(infile)
                template.stream(template_vars).dump(
                    os.path.join(destination, outfile_name))

            # Other files are just copied
            else:
                print("     Copying {}".format(outfile_name))
                shutil.copyfile(os.path.join(template_dir, infile),
                                os.path.join(destination, outfile))

    def _compile_addon(self, addon, directory):
        """ Compile the addon in order to read system info from the binary """
        print(" Compiling addon")
        addon_dir = os.path.join(directory, addon)
        build_dir = os.path.join(addon_dir, 'build')
        install_dir = os.path.join(addon_dir, 'install')
        cmake_dir = os.path.join(self._args.kodi_directory,
                                 'project', 'cmake', 'addons')

        ensure_directory_exists(build_dir, clean=True)
        subprocess.run([os.environ.get('CMAKE', 'cmake'),
                        '-DADDONS_TO_BUILD={}$'.format(addon),
                        '-DADDON_SRC_PREFIX={}'.format(directory),
                        '-DCMAKE_BUILD_TYPE=Debug', '-DPACKAGE_ZIP=1',
                        '-DCMAKE_INSTALL_PREFIX={}'.format(install_dir),
                        cmake_dir], cwd=build_dir)
        subprocess.run([os.environ.get('CMAKE', 'cmake'), '--build', '.',
                        '--', '-j{}'.format(multiprocessing.cpu_count())],
                       cwd=build_dir)


def ensure_directory_exists(path, clean=False):
    """ Ensure that the given path exists """
    try:
        if clean and os.path.exists(path):
            shutil.rmtree(path)

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
