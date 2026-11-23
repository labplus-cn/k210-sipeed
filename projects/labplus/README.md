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
| 1956 | 使用 `project.py` | [配置](config_board_labplus_1956.mk) | 240 × 320 | `0xD00000` / 3 MiB |
| Amigo | 使用 `project.py` | [配置](config_board_labplus_amigo.mk) | 480 × 320 | `0xD00000` / 3 MiB |

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
| 1956 | `python3 project.py build --config_file config_board_labplus_1956.mk` |
| Amigo | `python3 project.py build --config_file config_board_labplus_amigo.mk` |

1956 和 Amigo 通过通用构建入口 `project.py` 显式选择配置，其余板型由 `make.py -b` 选择。

### 切换板型或重新生成配置

所有板型共用 `build/`，编译完成后固件位于 `build/labplus.bin`。切换板型或修改板型配置（例如串口显示名称）后，先清理旧构建，再运行目标板型的编译命令。以下以切换到甘肃 v1 摄像头为例。

```sh
python3 make.py -b owl_gansu clean
python3 make.py -b owl_gansu build
```

`clean` 会删除整个 `build/`，包括之前生成的固件。

## 启动与代码位置

- [main/src/main.cpp](main/src/main.cpp) 调用 MaixPy 的 `maixpy_main()`。[MaixPy 启动代码](../../components/micropython/port/src/maixpy_main.c) 初始化硬件和 MicroPython，挂载 Flash、尝试挂载 SD 卡，再执行固化的 `_boot.py`。
- [builtin_py/](builtin_py/) 保存各板型的启动脚本和外设封装。以标准 Owl 为例，[`_boot.py`](builtin_py/labplus_owl/_boot.py) 导入 [`labplus.py`](builtin_py/labplus_owl/labplus.py)，启动 `AICamera` 并进入 UART 监听。相机、KPU 模型、颜色、二维码、语音和显示功能从这里接入。
- 当前 MaixPy 启动实现只有在固化 `_boot.py` 返回非零且未进入 IDE 调试模式时才尝试执行文件系统的 `boot.py`。处于友好 REPL 模式时还会尝试执行 `main.py`。
- [examples/](examples/) 包含相机、视觉、显示、音频和板级测试示例。[release/](release/) 保存烧录清单、SPIFFS 输入资源、模型和字库。

## 当前发布限制

- `mkfs` 和 `pack` 的清单映射只有 1956、Owl、Classroom Kit。Owl Gansu、Box、2024 和 Dog 缺少对应映射，调用这两个子命令会触发 `KeyError`。
- `mkfs` 传入 `pack -d … -o …`，当前 [SPIFFS 镜像工具](../../tools/spiffs/gen_spiffs_image.py) 只接受板型配置文件路径，且脚本内含固定的 Linux 路径。 `pack` 引用的 `tools/kfpkg/make_kfpkg.py` 在当前仓库中缺失。
- 标准 Owl 的 [烧录清单](release/labplus_owl_manifest.json) 与固件读取地址有差异。下表记录当前源码中的两个值，制作可用烧录包前需核对对应板型的完整 Flash 布局。

| 资源 | 标准 Owl 清单地址 | 标准 Owl 固件地址 |
| --- | --- | --- |
| SPIFFS | `0xD00000` | [`0xF00000`](config_board_labplus_owl.mk#L135) |
| 中文字库 | `0x400000` | [`0xA50000`](builtin_py/labplus_owl/display.py#L39) |
| MNIST | `0x600000` | [`0x610000`](builtin_py/labplus_owl/mnist.py#L16) |

`make.py flash` 固定使用 Linux 串口 `/dev/ttyCH343USB0`，只写入 `build/labplus.bin`。模型、字库和 SPIFFS 镜像需要按板型布局单独写入，或由核对过的烧录包统一写入。
