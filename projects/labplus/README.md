# Labplus K210 固件

本工程为 Labplus 多款 K210 设备构建 MaixPy 固件。板型配置决定 LCD、摄像头、MicroPython 功能开关和 SPIFFS 分区，并通过 `CONFIG_BUILTIN_PY_DIR` 选择要固化进固件的 Python 模块。

## 板型选择

| 板型 | `make.py -b` 参数 | 配置文件 | 默认 LCD | SPIFFS 起始地址 / 容量 |
| --- | --- | --- | --- | --- |
| Owl | `owl` | [配置](config_board_labplus_owl.mk) | 320 × 240 | `0xF00000` / 1 MiB |
| Owl Gansu | `owl_gansu` | [配置](config_board_labplus_owl_gansu.mk) | 320 × 240 | `0xF00000` / 1 MiB |
| Owl Dog | `owl_dog` | [配置](config_board_labplus_owl_dog.mk) | 320 × 240 | `0xF00000` / 1 MiB |
| Owl 2024 | `owl_2024` | [配置](config_board_labplus_owl_2024.mk) | 240 × 240 | `0xF00000` / 1 MiB |
| Owl 2024 Box | `owl_box` | [配置](config_board_labplus_owl_2024_box.mk) | 320 × 240 | `0xF00000` / 1 MiB |
| Classroom Kit | `classroom_kit` | [配置](config_board_labplus_classroom_kit.mk) | 320 × 240 | `0xD00000` / 3 MiB |
| 1956 | `1956` | [配置](config_board_labplus_1956.mk) | 240 × 320 | `0xD00000` / 3 MiB |
| Amigo | `amigo` | [配置](config_board_labplus_amigo.mk) | 480 × 320 | `0xD00000` / 3 MiB |

### 摄像头版本与串口显示

进入 MicroPython 串口 REPL 后，欢迎语会显示下表中的板型名称，后接 `with kendryte-k210`。`os.uname().machine` 也使用同一名称。显示值来自编译时选择的板型配置。

| 摄像头版本 | 构建参数 | 串口显示的板型名称 |
| --- | --- | --- |
| 2.0 摄像头 | `-b owl` | `labplus_owl (2.0摄像头)` |
| 3.1 摄像头 | `-b owl_2024` | `labplus_owl_2024 (3.1摄像头)` |
| 甘肃 v1 摄像头 | `-b owl_gansu` | `labplus_owl_gansu (甘肃v1摄像头)` |

### 模式初始化确认与固件配套

3.1 摄像头和甘肃 v1 摄像头的模式初始化增加了串口确认。主控 `smartcamera_new.py` 的 `switcher_mode()` 和各模式的 `*_init()` 在摄像头确认模型加载成功后才返回；失败或 30 秒内没有收到确认时抛出 `RuntimeError`。失败后可检查供电、接线和模型文件，再重新初始化。

使用该版本主控驱动时，必须同时更新摄像头固件。旧摄像头固件不支持初始化状态查询，无法与该版本主控驱动完成模式初始化。当前修改覆盖 3.1 和甘肃 v1，2.0 及其他板型尚不支持该协议。主控在初始化命令后发送 `01 01 FC` 查询，数据字节为模式号和请求编号；摄像头返回 `01 01 FD`，数据字节为模式号、结果（`1` 成功、`0` 失败）和请求编号。摄像头在初始化失败、退出模式失败或识别处理抛出异常时会发送 `01 FB` 变长错误文本帧；主控将错误文本打印到 REPL 串口日志，并在初始化失败时把文本附加到异常中。主控只接受编号匹配的初始化结果。

## 从源码构建

按[仓库构建文档](../../build.md)初始化 Git 子模块，安装 Python 3、CMake、GNU Make 和 Kendryte RISC-V 交叉工具链。板型配置默认使用 `/opt/kendryte-toolchain/bin` 下的 `riscv64-unknown-elf-` 工具链，路径以实际安装位置为准。

### 迁移前检查编译环境

在实际编译固件的 Linux 机器上，可运行采集脚本，将环境信息保存到带时间戳的 `build/build-environment-*.txt`。

```sh
cd projects/labplus
sh collect_build_environment.sh
```

也可以通过第一个参数指定报告路径，例如 `sh collect_build_environment.sh /tmp/k210-build-environment.txt`。报告包含项目路径、工具版本、Python 包、Git 工作区和子模块状态。报告不会覆盖已有文件。

在实际编译固件的 Linux 终端中进入仓库根目录，记录系统、工具链、Python 依赖和源码状态。

```sh
cat /etc/os-release
uname -m
python3 --version
cmake --version
make --version
gcc --version
g++ --version
command -v riscv64-unknown-elf-gcc
riscv64-unknown-elf-gcc --version
python3 -m pip freeze
git rev-parse HEAD
git status --short
git submodule status --recursive
```

如果交叉编译器未加入 `PATH`，检查板型配置中指定的默认位置。

```sh
ls -l /opt/kendryte-toolchain/bin/riscv64-unknown-elf-gcc
/opt/kendryte-toolchain/bin/riscv64-unknown-elf-gcc --version
```

在目标 Mac 的终端检查系统版本和 CPU 架构。

```sh
uname -m
sw_vers
```

这些信息用于确认编译器可执行文件的架构和需要迁移的子模块。工具链目录可能在板型配置或本地 `.config.mk` 中被覆盖。

### 按板型编译

从仓库根目录进入 Labplus 工程。

```sh
cd projects/labplus
```

在该目录运行对应的一条命令。

| 板型 | 编译命令 |
| --- | --- |
| Owl（2.0 摄像头） | `python3 make.py -b owl build` |
| Owl 2024（3.1 摄像头） | `python3 make.py -b owl_2024 build` |
| Owl Gansu（甘肃 v1 摄像头） | `python3 make.py -b owl_gansu build` |
| Owl 2024 Box | `python3 make.py -b owl_box build` |
| Owl Dog | `python3 make.py -b owl_dog build` |
| Classroom Kit | `python3 make.py -b classroom_kit build` |
| 1956 | `python3 make.py -b 1956 build` |
| Amigo | `python3 make.py -b amigo build` |

也可以通过通用入口选择配置，例如 `python3 project.py build --config_file config_board_labplus_1956.mk`。

### 切换板型或重新生成配置

各板型使用独立的 `build/<板型>/` 目录。例如 3.1 摄像头的固件位于 `build/owl_2024/labplus.bin`，甘肃版位于 `build/owl_gansu/labplus.bin`。切换板型可直接编译，修改某个板型的配置后可清理该板型再重新编译。

```sh
python3 make.py -b owl_gansu clean
python3 make.py -b owl_gansu build
```

`clean` 删除所选板型的构建目录及其中的固件。

## 一条命令打包三分区固件

编译得到 `build/owl_2024/labplus.bin` 后，在 `projects/labplus` 目录运行以下 PowerShell 命令，为 3.1 摄像头生成 `build/owl_2024/labplus_owl_2024_package-YYYY-MM-DD.kfpkg`。日期使用打包当天的本地日期，同一天重复打包会覆盖同名文件。

```powershell
py -3 .\pack_firmware.py -b owl_2024
```

在 Linux 或 WSL 中执行同样的打包操作。

```sh
python3 pack_firmware.py -b owl_2024
```

脚本按板型配置将 [`spiffs/fs`](spiffs/fs/) 中的文件生成 SPIFFS 镜像，保存到 `build/owl_2024/maixpy_spiffs.img`，并和主程序、模型一起写入 KFlash 烧录包。单独生成镜像可在 Linux 中运行以下命令。

```sh
python3 make.py -b owl_2024 mkfs
```

| Flash 地址 | 输入 |
| --- | --- |
| `0x000000` | 主程序，默认 `build/<板型>/labplus.bin` |
| `0x300000` | 3.1 默认使用 [模型分区镜像](k210_model/labplus_owl_2024_models_0x300000.bin) |
| `0xF00000` | 由 SPIFFS 源文件目录生成的 1 MiB 镜像 |

默认从 `tools/spiffs/mkspiffs` 源码临时编译镜像工具，Windows 通过 WSL 执行，环境需具备 Python 3、make、GCC、G++ 和已初始化的嵌套 SPIFFS 子模块。也可用 `--mkspiffs` 指定采用 MaixPy SPIFFS 格式的现成可执行文件。脚本接受 `--firmware`、`--fs-dir` 和 `--output`，已有 SPIFFS 镜像时可用 `--spiffs` 指定。

3.1 模型镜像由原来的 `0x300000_20241018.bin` 重命名而来。其他 Owl 板型通过 `--models` 显式指定对应的模型分区镜像，3.1 也可用该参数覆盖默认值。脚本检查分区重叠和 SPIFFS 镜像大小，主程序和模型镜像需与所选板型对应。打包命令生成文件，实际烧录由 KFlash 完成。

| 板型 | 项目内的组合模型镜像 |
| --- | --- |
| Owl（2.0） | [owl/0x300000.bin](k210_model/owl/0x300000.bin) |
| Owl 2024（3.1） | [labplus_owl_2024_models_0x300000.bin](k210_model/labplus_owl_2024_models_0x300000.bin) |
| Owl Gansu（甘肃 v1） | [owl_gansu/0x300000-c50000.bin](k210_model/owl_gansu/0x300000-c50000.bin) |

`owl_gansu/0x300000.bin` 包含 SPIFFS 地址范围，三分区打包时使用上表中的 `0x300000-c50000.bin`。例如，在工程目录执行甘肃版打包命令。

```powershell
py -3 .\pack_firmware.py -b owl_gansu --models .\k210_model\owl_gansu\0x300000-c50000.bin
```

## 启动与代码位置

- [main/src/main.cpp](main/src/main.cpp) 调用 MaixPy 的 `maixpy_main()`。[MaixPy 启动代码](../../components/micropython/port/src/maixpy_main.c) 初始化硬件和 MicroPython，挂载 Flash、尝试挂载 SD 卡，再执行固化的 `_boot.py`。
- [builtin_py/](builtin_py/) 保存各板型的启动脚本和外设封装。以标准 Owl 为例，[`_boot.py`](builtin_py/labplus_owl/_boot.py) 导入 [`labplus.py`](builtin_py/labplus_owl/labplus.py)，启动 `AICamera` 并进入 UART 监听。相机、KPU 模型、颜色、二维码、语音和显示功能从这里接入。
- 当前 MaixPy 启动实现只有在固化 `_boot.py` 返回非零且未进入 IDE 调试模式时才尝试执行文件系统的 `boot.py`。处于友好 REPL 模式时还会尝试执行 `main.py`。
- [examples/](examples/) 包含相机、视觉、显示、音频和板级测试示例。[release/](release/) 保存烧录清单、SPIFFS 输入资源、模型和字库。

## 当前发布限制

- 旧版 `make.py pack` 的清单映射只有 1956、Owl、Classroom Kit，并且引用的 `tools/kfpkg/make_kfpkg.py` 在当前仓库中缺失。三分区打包使用 `pack_firmware.py`。
- 标准 Owl 的 [烧录清单](release/labplus_owl_manifest.json) 与固件读取地址有差异。下表记录当前源码中的两个值，制作可用烧录包前需核对对应板型的完整 Flash 布局。

| 资源 | 标准 Owl 清单地址 | 标准 Owl 固件地址 |
| --- | --- | --- |
| SPIFFS | `0xD00000` | [`0xF00000`](config_board_labplus_owl.mk#L135) |
| 中文字库 | `0x400000` | [`0xA50000`](builtin_py/labplus_owl/display.py#L39) |
| MNIST | `0x600000` | [`0x610000`](builtin_py/labplus_owl/mnist.py#L16) |

`make.py flash` 固定使用 Linux 串口 `/dev/ttyCH343USB0`，写入所选板型目录下的 `labplus.bin`。模型、字库和 SPIFFS 镜像需要按板型布局单独写入，或由核对过的烧录包统一写入。
