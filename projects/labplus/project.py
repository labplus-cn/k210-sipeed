#!/usr/bin/env python
#-*- coding = utf-8 -*-

import sys, os

sdk_env_name = "MY_SDK_PATH"


# # check python version , for kflash not python2 compatable
# check_version = False
# try:
#     if sys.implementation.version.major>=3:
#         check_version = True
# except Exception:
#     pass
# if not check_version:
#     print("Please use python3 to run me!")
#     exit(1)

# get SDK absolute path
sdk_path = os.path.abspath(sys.path[0]+"/../../")
try:
    sdk_path = os.environ[sdk_env_name]
except Exception:
    pass
print("-- SDK_PATH:{}".format(sdk_path))

# Board configurations use the same isolated directories as make.py.
if "--build-dir" not in sys.argv and not any(arg.startswith("--build-dir=") for arg in sys.argv):
    config_arg = next((arg.split("=", 1)[1] for arg in sys.argv if arg.startswith("--config_file=")), None)
    if config_arg is None and "--config_file" in sys.argv:
        index = sys.argv.index("--config_file")
        if index + 1 < len(sys.argv):
            config_arg = sys.argv[index + 1]
    if config_arg:
        filename = os.path.basename(config_arg)
        prefix, suffix = "config_board_labplus_", ".mk"
        if filename.startswith(prefix) and filename.endswith(suffix):
            board = filename[len(prefix):-len(suffix)]
            if board == "owl_2024_box":
                board = "owl_box"
            if board in ("owl", "owl_2024", "owl_gansu", "owl_box", "owl_dog",
                         "classroom_kit", "1956", "amigo"):
                sys.argv.extend(["--build-dir", os.path.join("build", board)])

# execute project script from SDK
project_file_path = sdk_path+"/tools/cmake/project.py"
with open(project_file_path) as f:
    exec(f.read())

