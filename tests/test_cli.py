"""cli 模块单元测试：退出码、中文报错与生成结果。"""

from __future__ import annotations

import contextlib
import io
import tempfile
import unittest
from pathlib import Path
from typing import List, Tuple

from sundial.cli import build_parser, main


class CliTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.target = self.root / "日晷制作卡.html"

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def run_cli(self, argv: List[str]) -> Tuple[int, str, str]:
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = main(argv)
        return code, out.getvalue(), err.getvalue()

    def base_args(self) -> List[str]:
        return [
            "--latitude", "31.2",
            "--start-hour", "6",
            "--end-hour", "18",
            "--title", "日晷制作卡",
            "-o", str(self.target),
        ]

    def test_default_generation(self) -> None:
        code, out, err = self.run_cli(self.base_args())
        self.assertEqual(code, 0)
        self.assertEqual(err, "")
        self.assertIn("已生成", out)
        self.assertIn("3 页 A4", out)
        self.assertTrue(self.target.exists())

    def test_content(self) -> None:
        self.assertEqual(self.run_cli(self.base_args())[0], 0)
        page = self.target.read_text(encoding="utf-8")
        self.assertEqual(page.count("data-page="), 3)
        self.assertIn("北纬 31.2°", page)
        self.assertIn("地方真太阳时", page)

    def test_custom_range(self) -> None:
        argv = [
            "--latitude", "-33.9",
            "--start-hour", "7",
            "--end-hour", "17",
            "--title", "南半球日晷",
            "-o", str(self.target),
        ]
        code, _, _ = self.run_cli(argv)
        self.assertEqual(code, 0)
        page = self.target.read_text(encoding="utf-8")
        self.assertEqual(page.count('class="hour-line"'), 11)
        self.assertIn("南纬 33.9°", page)
        self.assertIn("07:00–17:00", page)
        self.assertIn("南半球日晷", page)

    def test_invalid_latitude_high(self) -> None:
        argv = self.base_args()
        argv[1] = "67"
        code, _, err = self.run_cli(argv)
        self.assertEqual(code, 2)
        self.assertIn("错误", err)
        self.assertIn("66", err)
        self.assertFalse(self.target.exists())

    def test_invalid_latitude_low(self) -> None:
        argv = self.base_args()
        argv[1] = "-67"
        self.assertEqual(self.run_cli(argv)[0], 2)

    def test_nan_latitude(self) -> None:
        argv = self.base_args()
        argv[1] = "nan"
        code, _, err = self.run_cli(argv)
        self.assertEqual(code, 2)
        self.assertIn("有限", err)

    def test_non_numeric_latitude(self) -> None:
        argv = self.base_args()
        argv[1] = "北纬"
        with contextlib.redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit) as ctx:
                main(argv)
        self.assertEqual(ctx.exception.code, 2)

    def test_start_hour_too_early(self) -> None:
        argv = self.base_args()
        argv[3] = "4"
        code, _, err = self.run_cli(argv)
        self.assertEqual(code, 2)
        self.assertIn("5", err)

    def test_end_hour_too_late(self) -> None:
        argv = self.base_args()
        argv[5] = "20"
        self.assertEqual(self.run_cli(argv)[0], 2)

    def test_equal_hours(self) -> None:
        argv = self.base_args()
        argv[5] = "6"
        code, _, err = self.run_cli(argv)
        self.assertEqual(code, 2)
        self.assertIn("早于", err)

    def test_reversed_hours(self) -> None:
        argv = self.base_args()
        argv[3] = "18"
        argv[5] = "6"
        self.assertEqual(self.run_cli(argv)[0], 2)

    def test_non_integer_hour(self) -> None:
        argv = self.base_args()
        argv[3] = "6.5"
        with contextlib.redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit) as ctx:
                main(argv)
        self.assertEqual(ctx.exception.code, 2)

    def test_empty_title(self) -> None:
        argv = self.base_args()
        argv[7] = ""
        code, _, err = self.run_cli(argv)
        self.assertEqual(code, 2)
        self.assertIn("标题", err)

    def test_long_title(self) -> None:
        argv = self.base_args()
        argv[7] = "字" * 41
        self.assertEqual(self.run_cli(argv)[0], 2)

    def test_title_escaped(self) -> None:
        argv = self.base_args()
        argv[7] = "<日晷>"
        self.assertEqual(self.run_cli(argv)[0], 0)
        page = self.target.read_text(encoding="utf-8")
        self.assertIn("&lt;日晷&gt;", page)
        self.assertNotIn("<日晷>", page)

    def test_missing_output_parent(self) -> None:
        argv = self.base_args()
        argv[-1] = str(self.root / "missing" / "out.html")
        code, _, err = self.run_cli(argv)
        self.assertEqual(code, 1)
        self.assertIn("写入文件失败", err)

    def test_output_is_directory(self) -> None:
        argv = self.base_args()
        argv[-1] = str(self.root)
        code, _, err = self.run_cli(argv)
        self.assertEqual(code, 1)
        self.assertIn("写入文件失败", err)

    def test_help(self) -> None:
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            with self.assertRaises(SystemExit) as ctx:
                main(["--help"])
        self.assertEqual(ctx.exception.code, 0)
        self.assertIn("usage", out.getvalue())
        self.assertIn("--latitude", out.getvalue())

    def test_version(self) -> None:
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            with self.assertRaises(SystemExit) as ctx:
                main(["--version"])
        self.assertEqual(ctx.exception.code, 0)
        self.assertIn("sundial 0.1.0", out.getvalue())

    def test_missing_value(self) -> None:
        with contextlib.redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit) as ctx:
                main(["--latitude"])
        self.assertEqual(ctx.exception.code, 2)

    def test_unknown_option(self) -> None:
        with contextlib.redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit) as ctx:
                main(["--unknown"])
        self.assertEqual(ctx.exception.code, 2)

    def test_parser_defaults(self) -> None:
        args = build_parser().parse_args([])
        self.assertEqual(args.latitude, 31.2)
        self.assertEqual(args.start_hour, 6)
        self.assertEqual(args.end_hour, 18)
        self.assertEqual(args.title, "日晷制作卡")
        self.assertEqual(args.output, "日晷制作卡.html")

    def test_negative_latitude_boundary(self) -> None:
        argv = self.base_args()
        argv[1] = "-66"
        self.assertEqual(self.run_cli(argv)[0], 0)

    def test_positive_latitude_boundary(self) -> None:
        argv = self.base_args()
        argv[1] = "66"
        self.assertEqual(self.run_cli(argv)[0], 0)

    def test_equator_generation(self) -> None:
        argv = self.base_args()
        argv[1] = "0"
        self.assertEqual(self.run_cli(argv)[0], 0)
        page = self.target.read_text(encoding="utf-8")
        self.assertIn("赤道 0°", page)
        self.assertIn("无法竖立", page)


if __name__ == "__main__":
    unittest.main()
