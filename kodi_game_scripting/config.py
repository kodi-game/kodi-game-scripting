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

""" Libretro core configuration

    Override settings for specific libretro cores. """

# pylint: disable=bad-whitespace, line-too-long
# flake8: noqa

GITHUB_ORGANIZATION = 'kodi-game'
GITHUB_ADDON_PREFIX = 'game.libretro.'

# core: {(Libretro repo, Makefile, Directory)}
ADDONS = {
    '2048':                      ('libretro-2048',              'Makefile.libretro', '.'),
    '4do':                       ('4do-libretro',               'Makefile',          '.'),
    #'beetle-bsnes':              ('beetle-bsnes-libretro',      'Makefile',          '.', {'soname': 'mednafen_bsnes'}),  # Undefined reference
    'beetle-gba':                ('beetle-gba-libretro',        'Makefile',          '.', {'soname': 'mednafen_gba'}),
    'beetle-lynx':               ('beetle-lynx-libretro',       'Makefile',          '.', {'soname': 'mednafen_lynx'}),
    'beetle-ngp':                ('beetle-ngp-libretro',        'Makefile',          '.', {'soname': 'mednafen_ngp'}),
    'beetle-pce-fast':           ('beetle-pce-fast-libretro',   'Makefile',          '.', {'soname': 'mednafen_pce_fast'}),
    #'beetle-pcfx':               ('beetle-pcfx-libretro',       'Makefile',          '.', {'soname': 'mednafen_pcfx'}),  # Undefined reference
    'beetle-psx':                ('beetle-psx-libretro',        'Makefile',          '.', {'soname': 'mednafen_psx'}),
    #'beetle-supergrafx':         ('beetle-supergrafx-libretro', 'Makefile',          '.', {'soname': 'mednafen_supergrafx'}),  # Undefined reference
    'beetle-vb':                 ('beetle-vb-libretro',         'Makefile',          '.', {'soname': 'mednafen_vb'}),
    'beetle-wswan':              ('beetle-wswan-libretro',      'Makefile',          '.', {'soname': 'mednafen_wswan'}),
    'bluemsx':                   ('blueMSX-libretro',           'Makefile',          '.'),
    'bnes':                      ('bnes-libretro',              'Makefile',          '.'),
    'bsnes-mercury-accuracy':    ('bsnes-mercury',              'Makefile',          '.', {'binary_dir': 'out', 'soname': 'bsnes_mercury_accuracy', 'cmake_options': 'profile=accuracy'}),
    'bsnes-mercury-balanced':    ('bsnes-mercury',              'Makefile',          '.', {'binary_dir': 'out', 'soname': 'bsnes_mercury_balanced', 'cmake_options': 'profile=balanced'}),
    'bsnes-mercury-performance': ('bsnes-mercury',              'Makefile',          '.', {'binary_dir': 'out', 'soname': 'bsnes_mercury_performance', 'cmake_options': 'profile=performance'}),
    'cap32':                     ('libretro-cap32',             'Makefile',          '.'),
    'desmume':                   ('desmume-libretro',           'Makefile.libretro', '.'),
    #'dolphin':                   ('dolphin',                    'Makefile',          'libretro'),  # Fails to compile, enet.h not found
    'dinothawr':                 ('Dinothawr',                  'Makefile',          '.'),
    'dosbox':                    ('dosbox-libretro',            'Makefile.libretro', '.'),
    'fbalpha2012':               ('fbalpha2012',                'makefile.libretro', 'svn-current/trunk'),  # fba
    'fceumm':                    ('libretro-fceumm',            'Makefile',          '.'),
    'fmsx':                      ('fmsx-libretro',              'Makefile',          '.'),
    'fuse':                      ('fuse-libretro',              'Makefile',          '.'),
    'gambatte':                  ('gambatte-libretro',          'Makefile',          '.'),
    'genplus':                   ('Genesis-Plus-GX',            'Makefile',          '.', {'soname': 'genesis_plus_gx'}),
    'gw':                        ('gw-libretro',                'Makefile',          '.'),
    'handy':                     ('libretro-handy',             'Makefile',          '.'),
    'hatari':                    ('hatari',                     'Makefile.libretro', '.'),
    'lutro':                     ('libretro-lutro',             'Makefile',          '.'),
    #'mame':                      ('mame',                       'Makefile.libretro', '.'),  # Huge checkout, fails to build
    'meteor':                    ('meteor-libretro',            'Makefile',          'libretro'),
    'mgba':                      ('mgba',                       'Makefile',          '.'),
    'mupen64plus':               ('mupen64plus-libretro',       'Makefile',          '.'),
    'nestopia':                  ('nestopia',                   'Makefile',          'libretro'),
    'nx':                        ('nxengine-libretro',          'Makefile',          '.', {'soname': 'nxengine'}),
    'o2em':                      ('libretro-o2em',              'Makefile',          '.'),
    'pcem':                      ('libretro-pcem',              'Makefile.libretro', 'src'),
    'pcsx-rearmed':              ('pcsx_rearmed',               'Makefile.libretro', '.', {'soname': 'pcsx_rearmed'}),
    'picodrive':                 ('picodrive',                  'Makefile.libretro', '.'),
    #'ppsspp':                    ('libretro-ppsspp',            'Makefile',          'libretro'),  # Longrunning, working
    'prboom':                    ('libretro-prboom',            'Makefile',          '.'),
    'prosystem':                 ('prosystem-libretro',         'Makefile',          '.'),
    'quicknes':                  ('QuickNES_Core',              'Makefile',          '.'),
    'reicast':                   ('reicast-emulator',           'Makefile',          '.'),
    #'rustation':                 ('rustation-libretro',         'Makefile',          '.'),  # Checkout fails
    #'scummvm':                   ('scummvm',                    'Makefile',          'backends/platform/libretro/build', {'binary_dir': 'backends/platform/libretro/build'}),  # Longrunning, working
    'snes9x':                    ('snes9x',                     'Makefile',          'libretro'),
    'snes9x2002':                ('snes9x2002',                 'Makefile',          '.'),
    'snes9x2010':                ('snes9x2010',                 'Makefile',          '.'),
    'stella':                    ('stella-libretro',            'Makefile',          '.'),
    'tgbdual':                   ('tgbdual-libretro',           'Makefile',          '.'),
    'tyrquake':                  ('tyrquake',                   'Makefile',          '.'),
    'vbam':                      ('vbam-libretro',              'Makefile',          'src/libretro'),
    'vba-next':                  ('vba-next',                   'Makefile',          '.', {'soname': 'vba_next'}),
    'vecx':                      ('libretro-vecx',              'Makefile',          '.'),
    'yabause':                   ('yabause',                    'Makefile',          'libretro'),
    'virtualjaguar':             ('virtualjaguar-libretro',     'Makefile',          '.')
}
