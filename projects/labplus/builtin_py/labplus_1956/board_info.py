from Maix import FPIOA

class Board_Info:
    def __init__(self):
        self.pin_num = 48
        self.M3_A = 0
        self.M3_B = 1
        self.M4_A = 2
        self.M4_B = 3
        self.ISP_RX = 4
        self.ISP_TX = 5
        self.ESP32_TX = 6
        self.ESP32_RX = 7
        self.SPI_nCS = 8
        self.SPI_MISO = 9
        self.SPI_MOSI = 10
        self.SPI_SCK = 11
        self.M1_A = 12
        self.M1_B = 13
        self.M2_A = 14
        self.M2_B = 15
        self.BOOT_KEY = 16
        self.MA_EN = 17
        self.MIC_ARRAY_BCK = 18
        self.MIC_ARRAY_WS = 19
        self.MIC_ARRAY_DATA3 = 20
        self.SPK_BCK = 21
        self.SPK_WS = 22
        self.SPK_DO = 23
        self.LED = 24
        self.PIN25 = 25
        self.PIN26 = 26
        self.PM_IRQ = 27
        self.PM_SCL = 28
        self.PM_SDA = 29
        self.SD_SCK = 30
        self.SD_MISO = 31
        self.SD_nCS = 32
        self.SD_MOSI = 33
        self.LCD_BL = 34
        self.PIN35 = 35
        self.LCD_CS = 36
        self.LCD_RST = 37	
        self.LCD_DC = 38
        self.LCD_WR = 39
        self.DVP_SDA = 40
        self.DVP_SCL = 41
        self.DVP_RST = 42
        self.DVP_VSYNC = 43
        self.DVP_PWDN = 44
        self.DVP_HSYNC = 45
        self.DVP_XCLK = 46
        self.DVP_PCLK = 47
        self.pin_name=['M3_A','M3_B','M4_A','M4_B','ISP_RX','ISP_TX','ESP32_TX ','ESP32_RX ','SPI_nCS ','SPI_MISO','SPI_MOSI','SPI_SCK','M1_A','M1_B','M2_A','M2_B','BOOT_KEY','MA_EN','MIC_ARRAY_BCK','MIC_ARRAY_WS ','MIC_ARRAY_DATA3','SPK_BCK','SPK_WS','SPK_DO','LED','PIN25','PIN26','PM_IRQ ','PM_SCL','PM_SDA','SD_SCK','SD_MISO','SD_nCS','SD_MOSI','LCD_BL','PIN35','LCD_CS','LCD_RST','LCD_DC','LCD_WR ','DVP_SDA','DVP_SCL','DVP_RST','DVP_VSYNC','DVP_PWDN','DVP_HSYNC','DVP_XCLK','DVP_PCLK']
        self.D = [4, 5, 21, 22, 23, 24, 32, 15, 14, 13, 12, 11, 10, 3]

    def pin_map(self,Pin = None):
        num_len = 10
        str_len = 23
        if Pin == None :
            num_sum_length = num_len
            str_sum_length = str_len
            Pin_str_obj = "Pin"
            Pin_str_obj_length = len(Pin_str_obj)
            Pin_str_obj_front = 3
            Pin_str_obj_rear = num_sum_length - Pin_str_obj_front - Pin_str_obj_front
            fun_str_obj = "Function"
            fun_str_obj_length = len(fun_str_obj)
            fun_str_obj_front = 5
            fun_str_obj_rear = str_sum_length - fun_str_obj_front - fun_str_obj_length
            print("|%s%s%s|%s%s%s|"%(str(Pin_str_obj_front * '-'),Pin_str_obj,str(Pin_str_obj_rear * '-'),str(fun_str_obj_front * '-'),fun_str_obj,str(fun_str_obj_rear*'-')))
            for i in range(0,len(self.pin_name)):
                num = str(i)
                num_length = len(num)
                num_front = 3
                num_rear = num_sum_length - num_front - num_length
                str_length = len(self.pin_name[i])
                str_front = 5
                str_rear = str_sum_length - str_front - str_length
                print("|%s%d%s|%s%s%s|"%(str(num_front * ' '),i,str(num_rear * ' '),str(str_front * ' '),self.pin_name[i],str(str_rear*' ')))
                print("+%s|%s+"%(str(num_sum_length*'-'),str(str_sum_length*'-')))
        elif isinstance(Pin,int) and Pin < 0 or Pin > 47:
            print("Pin num must in range[0,47]")
            return False
        elif isinstance(Pin,int):
            Pin_sum_length = num_len
            string_sum_length = str_len
            pin_str_obj = "Pin"
            pin_str_obj_length = len(pin_str_obj)
            pin_str_obj_front = 3
            pin_str_obj_rear = Pin_sum_length - pin_str_obj_front - pin_str_obj_front
            Fun_str_obj = "Function"
            Fun_str_obj_length = len(Fun_str_obj)
            Fun_str_obj_front = 5
            Fun_str_obj_rear = string_sum_length - Fun_str_obj_front - Fun_str_obj_length
            print("|%s%s%s|%s%s%s|"%(str(pin_str_obj_front * '-'),pin_str_obj,str(pin_str_obj_rear * '-'),str(Fun_str_obj_front * '-'),Fun_str_obj,str(Fun_str_obj_rear*'-')))
            Pin_str = str(Pin)
            Pin_length = len(Pin_str)
            Pin_front = 3
            Pin_rear = Pin_sum_length - Pin_front - Pin_length
            string_length = len(self.pin_name[Pin])
            string_front = 5
            string_rear = string_sum_length - string_front - string_length
            print("|%s%d%s|%s%s%s|"%(str(Pin_front * ' '),Pin,str(Pin_rear * ' '),str(string_front * ' '),self.pin_name[Pin],str(string_rear*' ')))
            print("+%s|%s+"%(str(Pin_sum_length*'-'),str(string_sum_length*'-')))
        else:
            print("Unknow error")
            return False
