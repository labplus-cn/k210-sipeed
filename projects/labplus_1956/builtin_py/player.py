from Maix import I2S
from fpioa_manager import *
from board import * 
import audio

# 分配引脚
fm.register(34, fm.fpioa.I2S0_OUT_D0)
fm.register(33, fm.fpioa.I2S0_WS)
fm.register(35, fm.fpioa.I2S0_SCLK)

# 初始化I2S输出
i2s_spk = I2S(I2S.DEVICE_0)
# i2s_spk.channel_config(i2s_spk.CHANNEL_0, I2S.TRANSMITTER, resolution=I2S.RESOLUTION_16_BIT, cycles=I2S.SCLK_CYCLES_16, align_mode = I2S.STANDARD_MODE)
i2s_spk.channel_config(i2s_spk.CHANNEL_0, I2S.TRANSMITTER, resolution=I2S.RESOLUTION_16_BIT, cycles=I2S.SCLK_CYCLES_16, align_mode = I2S.LEFT_JUSTIFYING_MODE)


# i2s_spk.channel_config(I2S.CHANNEL_0, I2S.TRANSMITTER, align_mode=I2S.STANDARD_MODE, cycles=SCLK_CYCLES_16)
# i2s_spk.set_sample_rate(44000)

def play(filename, mode):
    # 初始化音频
    player = audio.Audio(path=filename)
    wave_info = player.play_process(i2s_spk)    # 获取音频文件信息
    # print("wav file head information:", wave_info)
    # 根据音频文件信息配置I2S设备
    i2s_spk.set_sample_rate(wave_info[1])
    # 启动播放
    while True:
        ret = player.play()
        if ret == None:
            # print('format error')
            break
        if ret == 0:
            # print('play end')
            break
    player.finish()




