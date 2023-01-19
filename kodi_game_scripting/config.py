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

""" Libretro core configuration

    Override settings for specific libretro cores. """

# pylint: disable=bad-option-value, bad-whitespace, line-too-long
# flake8: noqa

GITHUB_ORGANIZATION = 'kodi-game'
GITHUB_ADDON_PREFIX = 'game.libretro.'

# core: {(Libretro repo, Makefile, Directory)}
ADDONS = {
    '2048':                      ('libretro-2048',              'Makefile.libretro', '.',                 'jni', {}),
    '3dengine':                  ('libretro-3dengine',          'Makefile',          '.',                 'jni', {}),
    '81':                        ('81-libretro',                'Makefile',          '.',                 'build/jni', {}),
    'atari800':                  ('libretro-atari800',          'Makefile',          '.',                 'jni', {}),
    'beetle-bsnes':              ('beetle-bsnes-libretro',      'Makefile',          '.',                 'jni', {'soname': 'mednafen_snes'}),
    'beetle-gba':                ('beetle-gba-libretro',        'Makefile',          '.',                 'jni', {'soname': 'mednafen_gba'}),
    'beetle-lynx':               ('beetle-lynx-libretro',       'Makefile',          '.',                 'jni', {'soname': 'mednafen_lynx'}),
    'beetle-ngp':                ('beetle-ngp-libretro',        'Makefile',          '.',                 'jni', {'soname': 'mednafen_ngp'}),
    'beetle-pce':                ('beetle-pce-libretro',        'Makefile',          '.',                 'jni', {'soname': 'mednafen_pce'}),
    'beetle-pce-fast':           ('beetle-pce-fast-libretro',   'Makefile',          '.',                 'jni', {'soname': 'mednafen_pce_fast'}),
    'beetle-pcfx':               ('beetle-pcfx-libretro',       'Makefile',          '.',                 'jni', {'soname': 'mednafen_pcfx'}),
    'beetle-psx':                ('beetle-psx-libretro',        'Makefile',          '.',                 'jni', {'soname': 'mednafen_psx'}),
    'beetle-saturn':             ('beetle-saturn-libretro',     'Makefile',          '.',                 'jni', {'soname': 'mednafen_saturn'}),
    'beetle-supergrafx':         ('beetle-supergrafx-libretro', 'Makefile',          '.',                 'jni', {'soname': 'mednafen_supergrafx'}),
    'beetle-vb':                 ('beetle-vb-libretro',         'Makefile',          '.',                 'jni', {'soname': 'mednafen_vb'}),
    'beetle-wswan':              ('beetle-wswan-libretro',      'Makefile',          '.',                 'jni', {'soname': 'mednafen_wswan'}),
    'bk':                        ('bk-emulator',                'Makefile.libretro', '.',                 'jni', {}),
    'blastem':                   ('blastem',                    'Makefile.libretro', '.',                 'android/jni', {'branch': 'libretro --', 'cmake_options': 'NOGL=1'}),
    'bluemsx':                   ('blueMSX-libretro',           'Makefile',          '.',                 'jni', {}),
    'bnes':                      ('bnes-libretro',              'Makefile',          '.',                 'libretro/jni', {}),
    'boom3':                     ('boom3',                      'Makefile',          'neo',               'jni', {}),
    'bsnes-mercury-accuracy':    ('bsnes-mercury',              'Makefile',          '.',                 'target-libretro/jni', {'soname': 'bsnes_mercury_accuracy', 'jnisoname': 'libretro_bsnes_mercury_accuracy', 'cmake_options': 'PROFILE=accuracy'}),
    'bsnes-mercury-balanced':    ('bsnes-mercury',              'Makefile',          '.',                 'target-libretro/jni', {'soname': 'bsnes_mercury_balanced', 'jnisoname': 'libretro_bsnes_mercury_balanced', 'cmake_options': 'PROFILE=balanced'}),
    'bsnes-mercury-performance': ('bsnes-mercury',              'Makefile',          '.',                 'target-libretro/jni', {'soname': 'bsnes_mercury_performance', 'jnisoname': 'libretro_bsnes_mercury_performance', 'cmake_options': 'PROFILE=performance'}),
    'bsnes2014-accuracy':        ('bsnes2014',                  'Makefile',          '.',                 'target-libretro/jni', {'branch': 'libretro --', 'soname': 'bsnes2014_accuracy', 'cmake_options': 'PROFILE=accuracy'}),
    'bsnes2014-balanced':        ('bsnes2014',                  'Makefile',          '.',                 'target-libretro/jni', {'branch': 'libretro --', 'soname': 'bsnes2014_balanced', 'cmake_options': 'PROFILE=balanced'}),
    'bsnes2014-performance':     ('bsnes2014',                  'Makefile',          '.',                 'target-libretro/jni', {'branch': 'libretro --', 'soname': 'bsnes2014_performance', 'cmake_options': 'PROFILE=performance'}),
    'cannonball':                ('cannonball',                 'Makefile',          '.',                 'jni', {}),
    'cap32':                     ('libretro-cap32',             'Makefile',          '.',                 'jni', {}),
    'chailove':                  ('libretro-chailove',          'Makefile',          '.',                 'jni', {'git_tag': True}),
    'craft':                     ('Craft',                      'Makefile.libretro', '.',                 'jni', {}),
    'crocods':                   ('libretro-crocods',           'Makefile',          '.',                 'jni', {}),
    'daphne':                    ('daphne',                     'Makefile',          '.',                 'jni', {}),
    'desmume':                   ('desmume',                    'Makefile.libretro', 'desmume/src/frontend/libretro', 'desmume/src/frontend/libretro/jni', {}),
    'desmume2015':               ('desmume2015',                'Makefile.libretro', 'desmume', 'desmume/src/libretro/jni', {}),
    'dinothawr':                 ('Dinothawr',                  'Makefile',          '.',                 'jni', {}),
    'dolphin':                   ('dolphin',                    '',                  '',                  '', {'cmake': True }),
    'dosbox':                    ('dosbox-libretro',            'Makefile.libretro', '.',                 'jni', {}),
    'dosbox-core':               ('dosbox-core',                'Makefile.libretro', 'libretro',          'libretro/jni', {'branch': 'libretro --', 'cmake_options': 'BUNDLED_SDL=1', 'soname': 'dosbox_core'}),
    'dosbox-pure':               ('dosbox-pure',                'Makefile',          '.',                 'jni', {'branch': 'main', 'soname': 'dosbox_pure'}),
    'ecwolf':                    ('ecwolf',                     'Makefile',          'src/libretro',       'src/libretro/jni', {}),
    'fbalpha2012':               ('fbalpha2012',                'makefile.libretro', 'svn-current/trunk', 'svn-current/trunk/projectfiles/libretro-android/jni', {}),
    'fbalpha2012-cps1':          ('fbalpha2012_cps1',           'makefile.libretro', '.',                 'projectfiles/libretro-android/jni', {'soname': 'fbalpha2012_cps1'}),
    'fbalpha2012-cps2':          ('fbalpha2012_cps2',           'makefile.libretro', '.',                 'projectfiles/libretro-android/jni', {'soname': 'fbalpha2012_cps2'}),
    'fbalpha2012-cps3':          ('fbalpha2012_cps3',           'makefile.libretro', 'svn-current/trunk', 'svn-current/trunk/projectfiles/libretro-android/jni', {'soname': 'fbalpha2012_cps3'}),
    'fbalpha2012-neogeo':        ('fbalpha2012_neogeo',         'makefile.libretro', '.',                 'projectfiles/libretro-android/jni', {'soname': 'fbalpha2012_neogeo'}),
    'fbneo':                     ('FBNeo',                      'Makefile',          'src/burner/libretro', 'src/burner/libretro/jni', {}),
    'fceumm':                    ('libretro-fceumm',            'Makefile',          '.',                 'jni', {}),
    'flycast':                   ('flycast',                    'Makefile',          '.',                 'jni', {}),
    'fmsx':                      ('fmsx-libretro',              'Makefile',          '.',                 'jni', {}),
    'freechaf':                  ('FreeChaF',                   'Makefile',          '.',                 'jni', {}),
    'freeintv':                  ('FreeIntv',                   'Makefile',          '.',                 'jni', {}),
    'frodo':                     ('frodo-libretro',             'Makefile',          '.',                 'jni', {}),
    #'fsuae':                     ('libretro-fsuae',             'Makefile.libretro', '.',                 'jni', {'branch': 'libretro-fsuae'}),  # Fails to build
    'fuse':                      ('fuse-libretro',              'Makefile',          '.',                 'build/jni', {}),
    'gambatte':                  ('gambatte-libretro',          'Makefile',          '.',                 'libgambatte/libretro/jni', {}),
    'gearboy':                   ('Gearboy',                    'Makefile',          'platforms/libretro', 'platforms/libretro/jni', {}),
    'genplus':                   ('Genesis-Plus-GX',            'Makefile.libretro', '.',                 'libretro/jni', {'soname': 'genesis_plus_gx'}),
    'genplus-wide':              ('Genesis-Plus-GX-Wide',       'Makefile.libretro', '.',                 'libretro/jni', {'soname': 'genesis_plus_gx_wide', 'branch': 'main'}),
    'gong':                      ('gong',                       'Makefile.libretro', '.',                 'jni', {}),  # TODO: No jni folder
    'gpsp':                      ('gpsp',                       'Makefile',          '.',                 'jni', {}),
    'gw':                        ('gw-libretro',                'Makefile',          '.',                 'build/jni', {}),
    'handy':                     ('libretro-handy',             'Makefile',          '.',                 'jni', {}),
    'hatari':                    ('hatari',                     'Makefile.libretro', '.',                 'libretro/jni', {}),
    'hbmame':                    ('hbmame-libretro',            'Makefile.libretro', '.',                 '3rdparty/SDL2/android-project/jni', {}),
    'lutro':                     ('libretro-lutro',             'Makefile',          '.',                 'jni', {}),
    'mame':                      ('mame',                       'Makefile.libretro', '.',                 'jni', {'cmake_options': 'PTR64=1'}),  # Huge and longrunning
    'mame2000':                  ('mame2000-libretro',          'Makefile',          '.',                 'jni', {}),
    'mame2003':                  ('mame2003-libretro',          'Makefile',          '.',                 'jni', {}),
    'mame2003_midway':           ('mame2003_midway',            'Makefile',          '.',                 'jni', {}),
    'mame2003_plus':             ('mame2003-plus-libretro',     'Makefile',          '.',                 'jni', {}),
    'mame2010':                  ('mame2010-libretro',          'Makefile',          '.',                 'jni', {'cmake_options': 'VRENDER=soft PTR64=1'}),  # Huge and longrunning
    'mame2015':                  ('mame2015-libretro',          'Makefile',          '.',                 'jni', {'cmake_options': 'PTR64=1 TARGET=mame'}),  # Huge and longrunning
    'mame2016':                  ('mame2016-libretro',          'Makefile.libretro', '.',                 '3rdparty/SDL2/android-project/jni', {'cmake_options': 'PTR64=1'}),  # Huge and longrunning
    'melonds':                   ('melonDS',                    'Makefile',          '.',                 'jni', {}),
    'meowpc98':                  ('libretro-meowPC98',          'Makefile.libretro', 'libretro',          'libretro/jni', {'soname': 'nekop2'}),
    'mesen':                     ('Mesen',                      'Makefile',          'Libretro',          'Libretro/jni', {}),
    'mesen-s':                   ('Mesen-S',                    'Makefile',          'Libretro',          'Libretro/jni', {}),
    'meteor':                    ('meteor-libretro',            'Makefile',          'libretro',          'libretro/jni', {}),
    'mgba':                      ('mgba',                       'Makefile',          '.',                 'libretro-build/jni', {}),
    'mrboom':                    ('Javanaise/mrboom-libretro',  'Makefile',          '.',                 'libretro/jni', {}),
    'mu':                        ('Mu',                         'Makefile.libretro', 'libretroBuildSystem', 'libretroBuildSystem/jni', {}),
    'mupen64plus-nx':            ('mupen64plus-libretro-nx',    'Makefile',          '.',                 'jni', {'soname': 'mupen64plus_next'}),
    'nestopia':                  ('nestopia',                   'Makefile',          'libretro',          'libretro/jni', {}),
    'neocd':                     ('neocd_libretro',             'Makefile',          '.',                 'jni', {}),
    'nx':                        ('nxengine-libretro',          'Makefile',          '.',                 'jni', {'soname': 'nxengine'}),
    'o2em':                      ('libretro-o2em',              'Makefile',          '.',                 'jni', {}),
    'oberon':                    ('oberon-risc-emu',            'Makefile.libretro', '.',                 'Libretro/jni', {}),
    'openlara':                  ('OpenLara',                   'Makefile',          'src/platform/libretro', 'src/platform/libretro/jni', {}),
    'opera':                     ('opera-libretro',             'Makefile',          '.',                 'jni', {}),
    'parallel_n64':              ('parallel-n64',               'Makefile',          '.',                 'jni', {}),
    'parallext':                 ('parallext',                  'Makefile',          '.',                 'libretro/jni', {'soname': 'parallel_n64'}),
    'pcem':                      ('libretro-pcem',              'Makefile.libretro', 'src',               'jni', {}),
    'pcsx-rearmed':              ('pcsx_rearmed',               'Makefile.libretro', '.',                 'jni', {'soname': 'pcsx_rearmed'}),
    'picodrive':                 ('picodrive',                  'Makefile.libretro', '.',                 'jni', {}),
    'pocketcdg':                 ('libretro-pocketcdg',         'Makefile',          '.',                 'jni', {}),
    'pokemini':                  ('PokeMini',                   'Makefile.libretro', '.',                 'jni', {}),
    'potator':                   ('potator',                    'Makefile' ,         ' platform/libretro', 'platform/libretro/jni', {}),
    'ppsspp':                    ('ppsspp',                     'Makefile',          'libretro',          'jni', {}),  # Longrunning, requires OpenGL
    'prboom':                    ('libretro-prboom',            'Makefile',          '.',                 'jni', {}),
    'prosystem':                 ('prosystem-libretro',         'Makefile',          '.',                 'jni', {}),
    'px68k':                     ('px68k-libretro',             'Makefile.libretro', '.',                 'libretro/jni', {}),
    'quasi88':                   ('quasi88-libretro',           'Makefile',          '.',                 'src/LIBRETRO/jni', {}),
    'quicknes':                  ('QuickNES_Core',              'Makefile',          '.',                 'jni', {}),
    'race':                      ('RACE',                       'Makefile',          '.',                 'jni', {}),
    'reminiscence':              ('REminiscence',               'Makefile',          '.',                 'jni', {}),
    'remotejoy':                 ('libretro-remotejoy',         'Makefile',          '.',                 'jni', {}),
    'retro8':                    ('retro8',                     'Makefile',          '.',                 'jni', {}),
    #'rustation':                 ('rustation-libretro',         'Makefile',          '.',                 'jni', {}),  # Checkout fails
    'sameboy':                   ('SameBoy',                    'Makefile',          'libretro',          'libretro/jni', {'branch': 'buildbot'}),
    'scummvm':                   ('kodi-game/scummvm',          'Makefile',          '.',                 'jni', {'branch': 'main'}),
    'smsplus-gx':                ('smsplus-gx',                 'Makefile.libretro', '.',                 'jni', {'soname': 'smsplus'}),
    'snes9x':                    ('snes9x',                     'Makefile',          'libretro',          'libretro/jni', {}),
    'snes9x2002':                ('snes9x2002',                 'Makefile',          '.',                 'jni', {}),
    'snes9x2010':                ('snes9x2010',                 'Makefile',          '.',                 'jni', {}),
    'stella':                    ('stella2014-libretro',        'Makefile',          '.',                 'jni', {'soname': 'stella2014'}),
    'supafaust':                 ('supafaust',                  'Makefile',          '.',                 'jni', {'soname': 'mednafen_supafaust'}),
    'swanstation':               ('swanstation',                '',                  '.',                 '', {'branch': 'main', 'cmake': True}),
    'tgbdual':                   ('tgbdual-libretro',           'Makefile',          '.',                 'jni', {}),
    'theodore':                  ('Zlika/theodore',             'Makefile',          '.',                  'jni', {}),
    'thepowdertoy':              ('kodi-game/ThePowderToy',     '',                  '',                  '', {'cmake': True, 'binary_dir': 'src', 'jnisoname': 'thepowdertoy_libretro_android'}),
    'tyrquake':                  ('tyrquake',                   'Makefile',          '.',                 'jni', {}),
    'uae':                       ('libretro-uae',               'Makefile',          '.',                 'jni', {'soname': 'puae'}),
    #'uae4arm':                   ('uae4arm-libretro',           'Makefile',          '.',                 'jni', {}),  # Fails to build on non arm system
    'uzem':                      ('libretro-uzem',              'Makefile.libretro', '.',                 'jni', {}),
    'vba-next':                  ('vba-next',                   'Makefile',          '.',                 'libretro/jni', {'soname': 'vba_next'}),
    'vbam':                      ('vbam-libretro',              'Makefile',          'src/libretro',      'src/libretro/jni', {}),
    'vecx':                      ('libretro-vecx',              'Makefile',          '.',                 'jni', {}),
    'vemulator':                 ('vemulator-libretro',         'Makefile',          '.',                 'jni', {}),
    'vice':                      ('vice-libretro',              'Makefile',          '.',                 'jni', {'soname': 'vice_x64'}),  # Settings broken for option API version 0
    'virtualjaguar':             ('virtualjaguar-libretro',     'Makefile',          '.',                 'jni', {}),
    'xmil':                      ('xmil-libretro',              'Makefile.libretro', 'libretro',          'libretro/jni', {'soname': 'x1'}),
    'xrick':                     ('xrick-libretro',             'Makefile.libretro', '.',                 'jni', {}),
    'yabause':                   ('yabause',                    'Makefile',          'yabause/src/libretro', 'yabause/src/libretro/jni', {}),
}
