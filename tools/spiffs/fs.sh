#!/bin/sh
set -eu

script_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
board=${1:-owl_gansu}
if [ "$board" = "owl_box" ]; then
    board=owl_2024_box
fi
exec python3 "$script_dir/gen_spiffs_image.py" \
    "$script_dir/../../projects/labplus/config_board_labplus_${board}.mk"
