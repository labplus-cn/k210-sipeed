import sys,getopt
import usb.core
import usb.util

def main(args):
    usage_msg = 'usage: ' + args[0] + '\t[-h | --help]  [-t <TARGET>] [--target=<TARGET>]\r\n'
    help_msg = 'option arguments:\r\n' + '  -t <TARGET>, --target=<TARGET\t\tselect the target. e.g. esp32, k210'
    try:
        opts, argv = getopt.getopt(args[1:], 'ht:', ['help', 'target='])
    except getopt.GetoptError as err:
        print(usage_msg)
        print(err)
        sys.exit(2)
    
    for opt, arg in opts:
        if opt in ('-h', '--help'):
            print(usage_msg)
            print(help_msg)
        elif opt in ('-t', '--target') and arg in ('esp32', 'k210'):
            vid = 0x10c4
            pid = 0xea60
            reqType = 0x41
            bReq = 0xff
            wVal = 0x37E1
            wIndex = 0x00ff
            if arg == 'k210':
                wIndex = 0x00ff
            else:
                wIndex = 0xffff
            dev = usb.core.find(idVendor=vid, idProduct=pid)
            if dev == None:
                print("not find cp2104")
                exit(2)
            dev.ctrl_transfer(reqType, bReq, wVal, wIndex)
        else:
            print('not support arguments')

if __name__ == '__main__':
    main(sys.argv)