
#include <stdio.h>
#include "py/runtime.h"
#include "py/mperrno.h"
#include "py/mphal.h"

#include "vfs_spiffs.h"
#include "w25qxx.h"
#include "sleep.h"
#include "syscalls.h"
#include "spiffs_config.h"
#include "spiffs_configport.h"


STATIC mp_obj_t k210_flash_read(mp_obj_t offset_in, mp_obj_t buf_in) {
    mp_int_t offset = mp_obj_get_int(offset_in);
    mp_buffer_info_t bufinfo;
    mp_get_buffer_raise(buf_in, &bufinfo, MP_BUFFER_WRITE);
    s32_t res = sys_spiffs_read(offset, bufinfo.len, bufinfo.buf);
    if (res != W25QXX_OK) {
        mp_raise_OSError(MP_EIO);
    }
    return mp_const_none;
}
STATIC MP_DEFINE_CONST_FUN_OBJ_2(flash_read_obj, k210_flash_read);

STATIC const mp_rom_map_elem_t flash_module_globals_table[] = {
    { MP_ROM_QSTR(MP_QSTR___name__), MP_ROM_QSTR(MP_QSTR_flash) },

    { MP_ROM_QSTR(MP_QSTR_read), MP_ROM_PTR(&flash_read_obj) },
};

STATIC MP_DEFINE_CONST_DICT(flash_module_globals, flash_module_globals_table);

const mp_obj_module_t flash_module = {
    .base = { &mp_type_module },
    .globals = (mp_obj_dict_t*)&flash_module_globals,
};

MP_REGISTER_MODULE(MP_QSTR_flash, flash_module, 1);
