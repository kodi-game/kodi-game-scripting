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

# core: {(Libretro repo, Makefile, Directory)}
ADDONS = {
    '2048':                      ('libretro-2048',              'Makefile.libretro', '.'),
    '4do':                       ('4do-libretro',               'Makefile',          '.'),
    'beetle-bsnes':              ('beetle-bsnes-libretro',      'Makefile',          '.'),
    'beetle-gba':                ('beetle-gba-libretro',        'Makefile',          '.'),
    'beetle-lynx':               ('beetle-lynx-libretro',       'Makefile',          '.'),
    'beetle-ngp':                ('beetle-ngp-libretro',        'Makefile',          '.'),
    'beetle-pce-fast':           ('beetle-pce-fast-libretro',   'Makefile',          '.'),
    'beetle-pcfx':               ('beetle-pcfx-libretro',       'Makefile',          '.'),
    'beetle-psx':                ('beetle-psx-libretro',        'Makefile',          '.'),
    'beetle-supergrafx':         ('beetle-supergrafx-libretro', 'Makefile',          '.'),
    'beetle-vb':                 ('beetle-vb-libretro',         'Makefile',          '.'),
    'beetle-wswan':              ('beetle-wswan-libretro',      'Makefile',          '.'),
    'bluemsx':                   ('blueMSX-libretro',           'Makefile',          '.'),
    'bnes':                      ('bnes-libretro',              'Makefile',          '.'),
    'bsnes-mercury-accuracy':    ('bsnes-mercury',              'Makefile',          '.'),
    'bsnes-mercury-balanced':    ('bsnes-mercury',              'Makefile',          '.'),
    'bsnes-mercury-performance': ('bsnes-mercury',              'Makefile',          '.'),
    'cap32':                     ('libretro-cap32',             'Makefile',          '.'),
    'desmume':                   ('desmume-libretro',           'Makefile.libretro', '.'),
    'dolphin':                   ('dolphin',                    'Makefile',          'libretro.'),
    'dinothawr':                 ('Dinothawr',                  'Makefile',          '.'),
    'dosbox':                    ('dosbox-libretro',            'Makefile.libretro', '.'),
    'fbalpha2012':               ('fbalpha2012',                'makefile.libretro', 'svn-current/trunk'),  # fba
    'fceumm':                    ('libretro-fceumm',            'Makefile',          '.'),
    'fmsx':                      ('fmsx-libretro',              'Makefile',          '.'),
    'fuse':                      ('fuse-libretro',              'Makefile',          '.'),
    'gambatte':                  ('gambatte-libretro',          'Makefile',          '.'),
    'genplus':                   ('Genesis-Plus-GX',            'Makefile',          '.'),
    'gw':                        ('gw-libretro',                'Makefile',          '.'),
    'handy':                     ('libretro-handy',             'Makefile',          '.'),
    'hatari':                    ('hatari',                     'Makefile.libretro', '.'),
    'lutro':                     ('libretro-lutro',             'Makefile',          '.'),
    'mame':                      ('mame',                       'Makefile.libretro', '.'),
    'meteor':                    ('meteor-libretro',            'Makefile',          'libretro'),
    'mgba':                      ('mgba',                       'Makefile',          '.'),
    'mupen64plus':               ('mupen64plus-libretro',       'Makefile',          '.'),
    'nestopia':                  ('nestopia',                   'Makefile',          '.'),
    'nx':                        ('nxengine-libretro',          'Makefile',          '.'),
    'o2em':                      ('libretro-o2em',              'Makefile',          '.'),
    'pcem':                      ('libretro-pcem',              'Makefile.libretro', 'src'),
    'pcsx-rearmed':              ('pcsx_rearmed',               'Makefile',          '.'),
    'picodrive':                 ('picodrive',                  'Makefile',          '.'),
    'ppsspp':                    ('libretro-ppsspp',            'Makefile',          'libretro'),
    'prboom':                    ('libretro-prboom',            'Makefile',          '.'),
    'prosystem':                 ('prosystem-libretro',         'Makefile',          '.'),
    'quicknes':                  ('QuickNES_Core',              'Makefile',          '.'),
    'reicast':                   ('reicast-emulator',           'Makefile',          '.'),
    'rustation':                 ('rustation-libretro',         'Makefile',          '.'),
    'scummvm':                   ('scummvm',                    'Makefile',          'backends/platform/libretro/build'),
    'snes9x':                    ('snes9x',                     'Makefile',          '.'),
    'snes9x2002':                ('snes9x2002',                 'Makefile',          '.'),
    'snes9x2010':                ('snes9x2010',                 'Makefile',          '.'),
    'stella':                    ('stella-libretro',            'Makefile',          '.'),
    'tgbdual':                   ('tgbdual-libretro',           'Makefile',          '.'),
    'tyrquake':                  ('tyrquake',                   'Makefile',          '.'),
    'vbam':                      ('vbam-libretro',              'Makefile',          'src/libretro'),
    'vba-next':                  ('vba-next',                   'Makefile',          '.'),
    'vecx':                      ('libretro-vecx',              'Makefile',          '.'),
    'yabause':                   ('yabause',                    'Makefile',          'libretro'),
    'virtualjaguar':             ('virtualjaguar-libretro',     'Makefile',          '.')
}
