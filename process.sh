#!/bin/bash
./process_game_addons.py \
    --game-addons-dir=game-addons \
    --kodi-source-dir=`pwd`/../kodi \
    `#--push-branch=master` \
    --git \
    --compile \
    --filter="yabause"
