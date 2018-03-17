[![Build Status](https://travis-ci.org/fetzerch/kodi-game-scripting.svg?branch=master)](https://travis-ci.org/fetzerch/kodi-game-scripting)

# Scripting for Kodi Game addons

This project supports Team-Kodi members in maintaining the
[game add-ons](https://github.com/kodi-game/) for
[Libretro](https://www.libretro.com/) game and emulator cores as
used by [Kodi's RetroPlayer](https://github.com/garbear/xbmc).

While the direct support of Libretro cores in RetroPlayer offers access to a
multitude of platforms and games, it's cumbersome to maintain because every
Libretro core needs to be built and packaged as a Kodi binary add-on. This
project tries to add some scripting to simplify the maintenance efforts.

## How does it work

The Kodi game add-ons that wrap Libretro cores are all very similar in
the way they are built and in the way the metadata (such as name,
version or description or version) is maintained.

*kodi-game-scripting* maintains a set of [Jinja2](http://jinja.pocoo.org/docs/)
templates from which we can completely generate an add-on that wraps a
Libretro core. The [templates](https://github.com/fetzerch/kodi-game-scripting/tree/master/templates)
define the overall structure of the add-on files and fill variable fields with
content from a set of metadata (descriptions from
[libretro-super](https://github.com/libretro/libretro-super/tree/master/dist/info),
the compiled Libretro core, and the current version of already existing files).

Additionally to the generation steps, *kodi-game-scripting* automates
dealing with Git(Hub) repos (creating, cloning, pulling, committing, pushing)
and also generates overview pages that can be used
to fill for example [Kodi Wiki - Game_add-ons](http://kodi.wiki/view/Game_add-ons).

## Use-cases

This project was designed to support the following use-cases:

- Fully automatic updates of build and add-on files (e.g. unify CMakeLists.txt,
  version numbers in addon.xml).
- Support manual work (e.g. automatic pushing after adding images to a
  set of add-ons).
- Create new add-ons for missing Libretro cores (as explained in this
  [forum post](http://forum.kodi.tv/showthread.php?tid=224328)).
- Simplify creating test builds for a given set of add-ons.
- Generate [Kodi Wiki - Game_add-ons](http://kodi.wiki/view/Game_add-ons).

## Dependencies

To compile the add-ons, you will need CMake >= 3.6.

*kodi-game-scripting* runs on Linux (and macOS with the constraint that
not all add-ons compile on macOS) and requires Python 3.

Additionally you will need the following Python packages:

- gitpython
- keyring
- jinja2
- pygithub
- xmljson

On Ubuntu, these can be installed using:

    sudo apt-get install python3-pip
    sudo pip3 install gitpython keyring jinja2 pygithub xmljson

The script will ask you for GitHub credentials as GitHub API calls are
limited when unauthorized. For pushing changes or creating new Repos, you need
to have write access to <https://github.com/kodi-game/>.

## Usage

Clone [game add-ons](https://github.com/kodi-game) to `<WORKING_DIRECTORY>` or
specify the `--git` parameter and then run:

    ./process_game_addons.py --game-addons-dir=<WORKING_DIRECTORY>

Some of the information (such as version or supported extensions) can only be
retrieved from a compiled add-on binary. This script can compile add-ons:

    ./process_game_addons.py --game-addons-dir=<WORKING_DIRECTORY> \
                             --compile --kodi-source-dir=<KODI_SOURCE_DIR>

Add-ons can be filtered with `--filter` (e.g. `--filter=bnes`).

The changed add-on files as well as the add-on descriptions necessary to
build the binary add-ons can be pushed to GitHub.

    ./process_game_addons.py --game-addons-dir=<WORKING_DIRECTORY> \
                             --compile --kodi-source-dir=<KODI_SOURCE_DIR> \
                             --git --push-branch testing \
                             --push-description --clean-description

- `--git` activates Git usage (and clones and resets add-on
  directories in the given `WORKING_DIRECTORY`.
- `--push-branch <BRANCH>` pushes the generated add-on files to the given
  `BRANCH` in *kodi-game*.
- `--push-description` pushes the add-on description files to the existing
  remote `origin` of the local `KODI_SOURCE_DIR`.
- `--clean-description` removes other existing add-on description files.

## License

This program is free software; you can redistribute it and/or modify it
under the terms of the GNU General Public License as published by the
Free Software Foundation; either version 2 of the License, or (at your
option) any later version.

This program is distributed in the hope that it will be useful, but
WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General
Public License for more details.
