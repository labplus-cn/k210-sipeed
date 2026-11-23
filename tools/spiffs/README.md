spiffs tools
========

## Generate spiffs image from files

Only support Linux

* Put project files in `<project>/spiffs/fs`. Projects without that directory use `tools/spiffs/fs`.

* Generate the image with the firmware configuration:

```
python gen_spiffs_image.py ../../projects/maixpy_k210/config_defaults.mk
```

Use the same configuration as the firmware build. Labplus board configurations place the image under `projects/labplus/build/<board>/maixpy_spiffs.img`. A generated `build/<board>/config/global_config.mk` also writes to that board's build directory. Other project configurations write to `<project>/build/maixpy_spiffs.img`.

For example, run the following from the repository root to generate the Labplus 3.1 camera image:

```sh
python3 tools/spiffs/gen_spiffs_image.py projects/labplus/config_board_labplus_owl_2024.mk
```

Linux requires `make`, GCC, G++, and the initialized `tools/spiffs/mkspiffs` and nested SPIFFS submodules. The tool builds `mkspiffs` in a temporary directory.

* Burn it to flash at correct address with [kflash_gui](https://github.com/sipeed/kflash_gui) or `kflash.py`, this adress is assigned in the config file(`config_defaults.mk` or `build/config/global_config.mk`)( variable `CONFIG_SPIFFS_START_ADDR`)


![pack_spiffs.gif](https://cdn.sipeed.com/pack_spiffs_ops.gif)

pack_spiffs_ops.gif: https://cdn.sipeed.com/pack_spiffs_ops.gif

