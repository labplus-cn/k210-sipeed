import sensor, image, lcd
import KPU as kpu
import time

#----------------------------------------------------------
# 内置模型的参数
builtin_models = {
    # face model
    1: {
        'type': 'yolo',
        "classes": ['face'],
        'path': 0x280000,
        'addr': 2621440,
        'anchor': (1.889, 2.5245, 2.9465, 3.94056, 3.99987, 5.3658, 5.155437, 6.92275, 6.718375, 9.01025),

        'pixformat':sensor.RGB565,
        'framesize':sensor.QVGA,
        'hmirror':1,
        'windows': (320, 240),
    },
    # 20classes model
    2: {
        'type': 'yolo',
        "classes": ['aeroplane', 'bicycle', 'bird', 'boat', 'bottle', 'bus', 'car', 'cat', 'chair', 'cow', 'diningtable', 'dog', 'horse', 'motorbike', 'person', 'pottedplant', 'sheep', 'sofa', 'train', 'tvmonitor'],
        'path': 0x300000,
        'addr': 3145728,
        'anchor': (1.08, 1.19, 3.42, 4.41, 6.63, 11.38, 9.42, 5.11, 16.62, 10.52),

        'pixformat':sensor.RGB565,
        'framesize':sensor.QVGA,
        'hmirror':1,
        'windows': (320, 240),
    },
    # mnist model
    3: {
        'type': 'mobilenet',
        'path': 0x200000,
        'addr': 2097152,

        'pixformat':sensor.RGB565,
        'framesize':sensor.QVGA,
        'hmirror':1,
        'windows': (320, 240),
    },
    # 1000classes modele
    4: {
        'type': 'mobilenet',
        'path': 0x500000,
        'addr': 5242880,

        'pixformat':sensor.RGB565,
        'framesize':sensor.QVGA,
        'hmirror':1,
        'windows': (320, 240),
    }
}

#-----------------------------------------------
# 应用主入口
#-----------------------------------------------
class app():
    # kpu 状态
    IDLE = const(0)
    INIT = const(1)
    RUN_ONESHOT = const(2)
    RUN_CONTINUS = const(3)
    DEINIT = const(4)
    MAX_STATE = DEINIT
    state = IDLE
    error = 0
    kpu = None
    img = None
    result = None
    ready = False
    # 模型
    MAX_MODEL_INDEX = const(3)
    model = 0
    new_modle = 0

    #----------------------------------------------------------
    @classmethod
    def _load_module(cls, model_index):
        # 如果已经初始化过KPU,先将其卸载
        if cls.kpu != None and cls.model != model_index:
            kpu.deinit(cls.kpu)
            cls.kpu = None
        if app.img != None:
            del app.img
            app.img = None
        
        # 配置摄像头为模型需要的参数
        sensor.reset()
        m = builtin_models[model_index]
        sensor.set_pixformat(m['pixformat'])
        sensor.set_framesize(m['framesize'])
        sensor.set_hmirror(m['hmirror'])
        sensor.set_windowing(m['windows'])
        sensor.run(1)
        sensor.skip_frames(10)
        app.img = sensor.snapshot()

        # 加载模型
        cls.kpu = kpu.load(m['path'])
        if cls.kpu == None:
            return False
        # YOLO模型需要额外的初始化
        if m['type'] == 'yolo':
            kpu.init_yolo2(cls.kpu, 0.5, 0.3, 5, m['anchor'])
        cls.model = model_index
        return True

    #---------------------------------------------------
    @classmethod
    def _run_model(cls):
        if cls.kpu == None:
            return None
        # 拍照
        app.img = sensor.snapshot()
        # lcd.display(app.img)
        # return None
        
        # AI运算
        if builtin_models[cls.model]['type'] == 'yolo':
            result = kpu.run_yolo2(cls.kpu, app.img)
            if result:
                for i in result:
                    app.img.draw_rectangle(i.rect())
            lcd.display(app.img)
        else:
            result = kpu.forward(cls.kpu, app.img)
            lcd.display(app.img)
        del app.img
        return result

    #--------------------------------------------------------
    @classmethod
    def _deinit(cls):
        if cls.kpu == None:
            return False
        kpu.deinit(cls.kpu)
        cls.kpu = None
        cls.state = cls.IDLE
        return True
    
    # AI线程:根据当前的状态处理不同的任务
    @classmethod
    def do_ai_work(cls):
        # INIT: 初始化KPU,准备运行AI运算
        if cls.state == cls.INIT:
            cls.error = cls._load_module(cls.new_modle)
            cls.ready = False
            cls.result = None
            cls.state = cls.IDLE

        # RUN_CONTINUS: KPU持续运算,结果存储在app.result
        elif cls.state == cls.RUN_CONTINUS:
            cls.result = cls._run_model()
            cls.error = 0
            cls.ready = True
    
        # RUN_ONESHOT: KPU运算一次,结果存储在app.result
        elif cls.state == cls.RUN_ONESHOT:
            cls.result = cls._run_model()
            cls.error = 0
            cls.ready = True
            cls.state = cls.IDLE
        # IDLE: 当前没有需要处理的任务,并且KPU已经释放
        elif cls.state == cls.IDLE:
            # print('ai running....')
            # time.sleep_ms(100)
            pass
        else:
            print('ai error....')
            time.sleep_ms(100)
    
    # public functions
    #=======================================================
    #-------------------------------------------------------
    # 切换运行模式
    @classmethod
    def set_mode(cls, new_mode):
        # 内置模型的范围1-4
        if new_mode in range(1, 5):
            cls.new_modle = new_mode
            cls.state = cls.INIT
            return True
        else:
            return False

    @classmethod
    def start(cls, oneshot=False):
        if cls.state == IDLE and cls.kpu != None:
            cls.ready = False
            if oneshot == True:
                cls.state = cls.RUN_ONESHOT
            else:
                cls.state = cls.RUN_CONTINUS
            return True
        else:
            return False
    
    @classmethod
    def stop(cls):
        if cls.state == cls.RUN_ONESHOT or cls.state == cls.RUN_CONTINUS:
            cls.state = cls.IDLE
            cls.ready = False
    
    #------------------------------------------------------
    # 获取运行结果
    @classmethod
    def get_result(cls):
        if cls.ready:
            cls.ready = False
            return cls.result
        else:
            return None
    #-----------------------------------------------------
    # 获取状态
    @classmethod
    def get_state(cls):
        return (cls.state, cls.ready, cls.model, cls.error)