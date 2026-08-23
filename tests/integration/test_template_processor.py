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

"""Test the Template Processor"""

import filecmp
import os
from unittest import mock

import pytest

from kodi_game_scripting.git_access import GitHubRepo
from kodi_game_scripting.process_game_addons import KodiGameAddon
from kodi_game_scripting.template_processor import TemplateProcessor, \
    TEMPLATE_DIR

pytestmark = [pytest.mark.integration]


# pylint: disable=redefined-outer-name

REFERENCE_DIR = os.path.join(
    os.path.dirname(os.path.realpath(__file__)),
    'test_data', os.path.splitext(os.path.basename(__file__))[0])


def generate_configured_addon(tmpdir, game_name):
    """Generate an add-on from its real config.py entry."""
    addon_name = 'game.libretro.{}'.format(game_name)
    github_repo = GitHubRepo(addon_name, '', '')

    # Source-control behavior is outside this template integration test. Avoid
    # creating a throwaway repository while retaining KodiGameAddon's real
    # config-to-template mapping.
    with mock.patch('kodi_game_scripting.process_game_addons.GitRepo'):
        addon = KodiGameAddon(addon_name, game_name, github_repo,
                              str(tmpdir), None)

    addon.process_addon_files()
    return os.path.join(str(tmpdir), addon_name)


def read_file(filename):
    """Read a generated UTF-8 file."""
    with open(filename, 'r', encoding='utf-8') as file_ctx:
        return file_ctx.read()


def cmake_section(cmake, start, end):
    """Extract a generated platform section from CMakeLists.txt."""
    return cmake.split(start, 1)[1].split(end, 1)[0]


def test_process_template(tmpdir):
    """Test the Template Processor"""
    data = {
        'game': {
            'name': 'mygame',
            'addon': 'game.libretro.mygame',
            'debian_package': 'game-libretro-mygame',
            'branch': 'master',
            'version': '2.10.3',
        },
        'libretro_repo': {
            'branch': 'master',
        },
        'config': {
            'cmake_options_osx':
                'MINVERSION=-mmacosx-version-min=${CMAKE_OSX_DEPLOYMENT_TARGET}',
        },
    }
    # Between them these cover what a settings.xml has to handle: options a
    # core leaves uncategorised and options it doesn't, help text present and
    # absent, and values with and without a label of their own
    extdata = {
        'system_info': {
            'extensions': ['ext1', 'ext2']
        },
        'categories': [
            {'id': 'general', 'label': 128, 'help': None, 'settings': [
                {'id': 'mysetting1', 'label': 30001, 'help': None,
                 'default': 'value1',
                 'values': [{'value': 'value1', 'label': None},
                            {'value': 'value2', 'label': None}]},
            ]},
            {'id': 'video', 'label': 30002, 'help': 30003, 'settings': [
                {'id': 'mysetting2', 'label': 30004, 'help': 30005,
                 'default': 'value2',
                 'values': [{'value': 'value1', 'label': 30006},
                            {'value': 'value2', 'label': None}]},
            ]},
        ],
        'strings': [
            {'id': 30001, 'content': 'mysetting1'},
            {'id': 30002, 'content': 'Video'},
            {'id': 30003, 'content': 'What the picture looks like.'},
            {'id': 30004, 'content': 'mysetting2'},
            # The shape of real core help text: several lines, and quotes
            {'id': 30005, 'content': 'What mysetting2 does.\nSet it to '
                                     '"value1" unless you know better.'},
            {'id': 30006, 'content': 'The first value'},
        ],
    }

    print('Template dir: file://{}'.format(TEMPLATE_DIR))
    print('Reference dir: file://{}'.format(REFERENCE_DIR))
    print('Test dir: file://{}'.format(tmpdir))

    template_processor = TemplateProcessor()

    # First generation step skips reading previously generated data.
    # Also don't yet provide all data so that we execute more branches.
    template_processor.process(TEMPLATE_DIR, str(tmpdir), data)

    # Add more data and run generation again.
    data.update(extdata)
    template_processor.process(TEMPLATE_DIR, str(tmpdir), data)

    # Run the generation and include data from the previously generated files.
    template_processor.process(TEMPLATE_DIR, str(tmpdir), data)

    def assert_identical(dircmp):
        assert not dircmp.right_only and not dircmp.diff_files
        for subdircmp in dircmp.subdirs.values():
            assert_identical(subdircmp)

    assert_identical(filecmp.dircmp(str(tmpdir), REFERENCE_DIR))


def test_process_template_linux_arm_platforms(tmpdir):
    """Test opting a core into architecture-specific Linux platforms"""
    data = {
        'game': {
            'name': 'uae4arm',
        },
        'config': {
            'platform_linux_aarch64': 'unix-aarch64',
            'platform_linux_arm': 'unix-neon',
        },
        'makefile': {
            'cmake': False,
            'dir': '.',
            'file': 'Makefile.libretro',
        },
        'library': {
            'soname': 'uae4arm_libretro',
            'jnisoname': 'libretro',
        },
    }

    TemplateProcessor.process(
        os.path.join('addon', 'depends', 'common'), str(tmpdir), data)

    cmake_path = os.path.join(str(tmpdir), 'uae4arm', 'CMakeLists.txt')
    with open(cmake_path, 'r', encoding='utf-8') as cmake_file:
        cmake = cmake_file.read()

    linux_build = cmake.split(
        'elseif(CORE_SYSTEM_NAME STREQUAL linux)', 1)[1].split(
            'elseif(CORE_SYSTEM_NAME STREQUAL osx)', 1)[0]
    assert ('if(CMAKE_SYSTEM_PROCESSOR STREQUAL arm64 OR '
            'CMAKE_SYSTEM_PROCESSOR STREQUAL aarch64)') in linux_build
    assert 'elseif(CMAKE_SYSTEM_PROCESSOR MATCHES "^arm")' in linux_build
    assert 'set(PLATFORM unix-aarch64)' in linux_build
    assert 'set(PLATFORM unix-neon)' in linux_build
    assert 'platform=${PLATFORM}' in linux_build
    assert '                    platform=unix\n' not in linux_build


def test_uae4arm_jenkins_platforms(tmpdir):
    """Test UAE4ARM's Jenkins matrix contains only supported ARM targets."""
    addon_dir = generate_configured_addon(tmpdir, 'uae4arm')
    jenkins = read_file(os.path.join(addon_dir, 'Jenkinsfile'))

    assert jenkins == (
        'buildPlugin(version: "Omega", platforms: '
        '["android-aarch64", "android-armv7", "osx-arm64"])\n')


def test_uae4arm_android_generation(tmpdir):
    """Test UAE4ARM uses direct Make for both supported Android ABIs."""
    addon_dir = generate_configured_addon(tmpdir, 'uae4arm')
    depends_dir = os.path.join(addon_dir, 'depends', 'common', 'uae4arm')
    cmake = read_file(os.path.join(depends_dir, 'CMakeLists.txt'))
    android_build = cmake_section(
        cmake, 'elseif(CORE_SYSTEM_NAME STREQUAL android)',
        'elseif(CORE_SYSTEM_NAME STREQUAL freebsd)')

    assert '${NDKROOT}/ndk-build' not in android_build
    assert '-C jni' not in android_build
    assert ('if(CPU STREQUAL armeabi-v7a)\n'
            '    set(PLATFORM android-armv7)') in android_build
    assert ('elseif(CPU STREQUAL arm64-v8a)\n'
            '    set(PLATFORM android-aarch64)') in android_build
    assert '-f Makefile.libretro' in android_build
    assert 'CC=${CMAKE_C_COMPILER}' in android_build
    assert 'CXX=${CMAKE_CXX_COMPILER}' in android_build
    assert 'CC_AS=${CMAKE_C_COMPILER}' in android_build
    assert 'platform=${PLATFORM}' in android_build
    assert 'DEPS_PREFIX=${ADDON_DEPENDS_PATH}' in android_build

    # UAE4ARM's Android Makefile emits an _android artifact. The dependency
    # build consumes that file, then installs it under Kodi's normal core name.
    assert ('set(LIBRETRO_SONAME '
            'uae4arm_libretro_android${CMAKE_SHARED_LIBRARY_SUFFIX})') \
        in android_build
    assert ('install(FILES ${PROJECT_SOURCE_DIR}/${LIBRETRO_BINARY_DIR}/'
            '${LIBRETRO_SONAME}') in cmake
    assert ('DESTINATION ${CMAKE_INSTALL_PREFIX}/lib/libretro '
            'RENAME uae4arm_libretro${CMAKE_SHARED_LIBRARY_SUFFIX})') in cmake

    # Source changes are maintained as a format-patch in the add-on repository,
    # not duplicated as a generator template.
    assert not any(filename.endswith('.patch')
                   for filename in os.listdir(depends_dir))


def test_same_cdi_android_generation(tmpdir):
    """Test SAME_CDI uses its libretro makefile for every Android ABI."""
    addon_dir = generate_configured_addon(tmpdir, 'same_cdi')
    cmake = read_file(os.path.join(
        addon_dir, 'depends', 'common', 'same_cdi', 'CMakeLists.txt'))
    android_build = cmake_section(
        cmake, 'elseif(CORE_SYSTEM_NAME STREQUAL android)',
        'elseif(CORE_SYSTEM_NAME STREQUAL freebsd)')

    assert '${NDKROOT}/ndk-build' not in android_build
    assert '-C jni' not in android_build
    assert ('if(CPU STREQUAL armeabi-v7a)\n'
            '    set(PLATFORM android-arm)') in android_build
    assert ('elseif(CPU STREQUAL arm64-v8a)\n'
            '    set(PLATFORM android-arm64)') in android_build
    assert ('elseif(CPU STREQUAL i686)\n'
            '    set(PLATFORM android-x86)') in android_build
    assert ('elseif(CPU STREQUAL x86_64)\n'
            '    set(PLATFORM android-x86_64)') in android_build
    assert '-f Makefile.libretro' in android_build
    assert '${build_job_count}' in android_build
    assert '${LIBRETRO_DEBUG}' in android_build
    assert 'CC=${CMAKE_C_COMPILER}' in android_build
    assert 'CXX=${CMAKE_CXX_COMPILER}' in android_build
    assert 'CC_AS=${CMAKE_C_COMPILER}' in android_build
    assert 'platform=${PLATFORM}' in android_build

    # SAME_CDI emits same_cdi_libretro_android.so on Android. Consume that
    # artifact while retaining the normal Kodi library name at install time.
    assert ('set(LIBRETRO_SONAME '
            'same_cdi_libretro_android${CMAKE_SHARED_LIBRARY_SUFFIX})') \
        in android_build
    assert ('DESTINATION ${CMAKE_INSTALL_PREFIX}/lib/libretro '
            'RENAME same_cdi_libretro${CMAKE_SHARED_LIBRARY_SUFFIX})') in cmake


def test_uae4arm_osx_arm64_generation(tmpdir):
    """Test UAE4ARM uses its Apple ARM platform and cross-build inputs."""
    addon_dir = generate_configured_addon(tmpdir, 'uae4arm')
    cmake = read_file(os.path.join(
        addon_dir, 'depends', 'common', 'uae4arm', 'CMakeLists.txt'))
    osx_build = cmake_section(
        cmake, 'elseif(CORE_SYSTEM_NAME STREQUAL osx)',
        'elseif(CORE_SYSTEM_NAME STREQUAL ios OR '
        'CORE_SYSTEM_NAME STREQUAL darwin_embedded)')

    assert ('if(CPU STREQUAL arm64)\n'
            '    set(ARCH arm)\n'
            '    set(PLATFORM osx-arm64)') in osx_build
    assert '-f Makefile.libretro' in osx_build
    assert 'CC=${CMAKE_C_COMPILER}' in osx_build
    assert 'CXX=${CMAKE_CXX_COMPILER}' in osx_build
    assert 'CC_AS=${CMAKE_C_COMPILER}' in osx_build
    assert 'CROSS_COMPILE=1' in osx_build
    assert 'LIBRETRO_APPLE_ISYSROOT=${CMAKE_OSX_SYSROOT}' in osx_build
    assert ('LIBRETRO_APPLE_PLATFORM=${CPU}-apple-macos'
            '${CMAKE_OSX_DEPLOYMENT_TARGET}') in osx_build
    assert 'platform=${PLATFORM}' in osx_build
    assert 'DEPS_PREFIX=${ADDON_DEPENDS_PATH}' in osx_build
    assert ('MINVERSION=-mmacosx-version-min='
            '${CMAKE_OSX_DEPLOYMENT_TARGET}') in osx_build

    # macOS does not override LIBRETRO_SONAME, so its source artifact resolves
    # to uae4arm_libretro.dylib via CMAKE_SHARED_LIBRARY_SUFFIX.
    assert ('set(LIBRETRO_SONAME '
            'uae4arm_libretro${CMAKE_SHARED_LIBRARY_SUFFIX})') in cmake


def test_jni_android_generation_unchanged(tmpdir):
    """Test a representative JNI core retains its ndk-build path."""
    addon_dir = generate_configured_addon(tmpdir, '2048')
    cmake = read_file(os.path.join(
        addon_dir, 'depends', 'common', '2048', 'CMakeLists.txt'))
    android_build = cmake_section(
        cmake, 'elseif(CORE_SYSTEM_NAME STREQUAL android)',
        'elseif(CORE_SYSTEM_NAME STREQUAL freebsd)')

    assert '${NDKROOT}/ndk-build' in android_build
    assert '-C jni' in android_build
    assert 'APP_ABI=${PLATFORM}' in android_build
    assert 'NDK_LIBS_OUT=${PROJECT_SOURCE_DIR}/${LIBRETRO_BINARY_DIR}' \
        in android_build
    assert ('&& cp ${PROJECT_SOURCE_DIR}/${LIBRETRO_BINARY_DIR}/'
            '${PLATFORM}/${LIBRETRO_JNISONAME}') in android_build
    assert 'CC=${CMAKE_C_COMPILER}' not in android_build
    assert 'CXX=${CMAKE_CXX_COMPILER}' not in android_build
    assert 'CC_AS=${CMAKE_C_COMPILER}' not in android_build


def test_direct_make_android_generation_unchanged(tmpdir):
    """Test an unrelated direct-Make core keeps its legacy Android block."""
    addon_dir = generate_configured_addon(tmpdir, 'moonlight')
    cmake = read_file(os.path.join(
        addon_dir, 'depends', 'common', 'moonlight', 'CMakeLists.txt'))
    android_build = cmake_section(
        cmake, 'elseif(CORE_SYSTEM_NAME STREQUAL android)',
        'elseif(CORE_SYSTEM_NAME STREQUAL freebsd)')

    assert android_build.splitlines() == [
        '',
        '  if(NOT NDKROOT)',
        '    message(FATAL_ERROR "${PROJECT_NAME} needs NDKROOT for Android. '
        'Missing Toolchain file?")',
        '  endif()',
        '  if(CPU STREQUAL armeabi-v7a)',
        '    set(PLATFORM android-armv7)',
        '  elseif(CPU STREQUAL i686)',
        '    set(PLATFORM x86)',
        '  else()',
        '    message(FATAL_ERROR "${PROJECT_NAME} needs Android ${CPU} build '
        'command in CMakeLists.txt!")',
        '  endif()',
        '  set(LIBRETRO_SONAME '
        'moonlight_libretro_android${CMAKE_SHARED_LIBRARY_SUFFIX})',
        '  get_filename_component(TOOLCHAIN_DIR ${CMAKE_C_COMPILER} DIRECTORY)',
        '  set(BUILD_COMMAND PATH=${TOOLCHAIN_DIR}:$ENV{PATH} $(MAKE)',
        '                                                     -C .',
        '                                                     -f Makefile',
        '                                                     ${build_job_count}',
        '                                                     ${LIBRETRO_DEBUG}',
        '                                                     GIT_VERSION=',
        '                                                     platform=${PLATFORM}',
        '                                                     )',
    ]
    assert 'arm64-v8a' not in android_build
    assert 'CC=${CMAKE_C_COMPILER}' not in android_build
    assert 'CXX=${CMAKE_CXX_COMPILER}' not in android_build
    assert 'CC_AS=${CMAKE_C_COMPILER}' not in android_build


def test_desktop_generation_unchanged(tmpdir):
    """Test an unrelated core retains its Windows and macOS generation."""
    addon_dir = generate_configured_addon(tmpdir, 'virtualjaguar')
    cmake = read_file(os.path.join(
        addon_dir, 'depends', 'common', 'virtualjaguar', 'CMakeLists.txt'))

    windows_build = cmake_section(
        cmake, 'if(CORE_SYSTEM_NAME STREQUAL windows)',
        'elseif(CORE_SYSTEM_NAME STREQUAL linux)')
    assert 'find_package(MinGW REQUIRED)' in windows_build
    assert 'set(MSYSTEM MINGW64)' in windows_build
    assert 'set(MSYSTEM MINGW32)' in windows_build
    assert 'set(BUILD_COMMAND ${MINGW_MAKE}' in windows_build
    assert '-f Makefile' in windows_build
    assert 'MSYSTEM=${MSYSTEM}' in windows_build
    assert 'platform=win' in windows_build

    osx_build = cmake_section(
        cmake, 'elseif(CORE_SYSTEM_NAME STREQUAL osx)',
        'elseif(CORE_SYSTEM_NAME STREQUAL ios OR '
        'CORE_SYSTEM_NAME STREQUAL darwin_embedded)')
    assert ('if(CPU STREQUAL arm64)\n'
            '    set(ARCH arm)') in osx_build
    assert ('elseif(CPU STREQUAL x86_64)\n'
            '    set(ARCH intel)\n'
            '    set(PLATFORM_CMAKE_OPTIONS BLITTER_SIMD=sse2)') in osx_build
    assert '-f Makefile' in osx_build
    assert 'CC=${CMAKE_C_COMPILER}' in osx_build
    assert 'CXX=${CMAKE_CXX_COMPILER}' in osx_build
    assert 'SDKROOT=${CMAKE_OSX_SYSROOT}' in osx_build
    assert 'MACOSX_DEPLOYMENT_TARGET=${CMAKE_OSX_DEPLOYMENT_TARGET}' \
        in osx_build
    assert 'platform=osx' in osx_build
    assert 'platform=${PLATFORM}' not in osx_build
    assert 'CC_AS=${CMAKE_C_COMPILER}' not in osx_build
