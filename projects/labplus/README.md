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

## 从源码构建

按[仓库构建文档](../../build.md)初始化 Git 子模块，安装 Python 3、CMake、GNU Make 和 Kendryte RISC-V 交叉工具链。板型配置默认使用 `/opt/kendryte-toolchain/bin` 下的 `riscv64-unknown-elf-` 工具链，路径以实际安装位置为准。

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

编译得到 `build/owl_2024/labplus.bin` 后，在 `projects/labplus` 目录运行以下 PowerShell 命令，为 3.1 摄像头生成 `build/owl_2024/labplus_owl_2024.kfpkg`。

```powershell
py -3 .\pack_firmware.py -b owl_2024
```

在 Linux 或 WSL 中执行同样的打包操作。

```sh
python3 pack_firmware.py -b owl_2024
```

脚本按板型配置将 [`tools/spiffs/fs`](../../tools/spiffs/fs/) 生成 SPIFFS 镜像，和主程序、模型一起写入 KFlash 烧录包。

| Flash 地址 | 输入 |
| --- | --- |
| `0x000000` | 主程序，默认 `build/<板型>/labplus.bin` |
| `0x300000` | 3.1 默认使用 [模型分区镜像](k210_model/labplus_owl_2024_models_0x300000.bin) |
| `0xF00000` | 由 SPIFFS 源文件目录生成的 1 MiB 镜像 |

默认使用 `tools/spiffs/mkspiffs/mkspiffs`。Windows 可使用同目录的 `mkspiffs.exe`，或通过 WSL 运行 Linux 版本。若工具位于其他位置，用 `--mkspiffs` 指定编译时采用 MaixPy SPIFFS 格式的可执行文件。脚本也接受 `--firmware`、`--fs-dir` 和 `--output`，已有 SPIFFS 镜像时可用 `--spiffs` 代替源文件目录。

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

- 旧版 `make.py mkfs` 和 `make.py pack` 的清单映射只有 1956、Owl、Classroom Kit。Owl Gansu、Box、2024 和 Dog 缺少对应映射，调用这两个子命令会触发 `KeyError`。
- `mkfs` 传入 `pack -d … -o …`，当前 [SPIFFS 镜像工具](../../tools/spiffs/gen_spiffs_image.py) 只接受板型配置文件路径，且脚本内含固定的 Linux 路径。 `pack` 引用的 `tools/kfpkg/make_kfpkg.py` 在当前仓库中缺失。
- 标准 Owl 的 [烧录清单](release/labplus_owl_manifest.json) 与固件读取地址有差异。下表记录当前源码中的两个值，制作可用烧录包前需核对对应板型的完整 Flash 布局。

| 资源 | 标准 Owl 清单地址 | 标准 Owl 固件地址 |
| --- | --- | --- |
| SPIFFS | `0xD00000` | [`0xF00000`](config_board_labplus_owl.mk#L135) |
| 中文字库 | `0x400000` | [`0xA50000`](builtin_py/labplus_owl/display.py#L39) |
| MNIST | `0x600000` | [`0x610000`](builtin_py/labplus_owl/mnist.py#L16) |

`make.py flash` 固定使用 Linux 串口 `/dev/ttyCH343USB0`，写入所选板型目录下的 `labplus.bin`。模型、字库和 SPIFFS 镜像需要按板型布局单独写入，或由核对过的烧录包统一写入。
