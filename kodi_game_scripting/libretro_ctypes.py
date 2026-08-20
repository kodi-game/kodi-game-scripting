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

""" Libretro Wrapper """

import collections
import ctypes
import json
import os
import re
import subprocess
import sys
import tempfile

from .utils import xstr


class LibretroWrapper:
    """ Wraps a libretro core giving access to system info.

        Use attributes system_info and settings to access this information. """

    EXT = 'dylib' if sys.platform == 'darwin' else 'so'
    LDD_CMD = ['otool', '-L'] if sys.platform == 'darwin' else ['ldd']

    class RetroSystemInfo(ctypes.Structure):
        """ struct retro_system_type """
        _fields_ = [
            ('library_name', ctypes.c_char_p),
            ('library_version', ctypes.c_char_p),
            ('valid_extensions', ctypes.c_char_p),
            ('need_fullpath', ctypes.c_bool),
            ('block_extract', ctypes.c_bool)
        ]

    class SystemInfo():
        """ Wrapped system info """
        def __init__(self, retro_system_info=None):
            self.name = xstr(retro_system_info.library_name)
            self.version = xstr(retro_system_info.library_version)
            self.extensions = [ext for ext in xstr(
                retro_system_info.valid_extensions).split('|')
                               if ext]
            self.need_fullpath = retro_system_info.need_fullpath
            self.block_extract = retro_system_info.block_extract
            self.supports_no_game = False
            self.supports_disc_control = False

        def __getitem__(self, item):
            return getattr(self, item)

        def __repr__(self):
            return '(name={}, version={}, extensions={}, need_fullpath={},' \
                   ' block_extract={}, supports_no_game={}, supports_disc_control={})'.format(
                       self.name, self.version, self.extensions,
                       self.need_fullpath, self.block_extract,
                       self.supports_no_game, self.supports_disc_control)

    class RetroVariable(ctypes.Structure):
        """ struct libretro_variable """
        _fields_ = [
            ('key', ctypes.c_char_p),
            ('value', ctypes.c_char_p)
        ]

    RETRO_ENVIRONMENT_SET_DISK_CONTROL_INTERFACE = 13
    RETRO_ENVIRONMENT_SET_DISK_CONTROL_EXT_INTERFACE = 58

    def __init__(self, library_path):
        lib = ctypes.cdll.LoadLibrary(library_path)

        # retro_get_system_info
        retro_get_system_info = lib.retro_get_system_info
        retro_get_system_info.argtypes = \
            [ctypes.POINTER(self.RetroSystemInfo)]
        retro_get_system_info.restype = None

        system_info = self.RetroSystemInfo()
        retro_get_system_info(ctypes.byref(system_info))
        self.system_info = self.SystemInfo(system_info)

        # retro_set_environment
        retro_environment_t = ctypes.CFUNCTYPE(
            ctypes.c_bool, ctypes.c_uint, ctypes.c_void_p)

        retro_set_environment = lib.retro_set_environment
        retro_set_environment.argtypes = [retro_environment_t]
        retro_set_environment.restype = None
        self.variables = []

        def retro_environment_cb(cb_type, arg, outer=self):
            """ Libretro environment callback """
            if cb_type == 18:  # RETRO_ENVIRONMENT_SET_SUPPORT_NO_GAME
                result = ctypes.cast(arg, ctypes.POINTER(ctypes.c_bool))[0]
                outer.system_info.supports_no_game = result
            elif cb_type == 16:  # RETRO_ENVIRONMENT_SET_VARIABLES
                index = 0
                while True:
                    var = ctypes.cast(arg, ctypes.POINTER(
                        self.RetroVariable))[index]
                    index += 1
                    if var.key is None and var.value is None:
                        break
                    outer.variables.append(outer.parse_libretro_variable(var))
            elif cb_type == self.RETRO_ENVIRONMENT_SET_DISK_CONTROL_INTERFACE:
                outer.system_info.supports_disc_control = True
            elif cb_type == self.RETRO_ENVIRONMENT_SET_DISK_CONTROL_EXT_INTERFACE:
                outer.system_info.supports_disc_control = True

        retro_environment_cb = retro_environment_t(retro_environment_cb)
        retro_set_environment(retro_environment_cb)

        self.system_info.supports_disc_control = self.probe_disc_control(
            library_path)

        # opengl linkage
        self.opengl_linkage = self.has_opengl_linkage(library_path)

    @classmethod
    def parse_libretro_variable(cls, variable):
        """ Parse variable into Variable(id, desc, values, default) """
        key = xstr(variable.key)
        description, values = xstr(variable.value).split(';', 1)
        values = values.strip().split('|')
        default = values[0]

        var = collections.namedtuple('Variable',
                                     'id description values default')
        return var(key, description, values, default)

    @classmethod
    def has_opengl_linkage(cls, library_path):
        """ Check if the library links opengl """
        ldd_output = subprocess.run(
            cls.LDD_CMD + [library_path], stdout=subprocess.PIPE, check=True)
        return bool(re.search(r'(?:libgl|opengl)',
                              str(ldd_output.stdout, 'utf-8'), re.IGNORECASE))

    @classmethod
    def probe_disc_control(cls, library_path):
        """Probe disk control support in a helper subprocess.

        Some cores only register disk control callbacks in retro_init(), and
        some cores crash inside retro_init(). Running this probe out-of-process
        prevents a crashing core from aborting the parent while preserving a
        positive callback result if it fired before the crash.
        """
        result_path = None
        try:
            with tempfile.NamedTemporaryFile(delete=False) as result_file:
                result_path = result_file.name

            subprocess.run(
                [sys.executable, '-m', 'kodi_game_scripting.libretro_ctypes',
                 '--probe-disc-control', library_path, result_path],
                check=False)
            return cls._read_probe_result(result_path)
        except (OSError, subprocess.SubprocessError):
            return False
        finally:
            if result_path:
                try:
                    os.unlink(result_path)
                except OSError:
                    pass

    @staticmethod
    def _read_probe_result(result_path):
        """Read probe result JSON from helper process."""
        try:
            with open(result_path, 'r', encoding='utf-8') as result_file:
                return bool(json.load(result_file).get('supports_disc_control'))
        except (OSError, ValueError, AttributeError):
            return False


def _write_probe_result(result_path, supports_disc_control):
    """Persist probe result to JSON and fsync for crash resilience."""
    with open(result_path, 'w', encoding='utf-8') as result_file:
        json.dump({'supports_disc_control': supports_disc_control}, result_file)
        result_file.flush()
        os.fsync(result_file.fileno())


def probe_disc_control_subprocess(library_path, result_path):
    """Entrypoint for probing disk control callbacks in an isolated process."""
    supports_disc_control = False

    lib = ctypes.cdll.LoadLibrary(library_path)

    class RetroSystemInfo(ctypes.Structure):
        """ struct retro_system_info """
        _fields_ = [
            ('library_name', ctypes.c_char_p),
            ('library_version', ctypes.c_char_p),
            ('valid_extensions', ctypes.c_char_p),
            ('need_fullpath', ctypes.c_bool),
            ('block_extract', ctypes.c_bool)
        ]

    retro_get_system_info = lib.retro_get_system_info
    retro_get_system_info.argtypes = [ctypes.POINTER(RetroSystemInfo)]
    retro_get_system_info.restype = None
    system_info = RetroSystemInfo()
    retro_get_system_info(ctypes.byref(system_info))

    retro_environment_t = ctypes.CFUNCTYPE(ctypes.c_bool, ctypes.c_uint,
                                           ctypes.c_void_p)

    def retro_environment_cb(cb_type, arg):
        del arg
        nonlocal supports_disc_control
        if cb_type in (
                LibretroWrapper.RETRO_ENVIRONMENT_SET_DISK_CONTROL_INTERFACE,
                LibretroWrapper.RETRO_ENVIRONMENT_SET_DISK_CONTROL_EXT_INTERFACE):
            supports_disc_control = True
            _write_probe_result(result_path, True)
        return False

    retro_set_environment = lib.retro_set_environment
    retro_set_environment.argtypes = [retro_environment_t]
    retro_set_environment.restype = None
    retro_environment_cb = retro_environment_t(retro_environment_cb)
    retro_set_environment(retro_environment_cb)

    retro_init = lib.retro_init
    retro_init.argtypes = []
    retro_init.restype = None
    retro_init()

    retro_deinit = getattr(lib, 'retro_deinit', None)
    if retro_deinit:
        retro_deinit.argtypes = []
        retro_deinit.restype = None
        retro_deinit()

    _write_probe_result(result_path, supports_disc_control)


if __name__ == '__main__':  # pragma: no cover
    if len(sys.argv) == 4 and sys.argv[1] == '--probe-disc-control':
        probe_disc_control_subprocess(sys.argv[2], sys.argv[3])
    else:
        LIB = LibretroWrapper(sys.argv[1])
