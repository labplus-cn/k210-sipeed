import image
import flash
import ustruct

class Font(object):

    def __init__(self, font_address=0x400000):
        self.font_address = font_address
        buffer = bytearray(18)
        flash.read(self.font_address, buffer)
        self.header, \
            self.height, \
            self.width, \
            self.baseline, \
            self.x_height, \
            self.Y_height, \
            self.first_char,\
            self.last_char = ustruct.unpack('4sHHHHHHH', buffer)
        self.first_char_info_address = self.font_address + 18

    def GetCharacterData(self, c):
        uni = ord(c)
        # if uni not in range(self.first_char, self.last_char):
        #     return None
        if (uni < self.first_char or uni > self.last_char):
            return None
        char_info_address = self.first_char_info_address + \
            (uni - self.first_char) * 6
        buffer = bytearray(6)
        flash.read(char_info_address, buffer)
        ptr_char_data, len = ustruct.unpack('IH', buffer)
        if (ptr_char_data) == 0 or (len == 0):
            return None
        buffer = bytearray(len)
        flash.read(ptr_char_data + self.font_address, buffer)
        return buffer

# 加载字体
font_noto_sans = Font(font_address=0xa50000)

def Draw_CJK_String(s, x, y, img, color=(255, 255, 255), font=font_noto_sans):
    """Draw_CJK_String 在img上显示unicode字符串,支持CJK字符集
    
    Parameters
    ----------
    s : string
        要显示的字符串
    x : int
        字符串起始x坐标
    y : int
        字符串起始y坐标
    img : image
        绘图image对象,字符串被渲染到该图像
    color : tuple, optional
        RGB888, by default (255, 255, 255)
    font : Font, optional
        显示字体, by default font_noto_sans
    
    Returns
    -------
    (width, (xe,ye))
        width,字符串总宽度
        (xe,ye),字符串结束位置坐标
    
    Raises
    ------
    Exception
        [description]
    """
    if font is None:
        raise Exception('font load failed')
    row = 0
    str_width = 0
    anchor = x
    last = None
    # 从s中取字符
    for c in s:
        # 处理连续的\r\n
        if last == '\r' and c == '\n':
            continue
        # 处理\r或\n
        if c == '\r' or c == '\n':    
            x = anchor
            y = y + font.Y_height
        # 获取字符位图
        data = font.GetCharacterData(c)
        last = c
        # 无数据的字符跳过一个字体字符宽度
        if data is None:
            x = x + font.width
            continue
        width, bytes_per_line = ustruct.unpack('HH', data[:4]) # width,字符宽度,字符每行占用的字节数
        # print('character [%d]: width = %d, bytes_per_line = %d' % (ord(c), width, bytes_per_line))
        # 超出边界自动换行,到达末端后自动归零
        '''
        if x > img.width() - width:
            str_width +=img.width() - x
            x = 0
            row += 1
            y += font.height
            if y > (img.height() - font.height)+0: y, row = 0, 0
        '''
    
        for h in range(0, font.height):
            w = 0
            i = 0
            while w < width:
                mask = data[4 + h * bytes_per_line + i]
                if (width - w) >= 8:
                    n = 8
                else:
                    n = width - w
                cy = y + h
                for p in range(0, n):
                    cx = x + w + p
                    if (mask & 0x80) != 0:
                        img.set_pixel(cx, cy, color)
                    mask = mask << 1
                w = w + 8
                i = i + 1
        x = x + width + 1
        str_width += width + 1
    return (str_width-1,(x-1, y))