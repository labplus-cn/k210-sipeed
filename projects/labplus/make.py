#!/usr/bin/env python
#-*- coding = utf-8 -*-

import sys, os
import argparse
import json

manifest_lists = {
    "1956": "release/labplus_1956_manifest.json",
    "owl": "release/labplus_owl_manifest.json",
    "classroom_kit": "release/labplus_classroom_kit_manifest.json"
}

build_dir = "build"

cwd = sys.path[0]

# get SDK absolute path
sdk_path = os.path.abspath(sys.path[0]+"/../../")
try:
    sdk_path = os.environ[sdk_env_name]
except Exception:
    pass
print("-- SDK_PATH:{}".format(sdk_path))


def main():
    parser = argparse.ArgumentParser("make labplus K210 projects")
    parser.add_argument('--board','-b', choices=['1956', 'owl', 'classroom_kit', 'owl_dog'], help='选择合适的板子, python3 make.py -b owl build', required=True)

    subparsers = parser.add_subparsers(dest='subcommand',help='select the task')

    cmd_build = subparsers.add_parser('build', help='build the special board')
    cmd_build.set_defaults(func=build)

    cmd_mkfs = subparsers.add_parser('mkfs', help='make a file system image')
    cmd_mkfs.add_argument('--dir', '-d', help='input files dir', action='store_const', const=None)
    cmd_mkfs.add_argument('--out', '-o', help='output image file', action='store_const', const=None)
    cmd_mkfs.set_defaults(func=mkfs)

    cmd_pack = subparsers.add_parser('pack', help='pack all files in to a .kfpgk files')
    cmd_pack.set_defaults(func=pack)

    cmd_flash = subparsers.add_parser('flash', help='download the bin to k210')
    cmd_flash.set_defaults(func=flash)

    cmd_clean = subparsers.add_parser('clean', help='clean build files')
    cmd_clean.set_defaults(func=clean)

    args = parser.parse_args()
    if args.subcommand is None:
        parser.print_help()
        parser.exit(1)
    args.func(args)



def build(args):
    if args.board == '1956':
        sys.argv = [sys.argv[0], 'build', '--config_file', 'config_board_labplus_1956.mk']
    if args.board == 'owl':
        sys.argv = [sys.argv[0], 'build', '--config_file', 'config_board_labplus_owl.mk']
    if args.board == 'owl_dog':
        sys.argv = [sys.argv[0], 'build', '--config_file', 'config_board_labplus_owl_dog.mk']
    if args.board == 'classroom_kit':
        sys.argv = [sys.argv[0], 'build', '--config_file', 'config_board_labplus_classroom_kit.mk']
    if args.board == 'amigo':
        sys.argv = [sys.argv[0], 'build', '--config_file', 'config_board_labplus_amigo.mk']
    os.environ['BOARD_NAME'] = args.board

    sdk_env_name = "MY_SDK_PATH"

    # 1. build application bin
    # execute project script from SDK
    project_file_path = sdk_path+"/tools/cmake/project.py"
    with open(project_file_path) as f:
        exec(f.read())

def mkfs(args):
    with open(os.path.join(cwd, manifest_lists[args.board]), 'r') as f:
        parameters = json.loads(f.read())
        indir = parameters['filesystem']['indir']
        image = parameters['filesystem']['image']

    os.chdir(sys.path[0])
    # 2. construct the file system image
    cmd = 'python3 ' + os.path.join(sdk_path, 'tools/spiffs/gen_spiffs_image.py') + \
        ' pack -d ' + indir + \
        ' -o ' + os.path.join(build_dir, image)
    os.system(cmd)

def pack(args):
    os.chdir(sys.path[0])
    files = ''
    with open(os.path.join(cwd, manifest_lists[args.board]), 'r') as f:
        parameters = json.loads(f.read())
        files = files + " -f 0 {}/{}".format(build_dir, parameters['application'])
        files = files + " -f {} {}/{}".format(int(parameters['filesystem']['addr'], base=16), build_dir, parameters['filesystem']['image'])
        # 3. 增加模型文件
        extras = parameters['extras']
        for extra in extras:
            files = files + " -f {} {}".format(int(extra['addr'], base=16), extra['bin'])

    # 打包kfpgk
    tag_version = os.popen("git describe --dirty --always").readline().strip()
    kfpgk_name = '-'.join((args.board, tag_version))
    cmd = 'python3 ' + os.path.join(sdk_path, 'tools/kfpkg/make_kfpkg.py') + \
        files + \
        ' -o release/kfpkg/{}'.format(kfpgk_name)  
    print(cmd)
    os.system(cmd)

def flash(args):
    # import usb.core
    # import usb.util
    # change cp2104 connect to k210
    # dev = usb.core.find(idVendor=0x10c4, idProduct=0xea60)
    # if dev == None:
    #     print('not found cp2104 devices')
    #     exit(2)
    # dev.ctrl_transfer(0x41, 0xff, 0x37E1, 0x0004)   # set CP2104.GPIO2 = 0

    cmd = 'kflash' + '  -B kd233 -p /dev/ttyUSB0 -b 1500000' + ' build/labplus.bin'
    os.system(cmd)
    
    # dev.ctrl_transfer(0x41, 0xff, 0x37E1, 0x0404)   # set CP2104.GPIO2 = 1

def clean(args):
    import shutil
    if os.path.exists("./build"):
        shutil.rmtree("./build")
        print("cleaned.. ")

if __name__ == "__main__":
    main()
