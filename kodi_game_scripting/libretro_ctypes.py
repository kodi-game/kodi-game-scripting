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
from enum import IntEnum
import json
import os
import re
import subprocess
import sys
import tempfile


# Environment commands we answer or record. See libretro.h.
RETRO_ENVIRONMENT_SET_VARIABLES = 16
RETRO_ENVIRONMENT_SET_SUPPORT_NO_GAME = 18
RETRO_ENVIRONMENT_SET_DISK_CONTROL_INTERFACE = 13
RETRO_ENVIRONMENT_SET_DISK_CONTROL_EXT_INTERFACE = 58
RETRO_ENVIRONMENT_GET_CORE_OPTIONS_VERSION = 52
RETRO_ENVIRONMENT_SET_CORE_OPTIONS = 53
RETRO_ENVIRONMENT_SET_CORE_OPTIONS_INTL = 54
RETRO_ENVIRONMENT_SET_CORE_OPTIONS_V2 = 67
RETRO_ENVIRONMENT_SET_CORE_OPTIONS_V2_INTL = 68
RETRO_ENVIRONMENT_GET_VARIABLE = 15
RETRO_ENVIRONMENT_SET_PIXEL_FORMAT = 10
RETRO_ENVIRONMENT_GET_LOG_INTERFACE = 27
RETRO_ENVIRONMENT_GET_MESSAGE_INTERFACE_VERSION = 59
RETRO_ENVIRONMENT_GET_SYSTEM_DIRECTORY = 9
RETRO_ENVIRONMENT_GET_SAVE_DIRECTORY = 31

# Opt-in directory for cores that build their option lists from what is on
# disk and register nothing when they find none. Unset, the probe declines the
# request exactly as before.
SYSTEM_DIRECTORY_ENV = 'KGS_SYSTEM_DIRECTORY'

RETRO_ENVIRONMENT_GET_LANGUAGE = 39

# The RETRO_LANGUAGE_* values a core is handed. Spelled out rather than taken
# from position, because the number is the ABI: a core picks its table with it.


class RetroLanguage(IntEnum):
    """ enum retro_language """
    ENGLISH = 0
    JAPANESE = 1
    FRENCH = 2
    SPANISH = 3
    GERMAN = 4
    ITALIAN = 5
    DUTCH = 6
    PORTUGUESE_BRAZIL = 7
    PORTUGUESE_PORTUGAL = 8
    RUSSIAN = 9
    KOREAN = 10
    CHINESE_TRADITIONAL = 11
    CHINESE_SIMPLIFIED = 12
    ESPERANTO = 13
    POLISH = 14
    VIETNAMESE = 15
    ARABIC = 16
    GREEK = 17
    TURKISH = 18
    SLOVAK = 19
    PERSIAN = 20
    HEBREW = 21
    ASTURIAN = 22
    FINNISH = 23
    INDONESIAN = 24
    SWEDISH = 25
    UKRAINIAN = 26
    CZECH = 27
    CATALAN_VALENCIA = 28
    CATALAN = 29
    BRITISH_ENGLISH = 30
    HUNGARIAN = 31
    BELARUSIAN = 32
    GALICIAN = 33
    NORWEGIAN = 34
    IRISH = 35
    THAI = 36

    @property
    def libretro_name(self):
        """ The name libretro writes, e.g. "portuguese_brazil" """
        return self.name.lower()


# The language each RETRO_LANGUAGE_* value means, as a BCP 47 tag. This is the
# layer to reason in: libretro's enum and Kodi's resource directories are both
# naming systems of their own, and neither survives contact with the other.
# "zh-Hant" is Traditional Chinese script, which is what libretro describes,
# where Kodi happens to file it under a Taiwan locale.
RETRO_LANGUAGE_TAGS = {
    RetroLanguage.ENGLISH: 'en',
    RetroLanguage.JAPANESE: 'ja',
    RetroLanguage.FRENCH: 'fr',
    RetroLanguage.SPANISH: 'es',
    RetroLanguage.GERMAN: 'de',
    RetroLanguage.ITALIAN: 'it',
    RetroLanguage.DUTCH: 'nl',
    RetroLanguage.PORTUGUESE_BRAZIL: 'pt-BR',
    RetroLanguage.PORTUGUESE_PORTUGAL: 'pt-PT',
    RetroLanguage.RUSSIAN: 'ru',
    RetroLanguage.KOREAN: 'ko',
    RetroLanguage.CHINESE_TRADITIONAL: 'zh-Hant',
    RetroLanguage.CHINESE_SIMPLIFIED: 'zh-Hans',
    RetroLanguage.ESPERANTO: 'eo',
    RetroLanguage.POLISH: 'pl',
    RetroLanguage.VIETNAMESE: 'vi',
    RetroLanguage.ARABIC: 'ar',
    RetroLanguage.GREEK: 'el',
    RetroLanguage.TURKISH: 'tr',
    RetroLanguage.SLOVAK: 'sk',
    RetroLanguage.PERSIAN: 'fa',
    RetroLanguage.HEBREW: 'he',
    RetroLanguage.ASTURIAN: 'ast',
    RetroLanguage.FINNISH: 'fi',
    RetroLanguage.INDONESIAN: 'id',
    RetroLanguage.SWEDISH: 'sv',
    RetroLanguage.UKRAINIAN: 'uk',
    RetroLanguage.CZECH: 'cs',
    RetroLanguage.CATALAN_VALENCIA: 'ca-valencia',
    RetroLanguage.CATALAN: 'ca',
    RetroLanguage.BRITISH_ENGLISH: 'en-GB',
    RetroLanguage.HUNGARIAN: 'hu',
    RetroLanguage.BELARUSIAN: 'be',
    RetroLanguage.GALICIAN: 'gl',
    RetroLanguage.NORWEGIAN: 'no',
    RetroLanguage.IRISH: 'ga',
    RetroLanguage.THAI: 'th',
}

_TAG_BY_LIBRETRO_NAME = {language.libretro_name: tag
                         for language, tag in RETRO_LANGUAGE_TAGS.items()}


def language_tag(libretro_name):
    """ The BCP 47 tag for a libretro language name, or None if unknown """
    return _TAG_BY_LIBRETRO_NAME.get(libretro_name)


# The core options version we tell cores the frontend speaks
CORE_OPTIONS_VERSION = 2

# struct retro_core_option_v2_definition::values is a fixed-size array
RETRO_NUM_CORE_OPTION_VALUES_MAX = 128

# A core that hangs in retro_init() must not hang the whole run
PROBE_TIMEOUT_SECONDS = 60


class RetroSystemInfo(ctypes.Structure):
    """ struct retro_system_info """
    _fields_ = [
        ('library_name', ctypes.c_char_p),
        ('library_version', ctypes.c_char_p),
        ('valid_extensions', ctypes.c_char_p),
        ('need_fullpath', ctypes.c_bool),
        ('block_extract', ctypes.c_bool)
    ]


RETRO_LOG_PRINTF_T = ctypes.CFUNCTYPE(None, ctypes.c_int, ctypes.c_char_p)


class RetroLogCallback(ctypes.Structure):
    """ struct retro_log_callback """
    _fields_ = [('log', RETRO_LOG_PRINTF_T)]


class RetroVariable(ctypes.Structure):
    """ struct retro_variable """
    _fields_ = [
        ('key', ctypes.c_char_p),
        ('value', ctypes.c_char_p)
    ]


class RetroCoreOptionValue(ctypes.Structure):
    """ struct retro_core_option_value """
    _fields_ = [
        ('value', ctypes.c_char_p),
        ('label', ctypes.c_char_p)
    ]


class RetroCoreOptionDefinition(ctypes.Structure):
    """ struct retro_core_option_definition (core options v1) """
    _fields_ = [
        ('key', ctypes.c_char_p),
        ('desc', ctypes.c_char_p),
        ('info', ctypes.c_char_p),
        ('values', RetroCoreOptionValue * RETRO_NUM_CORE_OPTION_VALUES_MAX),
        ('default_value', ctypes.c_char_p)
    ]


class RetroCoreOptionsIntl(ctypes.Structure):
    """ struct retro_core_options_intl """
    _fields_ = [
        ('us', ctypes.POINTER(RetroCoreOptionDefinition)),
        ('local', ctypes.POINTER(RetroCoreOptionDefinition))
    ]


class RetroCoreOptionV2Category(ctypes.Structure):
    """ struct retro_core_option_v2_category """
    _fields_ = [
        ('key', ctypes.c_char_p),
        ('desc', ctypes.c_char_p),
        ('info', ctypes.c_char_p)
    ]


class RetroCoreOptionV2Definition(ctypes.Structure):
    """ struct retro_core_option_v2_definition """
    _fields_ = [
        ('key', ctypes.c_char_p),
        ('desc', ctypes.c_char_p),
        ('desc_categorized', ctypes.c_char_p),
        ('info', ctypes.c_char_p),
        ('info_categorized', ctypes.c_char_p),
        ('category_key', ctypes.c_char_p),
        ('values', RetroCoreOptionValue * RETRO_NUM_CORE_OPTION_VALUES_MAX),
        ('default_value', ctypes.c_char_p)
    ]


class RetroCoreOptionsV2(ctypes.Structure):
    """ struct retro_core_options_v2 """
    _fields_ = [
        ('categories', ctypes.POINTER(RetroCoreOptionV2Category)),
        ('definitions', ctypes.POINTER(RetroCoreOptionV2Definition))
    ]


class RetroCoreOptionsV2Intl(ctypes.Structure):
    """ struct retro_core_options_v2_intl """
    _fields_ = [
        ('us', ctypes.POINTER(RetroCoreOptionsV2)),
        ('local', ctypes.POINTER(RetroCoreOptionsV2))
    ]


def _pair_strings(english, localised):
    """ Match a core's translated strings to the English they stand in for

    Keyed on the English text, because that is what the string table hands
    IDs out against: a translation is only useful against the string it
    translates, not against the option it came from. """
    paired = {}

    def add(source, target):
        if source and target and source != target:
            paired[source] = target

    for name in ('options', 'categories'):
        by_key = {item['key']: item for item in localised.get(name, [])}
        for item in english.get(name, []):
            other = by_key.get(item['key'])
            if other is None:
                continue
            add(item.get('description'), other.get('description'))
            add(item.get('info'), other.get('info'))
            labels = {value['value']: value.get('label')
                      for value in other.get('values', [])}
            for value in item.get('values', []):
                add(value.get('label'), labels.get(value['value']))

    return paired


def _str(char_p):
    """ Decode a char* that may be NULL """
    return char_p.decode('utf-8', 'replace') if char_p else ''


class LibretroWrapper:
    """ Wraps a libretro core giving access to system info.

        Use attributes system_info, options and categories to access this
        information.

        The core is loaded in a helper process: cores are third-party code
        that may crash or hang while registering their options, and that must
        not take the run down with them. """

    EXT = 'dylib' if sys.platform == 'darwin' else 'so'
    LDD_CMD = ['otool', '-L'] if sys.platform == 'darwin' else ['ldd']

    Option = collections.namedtuple(
        'Option', 'id description info category values default')
    OptionValue = collections.namedtuple('OptionValue', 'value label')
    Category = collections.namedtuple('Category', 'key description info')

    class SystemInfo():
        """ Wrapped system info """
        def __init__(self, system_info):
            self.name = system_info['name']
            self.version = system_info['version']
            self.extensions = [ext for ext in system_info['extensions'] if ext]
            self.need_fullpath = system_info['need_fullpath']
            self.block_extract = system_info['block_extract']
            self.supports_no_game = system_info['supports_no_game']
            self.supports_disc_control = system_info['supports_disc_control']

        def __getitem__(self, item):
            return getattr(self, item)

        def __repr__(self):
            return '(name={}, version={}, extensions={}, need_fullpath={},' \
                   ' block_extract={}, supports_no_game={}, supports_disc_control={})'.format(
                       self.name, self.version, self.extensions,
                       self.need_fullpath, self.block_extract,
                       self.supports_no_game, self.supports_disc_control)

    def __init__(self, library_path):
        probe_result, reason = self.probe(library_path)
        if probe_result is None:
            raise OSError(f"Failed to probe {library_path}: {reason}")

        self.system_info = self.SystemInfo(probe_result['system_info'])
        self.options = [
            self.Option(
                option['key'], option['description'], option['info'],
                option['category'],
                [self.OptionValue(value['value'], value['label'])
                 for value in option['values']],
                option['default'])
            for option in probe_result['options']]
        self.categories = [
            self.Category(category['key'], category['description'],
                          category['info'])
            for category in probe_result['categories']]

        # {language: {english text: translated text}}, for the languages the
        # core carries a table for
        self.translations = self._probe_translations(
            library_path, probe_result)

        # opengl linkage
        self.opengl_linkage = self.has_opengl_linkage(library_path)

    @classmethod
    def _probe_translations(cls, library_path, english):
        """ Ask the core for its strings once per language it may know

        Cores ship their translations inside themselves and choose a table
        from the answer to GET_LANGUAGE, so this is the only way to read them.
        Skipped for a core that never asks, which is most of them. """
        if not english.get('translatable'):
            return {}

        translations = {}
        for language in RetroLanguage:
            if language is RetroLanguage.ENGLISH:
                continue
            localised, _ = cls.probe(library_path, int(language))
            if localised is None or not localised.get('translated'):
                continue
            paired = _pair_strings(english, localised)
            if paired:
                translations[language.libretro_name] = paired
        return translations

    @classmethod
    def probe(cls, library_path, language=0):
        """ Load the core in a helper process and report what it registers.

        Some cores only register their options in retro_init(), and some cores
        crash or hang in there. Probing out-of-process keeps a bad core from
        aborting the parent, and preserves whatever the core managed to
        register before it died.

        The helper runs in a directory of its own, because retro_init() is
        also where a core is entitled to write its config file.

        Returns (result, reason), where reason says what went wrong if the
        core couldn't be read -- a core that won't load is the everyday case
        here, and "undefined symbol: mpeg2_info" is the answer to why. """
        result_path = None
        try:
            with tempfile.NamedTemporaryFile(delete=False) as result_file:
                result_path = result_file.name

            with tempfile.TemporaryDirectory() as scratch_directory:
                helper = subprocess.run(
                    [sys.executable, '-m',
                     'kodi_game_scripting.libretro_ctypes',
                     '--probe', os.path.abspath(library_path), result_path,
                     str(language)],
                    check=False, timeout=PROBE_TIMEOUT_SECONDS,
                    stderr=subprocess.PIPE,
                    cwd=scratch_directory, env=cls._probe_environment())

            result = cls._read_probe_result(result_path)
            if result is not None:
                return result, ''
            return None, cls._failure_reason(helper)
        except subprocess.TimeoutExpired:
            return None, f'no answer in {PROBE_TIMEOUT_SECONDS}s'
        except (OSError, subprocess.SubprocessError) as err:
            return None, str(err)
        finally:
            if result_path:
                try:
                    os.unlink(result_path)
                except OSError:
                    pass

    @staticmethod
    def _failure_reason(helper):
        """ Explain a helper that produced nothing usable

        Cores are noisy on the way down, so report the last thing said. """
        for line in reversed(helper.stderr.decode('utf-8', 'replace')
                             .splitlines()):
            if line.strip():
                return line.strip()

        if helper.returncode < 0:
            return f'killed by signal {-helper.returncode}'
        return f'exit code {helper.returncode}'

    @staticmethod
    def _probe_environment():
        """ Environment for the helper, which doesn't run from our directory

        Keep this package importable there, whether it's installed or being
        run from a checkout. """
        package_root = os.path.dirname(os.path.dirname(os.path.abspath(
            __file__)))
        environment = dict(os.environ)
        python_path = environment.get('PYTHONPATH')
        environment['PYTHONPATH'] = os.pathsep.join(
            [package_root, python_path] if python_path else [package_root])
        return environment

    @staticmethod
    def _read_probe_result(result_path):
        """ Read probe result JSON from helper process """
        try:
            with open(result_path, 'r', encoding='utf-8') as result_file:
                return json.load(result_file)
        except (OSError, ValueError):
            return None

    @classmethod
    def has_opengl_linkage(cls, library_path):
        """ Check if the library links opengl """
        ldd_output = subprocess.run(
            cls.LDD_CMD + [library_path], stdout=subprocess.PIPE, check=True)
        return bool(re.search(r'(?:libgl|opengl)',
                              str(ldd_output.stdout, 'utf-8'), re.IGNORECASE))


class LibretroProbe:
    """ Loads a libretro core and records what it registers.

        Runs in a helper process; see LibretroWrapper.probe(). """

    def __init__(self, library_path, result_path, language=0):
        self._result_path = result_path
        self._language = language
        self._lib = ctypes.cdll.LoadLibrary(library_path)
        self._result = {
            'system_info': {
                'name': '', 'version': '', 'extensions': [],
                'need_fullpath': False, 'block_extract': False,
                'supports_no_game': False, 'supports_disc_control': False,
            },
            'options': [],
            'categories': [],
            # Whether the core picks its strings by language, and whether it
            # had a table for the one it was given
            'translatable': False,
            'translated': False,
        }
        # Cores may register options more than once (typically SET_VARIABLES
        # first and then a richer API). The first set of options we're given
        # wins, so that the fallback doesn't overwrite the good one.
        self._have_options = False
        # Held for as long as the core may call back into it
        self._callback = None
        # Same, for any option value handed back through GET_VARIABLE
        self._variable_values = []
        # Same, for the directory handed back through GET_SYSTEM_DIRECTORY
        self._system_directory = None
        # Discards what the core logs; held so the core can keep calling it
        self._log_callback = RETRO_LOG_PRINTF_T(lambda level, message: None)

    def run(self):
        """ Probe the core, writing results out as they become known """
        self._read_system_info()
        self._write()

        self._set_environment()
        self._write()

        # Some cores defer registering their options to retro_init()
        self._init()
        self._write()

    def _write(self):
        """ Persist results and fsync, so a later crash can't lose them """
        with open(self._result_path, 'w', encoding='utf-8') as result_file:
            json.dump(self._result, result_file)
            result_file.flush()
            os.fsync(result_file.fileno())

    def _read_system_info(self):
        retro_get_system_info = self._lib.retro_get_system_info
        retro_get_system_info.argtypes = [ctypes.POINTER(RetroSystemInfo)]
        retro_get_system_info.restype = None

        system_info = RetroSystemInfo()
        retro_get_system_info(ctypes.byref(system_info))

        self._result['system_info'].update({
            'name': _str(system_info.library_name),
            'version': _str(system_info.library_version),
            'extensions': _str(system_info.valid_extensions).split('|'),
            'need_fullpath': bool(system_info.need_fullpath),
            'block_extract': bool(system_info.block_extract),
        })

    def _set_environment(self):
        environment_t = ctypes.CFUNCTYPE(
            ctypes.c_bool, ctypes.c_uint, ctypes.c_void_p)

        retro_set_environment = self._lib.retro_set_environment
        retro_set_environment.argtypes = [environment_t]
        retro_set_environment.restype = None

        self._callback = environment_t(self._environment)
        retro_set_environment(self._callback)

    def _init(self):
        retro_init = self._lib.retro_init
        retro_init.argtypes = []
        retro_init.restype = None
        retro_init()

        retro_deinit = getattr(self._lib, 'retro_deinit', None)
        if retro_deinit:
            retro_deinit.argtypes = []
            retro_deinit.restype = None
            retro_deinit()

    def _environment(self, cmd, data):
        """ Libretro environment callback """
        if cmd in (RETRO_ENVIRONMENT_SET_DISK_CONTROL_INTERFACE,
                   RETRO_ENVIRONMENT_SET_DISK_CONTROL_EXT_INTERFACE):
            self._result['system_info']['supports_disc_control'] = True
            self._write()
            return True

        if cmd == RETRO_ENVIRONMENT_SET_PIXEL_FORMAT:
            return True

        # A core may pass NULL to ask whether a command is answered at all.
        # Everything below this reads or writes through the pointer.
        if not data:
            return False

        if cmd == RETRO_ENVIRONMENT_GET_LANGUAGE:
            self._result['translatable'] = True
            ctypes.cast(data, ctypes.POINTER(ctypes.c_uint))[0] = \
                self._language
            return True

        if cmd == RETRO_ENVIRONMENT_SET_SUPPORT_NO_GAME:
            self._result['system_info']['supports_no_game'] = \
                ctypes.cast(data, ctypes.POINTER(ctypes.c_bool))[0]
            return True

        return self._environment_queries(cmd, data)

    def _environment_queries(self, cmd, data):
        """ The part of the environment callback that answers a core's asks """
        if cmd in (RETRO_ENVIRONMENT_GET_SYSTEM_DIRECTORY,
                   RETRO_ENVIRONMENT_GET_SAVE_DIRECTORY):
            return self._get_directory(data)

        if cmd == RETRO_ENVIRONMENT_GET_LOG_INTERFACE:
            # Not for the output: a core refused a logger keeps the null
            # pointer and calls through it anyway.
            ctypes.cast(data, ctypes.POINTER(RetroLogCallback))[0].log = \
                self._log_callback
            return True

        if cmd == RETRO_ENVIRONMENT_GET_MESSAGE_INTERFACE_VERSION:
            ctypes.cast(data, ctypes.POINTER(ctypes.c_uint))[0] = 0
            return True

        if cmd == RETRO_ENVIRONMENT_GET_VARIABLE:
            return self._get_variable(data)

        if cmd == RETRO_ENVIRONMENT_GET_CORE_OPTIONS_VERSION:
            # This is what gets a core to hand over its categories, help text
            # and value labels instead of a flat list of pipe-delimited values
            ctypes.cast(data, ctypes.POINTER(ctypes.c_uint))[0] = \
                CORE_OPTIONS_VERSION
            return True

        return self._environment_options(cmd, data)

    def _get_directory(self, data):
        """ Answer GET_SYSTEM_DIRECTORY and GET_SAVE_DIRECTORY """
        directory = os.environ.get(SYSTEM_DIRECTORY_ENV)
        if not directory:
            return False

        # The pointer has to outlive this call, so keep a reference
        self._system_directory = ctypes.c_char_p(directory.encode())
        ctypes.cast(data, ctypes.POINTER(ctypes.c_char_p))[0] = \
            self._system_directory
        return True

    def _get_variable(self, data):
        """ Answer GET_VARIABLE with the default the core just declared

        A core reading its own options back gets NULL otherwise and takes it
        into strcmp, ending the probe before anything is written. """
        variable = ctypes.cast(data, ctypes.POINTER(RetroVariable))[0]
        if not variable.key:
            return False

        key = _str(variable.key)
        for option in self._result['options']:
            if option['key'] != key:
                continue
            value = ctypes.c_char_p(option['default'].encode())
            self._variable_values.append(value)
            ctypes.cast(data, ctypes.POINTER(RetroVariable))[0].value = value
            return True
        return False

    def _environment_options(self, cmd, data):
        """ The part of the environment callback that registers settings """
        if cmd == RETRO_ENVIRONMENT_SET_VARIABLES:
            return self._set_variables(data)

        if cmd in (RETRO_ENVIRONMENT_SET_CORE_OPTIONS,
                   RETRO_ENVIRONMENT_SET_CORE_OPTIONS_INTL):
            return self._set_core_options(
                data, intl=cmd == RETRO_ENVIRONMENT_SET_CORE_OPTIONS_INTL)

        if cmd in (RETRO_ENVIRONMENT_SET_CORE_OPTIONS_V2,
                   RETRO_ENVIRONMENT_SET_CORE_OPTIONS_V2_INTL):
            return self._set_core_options_v2(
                data, intl=cmd == RETRO_ENVIRONMENT_SET_CORE_OPTIONS_V2_INTL)

        return False

    def _add_option(self, option):
        """ Record an option, with the default libretro would end up using """
        values = option['values']

        # The newer APIs name a default but are allowed to leave it out, in
        # which case libretro falls back to the first value. A handful of
        # cores name one that isn't among their own values ("100%" where the
        # values are "100"|"125"|...); fall back for those too, rather than
        # write a default Kodi would reject.
        if values and option['default'] not in [
                value['value'] for value in values]:
            option['default'] = values[0]['value']

        self._result['options'].append(option)

    @staticmethod
    def _read_values(values):
        """ Read a retro_core_option_value array, terminated by a null value """
        result = []
        for index in range(RETRO_NUM_CORE_OPTION_VALUES_MAX):
            if not values[index].value:
                break
            result.append({'value': _str(values[index].value),
                           'label': _str(values[index].label)})
        return result

    def _set_variables(self, data):
        """ Read struct retro_variable[], the oldest and least expressive API

        The description and the values arrive as one string, in the form
        "Description; value1|value2", and the first value is the default. """
        if self._have_options:
            return True

        index = 0
        while True:
            variable = ctypes.cast(data, ctypes.POINTER(RetroVariable))[index]
            index += 1
            if not variable.key and not variable.value:
                break

            description, _, values = _str(variable.value).partition(';')
            values = [{'value': value.strip(), 'label': ''}
                      for value in values.strip().split('|') if value.strip()]
            if not values:
                continue

            self._add_option({
                'key': _str(variable.key),
                'description': description,
                'info': '',
                'category': '',
                'values': values,
                'default': values[0]['value'],
            })

        self._have_options = bool(self._result['options'])
        self._write()
        return True

    def _intl_definitions(self, options):
        """ Pick the translated table when the core has one for the language

        A core with no table for it leaves local null and us is all there is,
        which is the English strings over again. """
        if self._language and options.local:
            self._result['translated'] = True
            return options.local
        return options.us

    def _set_core_options(self, data, intl):
        """ Read struct retro_core_option_definition[], core options v1

        Adds help text, per-value labels and an explicit default over
        SET_VARIABLES, but still has no categories. """
        if intl:
            options = ctypes.cast(
                data, ctypes.POINTER(RetroCoreOptionsIntl))[0]
            definitions = self._intl_definitions(options)
        else:
            definitions = ctypes.cast(
                data, ctypes.POINTER(RetroCoreOptionDefinition))

        if not definitions:
            return True

        self._result['options'] = []
        index = 0
        while definitions[index].key:
            definition = definitions[index]
            index += 1
            self._add_option({
                'key': _str(definition.key),
                'description': _str(definition.desc),
                'info': _str(definition.info),
                'category': '',
                'values': self._read_values(definition.values),
                'default': _str(definition.default_value),
            })

        self._have_options = True
        self._write()
        return True

    def _set_core_options_v2(self, data, intl):
        """ Read struct retro_core_options_v2, core options v2

        Everything v1 has, plus the categories that let Kodi show more than
        one flat list of settings. """
        if intl:
            options_intl = ctypes.cast(
                data, ctypes.POINTER(RetroCoreOptionsV2Intl))[0]
            if not options_intl.us:
                return True
            if self._language and options_intl.local:
                self._result['translated'] = True
                options = options_intl.local[0]
            else:
                options = options_intl.us[0]
        else:
            options = ctypes.cast(data, ctypes.POINTER(RetroCoreOptionsV2))[0]

        self._result['options'] = []
        self._result['categories'] = []

        if options.categories:
            index = 0
            while options.categories[index].key:
                category = options.categories[index]
                index += 1
                self._result['categories'].append({
                    'key': _str(category.key),
                    'description': _str(category.desc),
                    'info': _str(category.info),
                })

        if options.definitions:
            index = 0
            while options.definitions[index].key:
                definition = options.definitions[index]
                index += 1
                # desc is deliberate: desc_categorized drops the context that
                # existing translations were written against
                self._add_option({
                    'key': _str(definition.key),
                    'description': _str(definition.desc),
                    'info': _str(definition.info),
                    'category': _str(definition.category_key),
                    'values': self._read_values(definition.values),
                    'default': _str(definition.default_value),
                })

        self._have_options = True
        self._write()
        return True


if __name__ == '__main__':  # pragma: no cover
    if len(sys.argv) in (4, 5) and sys.argv[1] == '--probe':
        LibretroProbe(sys.argv[2], sys.argv[3],
                      int(sys.argv[4]) if len(sys.argv) == 5 else 0).run()
    else:
        LIB = LibretroWrapper(sys.argv[1])
        print(LIB.system_info)
        print(LIB.categories)
        print(LIB.options)
