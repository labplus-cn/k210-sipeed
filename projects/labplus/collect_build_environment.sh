#!/bin/sh

# Record the build environment without changing the source tree or dependencies.
set -u

project_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
default_output="$project_dir/build/build-environment-$(date +%Y-%m-%d_%H%M%S).txt"
output=${1:-$default_output}

if [ "$#" -gt 1 ]; then
    printf 'Usage: %s [output-file]\n' "$0" >&2
    exit 2
fi
if ! mkdir -p -- "$(dirname -- "$output")"; then
    exit 1
fi
# Refuse to overwrite an existing report.
if ! (set -C; : > "$output") 2>/dev/null; then
    printf 'Cannot create report (it may already exist): %s\n' "$output" >&2
    exit 1
fi

{
    printf 'Labplus K210 build environment\n'
    printf 'Collected: %s\n' "$(date '+%Y-%m-%d %H:%M:%S %z')"
    printf 'Project: %s\n' "$project_dir"

    printf '\n[System]\n'
    uname -a
    if [ -r /etc/os-release ]; then
        cat /etc/os-release
    fi

    printf '\n[Build tools]\n'
    for tool in python3 cmake make gcc g++ git; do
        if command -v "$tool" >/dev/null 2>&1; then
            printf '\n%s: %s\n' "$tool" "$(command -v "$tool")"
            "$tool" --version 2>&1 | sed -n '1p'
        else
            printf '\n%s: not found\n' "$tool"
        fi
    done

    printf '\n[K210 toolchain configuration]\n'
    for config in "$project_dir"/config_board_labplus_*.mk "$project_dir/.config.mk"; do
        if [ -f "$config" ]; then
            printf '\n%s\n' "$config"
            sed -n '/^CONFIG_TOOLCHAIN_PATH=/p; /^CONFIG_TOOLCHAIN_PREFIX=/p' "$config"
        fi
    done
    toolchain_from_path=$(command -v riscv64-unknown-elf-gcc 2>/dev/null || true)
    if [ -n "$toolchain_from_path" ]; then
        printf '\nCompiler on PATH: %s\n' "$toolchain_from_path"
        "$toolchain_from_path" --version 2>&1 | sed -n '1p'
    else
        printf '\nCompiler on PATH: not found\n'
    fi
    default_compiler=/opt/kendryte-toolchain/bin/riscv64-unknown-elf-gcc
    if [ -x "$default_compiler" ]; then
        printf '\nDefault compiler: %s\n' "$default_compiler"
        "$default_compiler" --version 2>&1 | sed -n '1p'
    else
        printf '\nDefault compiler: not found at %s\n' "$default_compiler"
    fi

    printf '\n[Python packages]\n'
    if command -v python3 >/dev/null 2>&1; then
        python3 -m pip freeze 2>&1 || printf 'Unable to list Python packages.\n'
    else
        printf 'Python 3 is not available.\n'
    fi

    printf '\n[Git revision and working tree]\n'
    if command -v git >/dev/null 2>&1; then
        git -C "$project_dir" rev-parse HEAD 2>&1
        git -C "$project_dir" status --short 2>&1
        printf '\n[Git submodules]\n'
        git -C "$project_dir" submodule status --recursive 2>&1
    else
        printf 'Git is not available.\n'
    fi
} > "$output" 2>&1

printf 'Build environment report: %s\n' "$output"
