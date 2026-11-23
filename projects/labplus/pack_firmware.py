#!/usr/bin/env python3
"""Build a KFlash package for an Owl-family firmware release."""

import argparse
import json
import os
from pathlib import Path
import re
import subprocess
from tempfile import TemporaryDirectory
from zipfile import ZIP_DEFLATED, ZipFile


PROJECT = Path(__file__).resolve().parent
SPIFFS = PROJECT.parents[1] / "tools" / "spiffs"
BOARDS = {
    "owl": "owl",
    "owl_2024": "owl_2024",
    "owl_gansu": "owl_gansu",
    "owl_box": "owl_2024_box",
    "owl_dog": "owl_dog",
}
MODEL_ADDR = 0x300000
FLASH_END = 0x1000000
# KFlash adds a 5-byte boot header and a 32-byte SHA-256 digest.
BOOT_OVERHEAD = 37


def make_spiffs(executable, source, image, config):
    if not source.is_dir():
        raise ValueError(f"SPIFFS source directory not found: {source}")
    if not executable.is_file():
        raise ValueError(f"SPIFFS mkspiffs executable not found: {executable}")

    paths = [executable, source, image]
    if os.name == "nt" and executable.suffix.lower() != ".exe":
        paths = [
            subprocess.check_output(
                ["wsl.exe", "--exec", "wslpath", "-a", str(path.resolve())],
                encoding="utf-8",
            ).strip()
            for path in paths
        ]
        command = ["wsl.exe", "--exec", paths[0]]
    else:
        command = [str(executable.resolve())]

    version = subprocess.check_output([*command, "--version"], encoding="utf-8")
    for key in ("OBJ_NAME_LEN", "USE_MAGIC", "USE_MAGIC_LENGTH"):
        expected = 1 if config[key] == "y" else int(config[key], 0)
        if not re.search(rf"^\s*SPIFFS_{key}:\s*{expected}\s*$", version, re.M):
            raise ValueError(f"SPIFFS mkspiffs build does not match board setting {key}")
    for key, expected in (("OBJ_META_LEN", int(config["META_LENGTH"], 0)),
                          ("ALIGNED_OBJECT_INDEX_TABLES", 1)):
        if not re.search(rf"^\s*SPIFFS_{key}:\s*{expected}\s*$", version, re.M):
            raise ValueError(f"SPIFFS mkspiffs build does not match {key}={expected}")

    subprocess.run([
        *command, "-c", str(paths[1]), "-b", config["LOGICAL_BLOCK_SIZE"],
        "-p", config["LOGICAL_PAGE_SIZE"], "-s", config["SIZE"], str(paths[2]),
    ], check=True)


def pack(args):
    config_path = PROJECT / f"config_board_labplus_{BOARDS[args.board]}.mk"
    config_text = config_path.read_text(encoding="utf-8")
    config = dict(re.findall(r"^CONFIG_SPIFFS_(\w+)=(\S+)", config_text, re.M))
    spiffs_addr = int(config["START_ADDR"], 0)
    spiffs_size = int(config["SIZE"], 0)
    if not MODEL_ADDR < spiffs_addr or spiffs_addr + spiffs_size > FLASH_END:
        raise ValueError("Invalid board SPIFFS partition")

    firmware_size = args.firmware.stat().st_size
    models_size = args.models.stat().st_size
    if not 0 < firmware_size <= MODEL_ADDR - BOOT_OVERHEAD:
        raise ValueError("Firmware must be nonempty and end at or before 0x300000 with its boot header")
    if not 0 < models_size <= spiffs_addr - MODEL_ADDR:
        raise ValueError(f"Model image must be nonempty and end at or before 0x{spiffs_addr:X}")

    output = args.output.resolve()
    inputs = [args.firmware, args.models]
    if args.spiffs:
        inputs.append(args.spiffs)
    if output in [path.resolve() for path in inputs]:
        raise ValueError("Output path matches an input file")
    if output.suffix.lower() != ".kfpkg":
        raise ValueError("Output filename must end in .kfpkg")
    if not args.spiffs and args.fs_dir.resolve() in output.parents:
        raise ValueError("Output must be outside the SPIFFS source directory")
    output.parent.mkdir(parents=True, exist_ok=True)

    with TemporaryDirectory(prefix=".labplus-pack-", dir=str(output.parent)) as directory:
        temp = Path(directory)
        image = args.spiffs
        if image is None:
            image = temp / "maixpy_spiffs.img"
            make_spiffs(args.mkspiffs, args.fs_dir, image, config)
        if image.stat().st_size != spiffs_size:
            raise ValueError(f"SPIFFS image must be exactly 0x{spiffs_size:X} bytes")

        partitions = [
            (args.firmware, "labplus.bin", 0, True),
            (args.models, "0x300000.bin", MODEL_ADDR, False),
            (image, "maixpy_spiffs.img", spiffs_addr, False),
        ]
        temporary_package = temp / "firmware.kfpkg"
        manifest = {"version": "0.1.0", "files": []}
        with ZipFile(temporary_package, "w", ZIP_DEFLATED) as archive:
            for path, name, address, prefix in partitions:
                archive.write(path, name)
                manifest["files"].append({
                    "address": address, "bin": name, "sha256Prefix": prefix,
                })
            archive.writestr("flash-list.json", json.dumps(manifest, indent=4) + "\n")
        os.replace(temporary_package, output)
    print(f"{args.board}: {output}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("-b", "--board", choices=BOARDS, required=True)
    parser.add_argument("--firmware", type=Path, default=PROJECT / "build" / "labplus.bin")
    parser.add_argument("--models", type=Path, help="Raw model image for 0x300000")
    source = parser.add_mutually_exclusive_group()
    source.add_argument("--fs-dir", type=Path, default=SPIFFS / "fs")
    source.add_argument("--spiffs", type=Path, help="Use a prebuilt SPIFFS image")
    mkspiffs = SPIFFS / "mkspiffs" / "mkspiffs"
    if os.name == "nt" and mkspiffs.with_suffix(".exe").is_file():
        mkspiffs = mkspiffs.with_suffix(".exe")
    parser.add_argument("--mkspiffs", type=Path, default=mkspiffs)
    parser.add_argument("-o", "--output", type=Path)
    args = parser.parse_args()
    if args.models is None:
        if args.board != "owl_2024":
            parser.error("--models is required for this board")
        args.models = PROJECT / "k210_model" / "labplus_owl_2024_models_0x300000.bin"
    if args.output is None:
        args.output = PROJECT / "build" / f"labplus_{BOARDS[args.board]}.kfpkg"
    try:
        pack(args)
    except (OSError, ValueError, subprocess.CalledProcessError) as error:
        parser.exit(1, f"error: {error}\n")


if __name__ == "__main__":
    main()
