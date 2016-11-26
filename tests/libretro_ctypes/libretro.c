#include "libretro.h"

void retro_get_system_info(struct retro_system_info *info)
{
   info->library_name = "libraryname";
   info->library_version = "123-ver";
   info->valid_extensions = "a|bb|ccc";
   info->need_fullpath = true;
   info->block_extract = false;
}

static struct retro_variable vars[] = {
   { "setting1", "Setting 1; enabled|disabled" },
   { "setting2", "Setting 2; 0|1|2|3" },
   { NULL, NULL },
};

void retro_set_environment(retro_environment_t cb)
{
   bool allow_no_game = true;
   cb(RETRO_ENVIRONMENT_SET_SUPPORT_NO_GAME, &allow_no_game);
   cb(RETRO_ENVIRONMENT_SET_VARIABLES, (void*)vars);
   cb(RETRO_ENVIRONMENT_GET_SYSTEM_DIRECTORY, NULL);
}
