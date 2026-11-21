"""命令行入口：生成可打印的水平日晷制作卡。"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import NoReturn, Optional, Sequence

from .model import (
    DEFAULT_END_HOUR,
    DEFAULT_LATITUDE,
    DEFAULT_START_HOUR,
    DEFAULT_TITLE,
    Sundial,
    SundialError,
)
from .render import render_sundial


def _latitude_arg(text: str) -> float:
    """argparse 纬度转换，错误信息使用中文。"""
    try:
        return float(text)
    except ValueError:
        raise argparse.ArgumentTypeError("纬度必须是数字") from None


def _hour_arg(text: str) -> int:
    """argparse 整点转换，错误信息使用中文。"""
    try:
        return int(text)
    except ValueError:
        raise argparse.ArgumentTypeError("时刻必须是整数") from None


class _ChineseArgumentParser(argparse.ArgumentParser):
    """把 argparse 的默认英文错误前缀替换为中文。"""

    def error(self: "_ChineseArgumentParser", message: str) -> NoReturn:
        self.print_usage(sys.stderr)
        print("错误: %s" % message, file=sys.stderr)
        raise SystemExit(2)


def build_parser() -> argparse.ArgumentParser:
    """构造命令行解析器。"""
    parser = _ChineseArgumentParser(
        prog="sundial",
        description="水平日晷制作卡：按纬度计算时刻线，生成 A4 可打印 HTML",
    )
    parser.add_argument(
        "--version", action="version", version="sundial 0.1.0"
    )
    parser.add_argument(
        "--latitude",
        type=_latitude_arg,
        default=DEFAULT_LATITUDE,
        help="纬度，-66~66，北正南负（默认 31.2）",
    )
    parser.add_argument(
        "--start-hour",
        type=_hour_arg,
        default=DEFAULT_START_HOUR,
        help="起始整点，5~19（默认 6）",
    )
    parser.add_argument(
        "--end-hour",
        type=_hour_arg,
        default=DEFAULT_END_HOUR,
        help="结束整点，5~19（默认 18）",
    )
    parser.add_argument(
        "--title", default=DEFAULT_TITLE, help="制作卡标题，1~40 字"
    )
    parser.add_argument(
        "-o",
        "--output",
        default="日晷制作卡.html",
        help="输出 HTML 路径（默认 日晷制作卡.html）",
    )
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    """执行命令行，返回退出码：成功 0，参数错误 2，IO 失败 1。"""
    args = build_parser().parse_args(argv)

    try:
        sundial = Sundial(
            latitude=args.latitude,
            start_hour=args.start_hour,
            end_hour=args.end_hour,
            title=args.title,
        )
        page = render_sundial(sundial)
    except SundialError as exc:
        print("错误: %s" % exc, file=sys.stderr)
        return 2

    target = Path(args.output)
    try:
        target.write_text(page, encoding="utf-8")
    except OSError as exc:
        print("错误: 写入文件失败: %s" % exc, file=sys.stderr)
        return 1

    print(
        "已生成 %s：%s，时刻线 %02d:00–%02d:00，共 3 页 A4"
        % (
            args.output,
            sundial.location_text,
            sundial.start_hour,
            sundial.end_hour,
        )
    )
    print("用浏览器打开后按 Ctrl/Cmd + P，纸张选 A4 纵向，缩放 100%")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
