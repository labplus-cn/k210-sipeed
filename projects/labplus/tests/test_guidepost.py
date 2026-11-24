"""Regression tests for failed Guidepost inference."""

import ast
import gc
from pathlib import Path
from types import SimpleNamespace
import unittest


PROJECT = Path(__file__).resolve().parents[1]


class GuidepostTests(unittest.TestCase):
    def test_inference_exception_returns_empty_result(self):
        for board in ("labplus_owl_2024", "labplus_owl_gansu"):
            with self.subTest(board=board):
                path = PROJECT / "builtin_py" / board / "guidepost.py"
                tree = ast.parse(path.read_text(encoding="utf-8"))
                cls = next(node for node in tree.body
                           if isinstance(node, ast.ClassDef) and node.name == "Guidepost")
                namespace = {"gc": gc}
                exec(compile(ast.Module(body=[cls], type_ignores=[]), str(path), "exec"), namespace)
                instance = object.__new__(namespace["Guidepost"])
                instance.clock = SimpleNamespace(tick=lambda: None)
                instance.sensor = SimpleNamespace(snapshot=lambda: SimpleNamespace(width=lambda: 192))
                def fail(*args):
                    raise RuntimeError("inference failed")
                instance.kpu = SimpleNamespace(forward=fail, memtest=lambda: None,
                                               deinit=lambda task: None)
                instance.task = object()
                self.assertEqual(instance.recognize(), (None, None))


if __name__ == "__main__":
    unittest.main()
