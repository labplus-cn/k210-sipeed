"""Exercise the actual host and camera UART protocols together without hardware."""

import ast
from contextlib import redirect_stdout
import gc
from io import StringIO
from pathlib import Path
import threading
from types import SimpleNamespace
import unittest

from test_mode_initialization import BOARDS, load_camera


PROJECT = Path(__file__).resolve().parents[3]
COMMON = PROJECT.parent / "labplus_mpython_esp32s3/port/file_system/common"
PUBLIC = COMMON / "lib/k210_ai/public.py"
DRIVER = COMMON / "smartcamera_new.py"
AI = COMMON / "lib/k210_ai/ai.py"


class Endpoint:
    def __init__(self):
        self.rx = bytearray()
        self.peer = None
        self.on_write = None
        self.frames = []

    def write(self, data):
        frame = bytes(data)
        self.frames.append(frame)
        self.peer.rx.extend(frame)
        if self.on_write:
            self.on_write()

    def any(self):
        return len(self.rx)

    def read(self, count=None):
        if count is None:
            count = len(self.rx)
        data = bytes(self.rx[:count])
        del self.rx[:count]
        return data


def host_driver():
    clock = SimpleNamespace(sleep=lambda _: None, sleep_ms=lambda _: None)
    env = {"gc": gc, "time": clock, "Pin": SimpleNamespace(P15=15, P16=16)}
    public_tree = ast.parse(PUBLIC.read_text(encoding="utf-8"))
    nodes = [n for n in public_tree.body if isinstance(n, ast.Assign) and
             all(isinstance(t, ast.Name) for t in n.targets) and
             isinstance(n.value, (ast.Constant, ast.Dict, ast.List))]
    nodes += [n for n in public_tree.body if isinstance(n, ast.FunctionDef) and
              n.name in ("CheckCode", "uart_handle", "AI_Uart_CMD", "AI_Uart_CMD_String")]
    exec(compile(ast.Module(body=nodes, type_ignores=[]), str(PUBLIC), "exec"), env)
    for path, name in ((AI, "FACE_DETECT"), (AI, "KPU_MODEL"), (DRIVER, "SmartCamera")):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        cls = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == name)
        exec(compile(ast.Module(body=[cls], type_ignores=[]), str(path), "exec"), env)
    host = object.__new__(env["SmartCamera"])
    host.mode = env["DEFAULT_MODE"]
    host.connected = True
    host.lock = False
    host.last_error = None
    host._uart_rx = [bytearray()]
    host._uart_guard = threading.Lock()
    host._control_guard = threading.Lock()
    host._model_parameters = {}
    host._face_parameters = (1, 80)
    host.slc_parameter = [3, 15, 11, 1]
    return host


def pair(board, fail=False):
    host = host_driver()
    device, env = load_camera(board)
    env["lcd"] = device.lcd
    device.lcd.GREEN = 3
    host_uart, device_uart = Endpoint(), Endpoint()
    host_uart.peer, device_uart.peer = device_uart, host_uart
    host.uart, device.uart = host_uart, device_uart
    del device._uart_read_pending
    host_uart.on_write = device.uart_handle
    events = []

    class Face:
        def __init__(self, **kwargs):
            if fail:
                raise RuntimeError("model failed")
            self.live = True
            events.append("load")

        def __del__(self):
            if getattr(self, "live", False):
                self.live = False
                events.append("release")

    env["FACE_DETECT"] = Face
    return host, device, host_uart, device_uart, events


class EndToEndProtocolTests(unittest.TestCase):
    def assert_frames_valid(self, frames, header, size):
        for frame in frames:
            self.assertEqual(frame[:2], header)
            self.assertEqual(len(frame), size)
            self.assertEqual(sum(frame[:-1]) & 255, frame[-1])

    def assert_status_query(self, requests, replies, mode, status):
        queries = [frame for frame in requests if frame[2:5] == bytes((1, 1, 0xFC))]
        self.assertTrue(queries, "host must query status with a nonce")
        query = queries[-1]
        self.assertEqual(query[5], mode)
        self.assertTrue(any(frame[2:8] == bytes((1, 1, 0xFD, mode, status, query[6]))
                            for frame in replies), "status reply must echo the query nonce")

    def test_switch_success_uses_real_frames_and_ack(self):
        for board in BOARDS:
            with self.subTest(board=board):
                host, device, tx, rx, events = pair(board)
                self.assertTrue(host.switcher_mode(4, 1))
                self.assertEqual((host.mode, device.k210.mode), (4, 4))
                self.assertTrue(host.connected)
                self.assertEqual(events, ["load"])
                self.assert_frames_valid(tx.frames, b"\xaa\xbb", 14)
                self.assert_frames_valid(rx.frames, b"\xbb\xaa", 12)
                self.assert_status_query(tx.frames, rx.frames, 4, 1)

    def test_device_model_exception_reaches_host_and_clears_state(self):
        for board in BOARDS:
            with self.subTest(board=board):
                host, device, tx, rx, events = pair(board, fail=True)
                with self.assertRaisesRegex(RuntimeError, "initialization failed"):
                    host.switcher_mode(4, 1)
                self.assertFalse(host.connected)
                self.assertEqual((host.mode, device.k210.mode), (1, 1))
                self.assertIsNone(device.face_detect)
                self.assert_status_query(tx.frames, rx.frames, 4, 0)
                self.assert_frames_valid(tx.frames, b"\xaa\xbb", 14)
                self.assert_frames_valid(rx.frames, b"\xbb\xaa", 12)

    def test_same_mode_retry_releases_and_reloads(self):
        for board in BOARDS:
            with self.subTest(board=board):
                host, device, tx, rx, events = pair(board)
                self.assertTrue(host.switcher_mode(4, 1))
                old = host.face_detect
                self.assertTrue(host.switcher_mode(4, 1))
                self.assertTrue(old.lock)
                self.assertEqual(events, ["load", "release", "load"])
                self.assertEqual((host.mode, device.k210.mode), (4, 4))
                queries = [f for f in tx.frames if f[2:6] == bytes((1, 1, 0xFC, 4))]
                self.assertEqual(len(queries), 2)
                self.assertNotEqual(queries[0][6], queries[1][6])
                for query in queries:
                    self.assertTrue(any(f[2:8] == bytes((1, 1, 0xFD, 4, 1, query[6])) for f in rx.frames))
                self.assert_frames_valid(tx.frames, b"\xaa\xbb", 14)
                self.assert_frames_valid(rx.frames, b"\xbb\xaa", 12)

    def test_custom_model_uses_real_string_frame_and_ack(self):
        for board in BOARDS:
            with self.subTest(board=board):
                host, device, tx, rx, _ = pair(board)
                env = device.process_cmd.__func__.__globals__
                kwargs_seen = []
                def model(**kwargs):
                    kwargs_seen.append(kwargs)
                    return SimpleNamespace()
                env["KPU_KMODEL"] = model
                self.assertTrue(host.kmodel_init(1, "/sd/test.kmodel", 128, 128))
                self.assertEqual((host.mode, device.k210.mode), (11, 11))
                self.assertEqual(kwargs_seen[0]["model"], "/sd/test.kmodel")
                string_frame = next(f for f in tx.frames if f[2] == 2)
                self.assertEqual(string_frame[:5], bytes((0xaa, 0xbb, 2, 11, 2)))
                self.assertEqual(string_frame[8], len(string_frame) - 10)
                self.assertEqual(string_frame[9:-1], b"/sd/test.kmodel|128|128")
                self.assertEqual((sum(string_frame[:8]) + sum(string_frame[9:-1])) & 255,
                                 string_frame[-1])
                self.assert_status_query(tx.frames, rx.frames, 11, 1)
                self.assert_frames_valid(rx.frames, b"\xbb\xaa", 12)

    def test_device_rejects_invalid_fixed_frame_checksum(self):
        for board in BOARDS:
            with self.subTest(board=board):
                host, device, tx, rx, events = pair(board)
                corrupted = bytearray((0xaa, 0xbb, 1, 4, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0))
                self.assertNotEqual(sum(corrupted[:-1]) & 255, corrupted[-1])
                host.uart.write(corrupted)
                self.assertEqual(events, [])
                self.assertEqual(device.k210.mode, 1)
                self.assertEqual(rx.frames, [])

    def test_stale_ack_nonce_cannot_confirm_new_switch(self):
        for board in BOARDS:
            with self.subTest(board=board):
                host, device, tx, _, _ = pair(board)
                def forward_except_query():
                    frame = tx.frames[-1]
                    if frame[2:5] != bytes((1, 1, 0xFC)):
                        device.uart_handle()
                        return
                    device.uart.rx.clear()
                    stale = bytearray((0xbb, 0xaa, 1, 1, 0xFD, frame[5], 1,
                                       (frame[6] + 1) & 255, 0, 0, 0))
                    stale.append(sum(stale) & 255)
                    host.uart.rx.extend(stale)
                tx.on_write = forward_except_query
                with self.assertRaisesRegex(RuntimeError, "timed out"):
                    host.switcher_mode(4, 1)
                self.assertFalse(host.connected)

    def test_lost_same_mode_init_does_not_reuse_previous_success(self):
        for board in BOARDS:
            with self.subTest(board=board):
                host, device, tx, _, events = pair(board)
                self.assertTrue(host.switcher_mode(4, 1))
                def drop_init():
                    if tx.frames[-1][2:5] == bytes((1, 4, 1)):
                        device.uart.rx.clear()
                    else:
                        device.uart_handle()
                tx.on_write = drop_init
                with self.assertRaisesRegex(RuntimeError, "initialization failed|timed out"):
                    host.switcher_mode(4, 1)
                self.assertFalse(host.connected)
                self.assertEqual(device.k210.mode, 1)
                self.assertEqual(events, ["load", "release"])

    def test_failed_release_cannot_be_bypassed_by_fe_retry(self):
        for board in BOARDS:
            with self.subTest(board=board):
                host, device, _, _, events = pair(board)
                host.mode = 4
                host.face_detect = SimpleNamespace(lock=False)
                device.k210.mode = 4
                def fail_release():
                    raise RuntimeError("deinit failed")
                device.face_detect = SimpleNamespace(__del__=fail_release)
                # The reset path has its own hardware handshake; here we check
                # that FE retries cannot hide the failure before recovery.
                host._wait_for_ai_init_locked = lambda: False
                with redirect_stdout(StringIO()):
                    with self.assertRaisesRegex(RuntimeError, "recovery failed"):
                        host.switcher_mode(4, 1)
                self.assertEqual(events, [])
                self.assertFalse(host.connected)


if __name__ == "__main__":
    unittest.main()
