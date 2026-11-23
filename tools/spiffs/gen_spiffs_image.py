#!/usr/bin/env python3
"""Generate a SPIFFS image using a project's firmware configuration."""

import argparse
from pathlib import Path
import re
import shutil
import subprocess
import tempfile


TOOLS_DIR = Path(__file__).resolve().parent
MKSPIFFS_DIR = TOOLS_DIR / "mkspiffs"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("config_file", type=Path, help="Configuration used to build the firmware")
    parser.add_argument("-d", "--dir", type=Path, help="SPIFFS source directory")
    parser.add_argument("-o", "--out", type=Path, help="Output image path")
    args = parser.parse_args()
    config_file = args.config_file.resolve()
    if not config_file.is_file():
        parser.error("configuration file not found: {}".format(config_file))

    project = next((parent for parent in config_file.parents
                    if (parent / "CMakeLists.txt").is_file()
                    and (parent / "main").is_dir()), None)
    if project is None:
        parser.error("could not find a project directory above {}".format(config_file))

    project_fs = project / "spiffs" / "fs"
    in_dir = args.dir.resolve() if args.dir else (project_fs if project_fs.is_dir() else TOOLS_DIR / "fs")
    if not in_dir.is_dir():
        parser.error("SPIFFS source directory not found: {}".format(in_dir))

    config = dict(re.findall(r"^CONFIG_SPIFFS_(\w+)=(\S+)",
                             config_file.read_text(encoding="utf-8"), re.MULTILINE))
    required = ("SIZE", "START_ADDR", "LOGICAL_BLOCK_SIZE", "LOGICAL_PAGE_SIZE")
    missing = [key for key in required if key not in config]
    if missing:
        parser.error("missing SPIFFS configuration: {}".format(", ".join(missing)))

    board_prefix = "config_board_labplus_"
    if config_file.name.startswith(board_prefix) and config_file.suffix == ".mk":
        board = config_file.stem[len(board_prefix):]
        if board == "owl_2024_box":
            board = "owl_box"
        out_dir = project / "build" / board
    elif config_file.name == "global_config.mk" and config_file.parent.name == "config":
        out_dir = config_file.parent.parent
    else:
        out_dir = project / "build"
    image = args.out.resolve() if args.out else out_dir / "maixpy_spiffs.img"
    out_dir = image.parent

    if not (MKSPIFFS_DIR / "spiffs" / "src" / "spiffs.h").is_file():
        parser.error("mkspiffs source or SPIFFS submodule is missing: {}".format(MKSPIFFS_DIR))

    flags = ["-DSPIFFS_{}={}".format(key, "1" if value == "y" else value)
             for key, value in config.items() if value != "n"]
    flags.extend(["-DSPIFFS_READ_ONLY=0", "-DSPIFFS_ALIGNED_OBJECT_INDEX_TABLES=1",
                  "-DSPIFFS_SINGLETON=0", "-DSPIFFS_HAL_CALLBACK_EXTRA=0"])
    try:
        with tempfile.TemporaryDirectory(prefix="labplus-mkspiffs-") as temp:
            build = Path(temp) / "mkspiffs"
            build.mkdir()
            for directory in ("include", "tclap"):
                shutil.copytree(MKSPIFFS_DIR / directory, build / directory)
            (build / "spiffs").mkdir()
            shutil.copytree(MKSPIFFS_DIR / "spiffs" / "src", build / "spiffs" / "src",
                            ignore=shutil.ignore_patterns("*.o"))
            for name in ("Makefile", "main.cpp"):
                shutil.copy2(MKSPIFFS_DIR / name, build / name)
            subprocess.run(["make", "VERSION=local", "SPIFFS_VERSION=local",
                            "BUILD_CONFIG_NAME=-maixpy", "CPPFLAGS=" + " ".join(flags)],
                           cwd=str(build), check=True)
            out_dir.mkdir(parents=True, exist_ok=True)
            subprocess.run([str(build / "mkspiffs"), "-c", str(in_dir),
                            "-b", str(int(config["LOGICAL_BLOCK_SIZE"], 0)),
                            "-p", str(int(config["LOGICAL_PAGE_SIZE"], 0)),
                            "-s", str(int(config["SIZE"], 0)), str(image)], check=True)
    except (OSError, subprocess.CalledProcessError) as error:
        parser.exit(1, "error: {}\n".format(error))

    print("[SUCCESS] image: {}".format(image))
    print("[USAGE] flash at 0x{:X}".format(int(config["START_ADDR"], 0)))


if __name__ == "__main__":
    main()
