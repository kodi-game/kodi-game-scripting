/* Test core for LibretroWrapper.
 *
 * Built three times with different defines, to cover the three ways a core
 * can hand over its settings:
 *
 *   (default)               core options v2, from retro_set_environment
 *   TEST_CORE_VARIABLES     SET_VARIABLES only, the oldest API
 *   TEST_CORE_INIT          core options v2, but not until retro_init
 */

#include "libretro.h"

#include <stddef.h>

static retro_environment_t environ_cb;

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

static struct retro_core_option_v2_category categories[] = {
   { "video", "Video", "Change what the picture looks like." },
   { NULL, NULL, NULL },
};

static struct retro_core_option_v2_definition definitions[] = {
   {
      "setting1",
      "Setting 1",
      NULL,
      "What setting 1 does.",
      NULL,
      "video",
      {
         { "enabled", "On" },
         { "disabled", "Off" },
         { NULL, NULL },
      },
      "disabled"
   },
   {
      "setting2",
      "Setting 2",
      NULL,
      NULL,
      NULL,
      NULL,
      {
         { "0", NULL },
         { "1", NULL },
         { "2", NULL },
         { "3", NULL },
         { NULL, NULL },
      },
      "0"
   },
   { NULL, NULL, NULL, NULL, NULL, NULL, {{NULL, NULL}}, NULL },
};

static struct retro_core_options_v2 options_v2 = {
   categories,
   definitions
};

static void set_options(void)
{
#ifdef TEST_CORE_VARIABLES
   environ_cb(RETRO_ENVIRONMENT_SET_VARIABLES, (void*)vars);
#else
   unsigned version = 0;

   /* A core only offers the richer API if the frontend says it speaks it */
   if (environ_cb(RETRO_ENVIRONMENT_GET_CORE_OPTIONS_VERSION, &version)
       && version >= 2)
      environ_cb(RETRO_ENVIRONMENT_SET_CORE_OPTIONS_V2, &options_v2);
   else
      environ_cb(RETRO_ENVIRONMENT_SET_VARIABLES, (void*)vars);
#endif
}

void retro_set_environment(retro_environment_t cb)
{
   bool allow_no_game = true;

   environ_cb = cb;

   cb(RETRO_ENVIRONMENT_SET_SUPPORT_NO_GAME, &allow_no_game);
   cb(RETRO_ENVIRONMENT_GET_SYSTEM_DIRECTORY, NULL);

#ifndef TEST_CORE_INIT
   set_options();
#endif
}

void retro_init(void)
{
#ifdef TEST_CORE_INIT
   set_options();
#endif
}

void retro_deinit(void)
{
}
