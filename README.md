# Scripting for Kodi Game addons

[Kodi's RetroPlayer](https://github.com/garbear/xbmc) offers a wrapper to use
[Libretro](https://www.libretro.com/) game and emulator cores.

While this offers access to a multitude of platforms and games, it's cumbersome
to maintain because every Libretro core needs to be built and packaged as a
Kodi binary add-on. This project tries to add some scripting to simplify the
maintenance efforts.

Manual porting is explained in this [forum post](http://forum.kodi.tv/showthread.php?tid=224328).

## Usage

Clone [game add-ons](https://github.com/kodi-game) to `<WORKING_DIRECTORY>` and
run:

    ./process_game_addons.py --game-addons-dir <WORKING_DIRECTORY>

Afterwards use `git` to check in the changes and push them to the repos.

## License

This program is free software; you can redistribute it and/or modify it
under the terms of the GNU General Public License as published by the
Free Software Foundation; either version 2 of the License, or (at your
option) any later version.

This program is distributed in the hope that it will be useful, but
WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General
Public License for more details.
