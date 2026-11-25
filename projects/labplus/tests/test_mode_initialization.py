"""Device mode initialization and resource-release regressions."""

import ast
import gc
from pathlib import Path
from types import SimpleNamespace
import unittest

PROJECT = Path(__file__).resolve().parents[1]
BOARDS = ("labplus_owl_2024", "labplus_owl_gansu")


def load_camera(board):
    path = PROJECT / "builtin_py" / board / "labplus.py"
    tree = ast.parse(path.read_text(encoding="utf-8"))
    nodes = [n for n in tree.body if isinstance(n, ast.Assign) and
             all(isinstance(t, ast.Name) for t in n.targets) and
             isinstance(n.value, ast.Constant) and isinstance(n.value.value, int)]
    nodes += [n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == "AICamera"]
    env = {"gc": gc, "time": SimpleNamespace(sleep=lambda _: None, sleep_ms=lambda _: None),
           "sensor": SimpleNamespace(QVGA=1, RGB565=2)}
    exec(compile(ast.Module(body=nodes, type_ignores=[]), str(path), "exec"), env)
    camera = object.__new__(env["AICamera"])
    camera.k210 = camera.K210()
    camera._uart_rx = bytearray()
    camera.uart = SimpleNamespace(write=lambda data: camera.responses.append(bytes(data)))
    camera.responses = []
    camera._uart_read_pending = lambda: None
    camera.lcd = SimpleNamespace(draw_string=lambda *a: None, WHITE=1, BLUE=2)
    camera.sensor = object()
    camera.kpu = object()
    for attr in camera._MODE_OBJECTS.values():
        setattr(camera, attr, None)
    return camera, env


def send_fixed(camera, mode, action, value=0, extra=0):
    packet = [0xAA, 0xBB, 1, mode, action, value, extra, 0, 0, 0, 0, 0, 0]
    packet.append(sum(packet) & 255)
    camera._uart_rx.extend(packet)
    camera.uart_handle()


def send_string(camera, mode, action, value):
    content = value.encode("utf-8")
    header = bytes((0xAA, 0xBB, 2, mode, action, 0, 0, 0))
    checksum = (sum(header) + sum(content)) & 0xFF
    camera._uart_rx.extend(header + bytes((len(content),)) + content + bytes((checksum,)))
    camera.uart_handle()


class ModeInitTests(unittest.TestCase):
    def test_success_and_failure_acknowledgement(self):
        for board in BOARDS:
            with self.subTest(board=board):
                camera, env = load_camera(board)
                env["FACE_DETECT"] = lambda **kw: SimpleNamespace()
                send_fixed(camera, 4, 1)
                self.assertEqual(camera.responses[-1][2:7], bytes((1, 1, 0xFD, 4, 1)))
                self.assertEqual(camera.k210.mode, 4)
                def fail(**kwargs):
                    raise RuntimeError("model load failed")
                env["FACE_DETECT"] = fail
                send_fixed(camera, 4, 1)
                self.assertEqual(camera.responses[-1][2:7], bytes((1, 1, 0xFD, 4, 0)))
                self.assertEqual(camera.k210.mode, 1)
                self.assertIsNone(camera.face_detect)

    def test_repeated_init_releases_old_object_before_loading(self):
        for board in BOARDS:
            with self.subTest(board=board):
                camera, env = load_camera(board)
                events = []
                class FakeModel:
                    def __init__(self, **kwargs):
                        self.live = True
                        self.events = events
                        self.events.append("load")
                    def __del__(self):
                        if self.live:
                            self.live = False
                            self.events.append("release")
                env["FACE_DETECT"] = FakeModel
                send_fixed(camera, 4, 1)
                send_fixed(camera, 4, 1)
                self.assertEqual(events[:3], ["load", "release", "load"])

    def test_release_failure_does_not_load_next_model(self):
        for board in BOARDS:
            with self.subTest(board=board):
                camera, env = load_camera(board)
                loaded = []
                def fail():
                    raise RuntimeError("deinit failed")
                camera.face_detect = SimpleNamespace(__del__=fail)
                camera.k210.mode = 4
                env["YOLO_DETECT"] = lambda **kwargs: loaded.append(True)
                send_fixed(camera, 3, 1)
                self.assertEqual(loaded, [])
                self.assertEqual(camera.k210.mode, 1)
                self.assertEqual(camera.responses[-1][2:7], bytes((1, 1, 0xFD, 3, 0)))

    def test_release_failure_blocks_retries_until_reset(self):
        for board in BOARDS:
            with self.subTest(board=board):
                camera, env = load_camera(board)
                loaded = []
                def fail():
                    raise RuntimeError("deinit failed")
                camera.face_detect = SimpleNamespace(__del__=fail)
                camera.k210.mode = 4
                env["YOLO_DETECT"] = lambda **kwargs: loaded.append(True) or SimpleNamespace()
                send_fixed(camera, 3, 1)
                send_fixed(camera, 1, 0xFE, 3)
                self.assertFalse(any(frame[2:5] == bytes((1, 1, 0xFE)) for frame in camera.responses))
                send_fixed(camera, 3, 1)
                send_fixed(camera, 1, 0xFC, 3, 25)
                self.assertEqual(loaded, [])
                self.assertEqual(camera.responses[-1][2:8], bytes((1, 1, 0xFD, 3, 0, 25)))

    def test_constructor_release_failure_blocks_subsequent_modes(self):
        for board in BOARDS:
            with self.subTest(board=board):
                camera, env = load_camera(board)
                def fail(**kwargs):
                    raise RuntimeError("KPU_RELEASE_FAILED")
                loaded = []
                env["FACE_DETECT"] = fail
                env["YOLO_DETECT"] = lambda **kwargs: loaded.append(True) or SimpleNamespace()
                send_fixed(camera, 4, 1)
                send_fixed(camera, 3, 1)
                send_fixed(camera, 1, 0xFC, 3, 26)
                self.assertEqual(loaded, [])
                self.assertEqual(camera.responses[-1][2:8], bytes((1, 1, 0xFD, 3, 0, 26)))

    def test_canvas_init_ack(self):
        for board in BOARDS:
            with self.subTest(board=board):
                camera, env = load_camera(board)
                camera.init_canvas = lambda: None
                send_fixed(camera, 1, 0xFA, 1)
                self.assertEqual(camera.responses[-1][2:7], bytes((1, 1, 0xFD, 1, 1)))

    def test_init_status_query_echoes_nonce_and_matching_mode(self):
        for board in BOARDS:
            with self.subTest(board=board):
                camera, env = load_camera(board)
                env["FACE_DETECT"] = lambda **kwargs: SimpleNamespace()
                send_fixed(camera, 4, 1)
                send_fixed(camera, 1, 0xFC, 4, 42)
                self.assertEqual(camera.responses[-1][2:8], bytes((1, 1, 0xFD, 4, 1, 42)))
                send_fixed(camera, 1, 0xFC, 3, 43)
                self.assertEqual(camera.responses[-1][2:8], bytes((1, 1, 0xFD, 3, 0, 43)))

    def test_init_status_query_reports_init_failure(self):
        for board in BOARDS:
            with self.subTest(board=board):
                camera, env = load_camera(board)
                def fail(**kwargs):
                    raise RuntimeError("bad model")
                env["FACE_DETECT"] = fail
                send_fixed(camera, 4, 1)
                send_fixed(camera, 1, 0xFC, 4, 73)
                self.assertEqual(camera.responses[-1][2:8], bytes((1, 1, 0xFD, 4, 0, 73)))

    def test_switch_invalidates_previous_success(self):
        for board in BOARDS:
            with self.subTest(board=board):
                camera, env = load_camera(board)
                env["FACE_DETECT"] = lambda **kwargs: SimpleNamespace()
                send_fixed(camera, 4, 1)
                send_fixed(camera, 1, 0xFE, 4)
                send_fixed(camera, 1, 0xFC, 4, 12)
                self.assertEqual(camera.responses[-1][2:8], bytes((1, 1, 0xFD, 4, 0, 12)))

    def test_corrupted_string_frame_is_skipped_and_next_frame_processed(self):
        for board in BOARDS:
            with self.subTest(board=board):
                camera, env = load_camera(board)
                loaded = []
                env["KPU_KMODEL"] = lambda **kwargs: loaded.append(kwargs["model"]) or SimpleNamespace()
                payload = b"bad|128|128"
                header = bytes((0xAA, 0xBB, 2, 11, 2, 0, 0, 0))
                frame = header + bytes((len(payload),)) + payload + bytes(((sum(header) + sum(payload) + 1) & 0xFF,))
                camera._uart_rx.extend(frame)
                send_string(camera, 11, 2, "good|128|128")
                self.assertEqual(loaded, ["good"])

    def test_custom_model_string_init_ack(self):
        for board in BOARDS:
            with self.subTest(board=board):
                camera, env = load_camera(board)
                env["KPU_KMODEL"] = lambda **kwargs: SimpleNamespace()
                send_string(camera, 11, 2, "/sd/model.kmodel|128|128")
                self.assertEqual(camera.responses[-1][2:7], bytes((1, 1, 0xFD, 11, 1)))
                self.assertEqual(camera.k210.mode, 11)

    def test_same_mode_fe_releases_and_acknowledges(self):
        for board in BOARDS:
            with self.subTest(board=board):
                camera, env = load_camera(board)
                released = []
                camera.face_detect = SimpleNamespace(__del__=lambda: released.append(True))
                camera.k210.mode = 4
                send_fixed(camera, 1, 0xFE, 4)
                self.assertEqual(released, [True])
                self.assertEqual(camera.k210.mode, 1)
                self.assertEqual(camera.responses[-1][2:5], bytes((1, 1, 0xFE)))

    def test_partial_face_model_load_is_released(self):
        for board in BOARDS:
            with self.subTest(board=board):
                path = PROJECT / "builtin_py" / board / "face_recognization.py"
                tree = ast.parse(path.read_text(encoding="utf-8"))
                cls = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == "Face_recognization")
                env = {}
                exec(compile(ast.Module(body=[cls], type_ignores=[]), str(path), "exec"), env)
                released = []
                def load(address):
                    if address == 0x380000:
                        raise RuntimeError("second model failed")
                    return address
                kpu = SimpleNamespace(load=load, deinit=released.append)
                with self.assertRaises(RuntimeError):
                    env["Face_recognization"](kpu=kpu)
                gc.collect()
                self.assertEqual(released, [0x300000])

    def test_mnist_model_failure_does_not_return_initialized_object(self):
        for board in BOARDS:
            with self.subTest(board=board):
                path = PROJECT / "builtin_py" / board / "mnist.py"
                tree = ast.parse(path.read_text(encoding="utf-8"))
                cls = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == "MNIST")
                lcd = SimpleNamespace(init=lambda **kw: None, rotation=lambda *a: None,
                                      clear=lambda *a: None, draw_string=lambda *a: None,
                                      WHITE=1, BLUE=2)
                env = {"lcd": lcd, "time": SimpleNamespace(sleep=lambda _: None)}
                exec(compile(ast.Module(body=[cls], type_ignores=[]), str(path), "exec"), env)
                def fail(_):
                    raise RuntimeError("missing model")
                with self.assertRaises(RuntimeError):
                    env["MNIST"](sensor=None, lcd=lcd, kpu=SimpleNamespace(load=fail))

    def test_sensor_failure_releases_loaded_model_once(self):
        for board in BOARDS:
            with self.subTest(board=board):
                path = PROJECT / "builtin_py" / board / "face_detect.py"
                tree = ast.parse(path.read_text(encoding="utf-8"))
                cls = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == "FACE_DETECT")
                env = {"time": SimpleNamespace(clock=lambda: object()), "gc": gc}
                exec(compile(ast.Module(body=[cls], type_ignores=[]), str(path), "exec"), env)
                released = []
                kpu = SimpleNamespace(load=lambda _: "task", init_yolo2=lambda *args: None,
                                      memtest=lambda: None, deinit=released.append)
                def reset(**kwargs):
                    raise RuntimeError("sensor unavailable")
                sensor = SimpleNamespace(reset=reset)
                with self.assertRaises(RuntimeError):
                    env["FACE_DETECT"](sensor=sensor, kpu=kpu,
                                       lcd=SimpleNamespace(rotation=lambda _: None))
                gc.collect()
                self.assertEqual(released, ["task"])

    def test_constructor_reports_kpu_release_failure(self):
        for board in BOARDS:
            with self.subTest(board=board):
                path = PROJECT / "builtin_py" / board / "face_detect.py"
                tree = ast.parse(path.read_text(encoding="utf-8"))
                cls = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == "FACE_DETECT")
                env = {"time": SimpleNamespace(clock=lambda: object()), "gc": gc}
                exec(compile(ast.Module(body=[cls], type_ignores=[]), str(path), "exec"), env)
                def fail(*args, **kwargs):
                    raise RuntimeError("sensor or deinit failed")
                kpu = SimpleNamespace(load=lambda _: "task", init_yolo2=lambda *args: None,
                                      memtest=lambda: None, deinit=fail)
                with self.assertRaisesRegex(RuntimeError, "KPU_RELEASE_FAILED"):
                    env["FACE_DETECT"](sensor=SimpleNamespace(reset=fail), kpu=kpu,
                                       lcd=SimpleNamespace(rotation=lambda _: None))


if __name__ == "__main__":
    unittest.main()
