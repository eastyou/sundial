"""水平日晷的几何模型：时刻线角度、端点与参数校验。

时刻线方位角满足::

    tan(theta) = sin(phi) * tan(15° * (t - 12))

其中 ``phi`` 是纬度，``t`` 是地方真太阳时（小时），``theta`` 从正午线起算。
正午线在北半球指向正北，在南半球指向正南；南半球的角度自然左右镜像。
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Tuple, Union

MIN_LATITUDE = -66.0
MAX_LATITUDE = 66.0
MIN_HOUR = 5
MAX_HOUR = 19
MIN_TITLE_LENGTH = 1
MAX_TITLE_LENGTH = 40
DEFAULT_LATITUDE = 31.2
DEFAULT_START_HOUR = 6
DEFAULT_END_HOUR = 18
DEFAULT_TITLE = "日晷制作卡"
DEGREES_PER_HOUR = 15.0
GNOMON_BASE_MM = 60.0

Number = Union[int, float]


class SundialError(ValueError):
    """日晷参数或几何数据不合法。"""


def _is_number(value: object) -> bool:
    """判断是否为实数，并排除 bool（bool 是 int 的子类）。"""
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def validate_latitude(latitude: Number) -> float:
    """校验纬度，返回浮点值。"""
    if not _is_number(latitude):
        raise SundialError("纬度必须是数字")
    value = float(latitude)
    if not math.isfinite(value):
        raise SundialError("纬度必须是有限数字")
    if value < MIN_LATITUDE or value > MAX_LATITUDE:
        raise SundialError(
            "纬度必须在 %.0f° 到 %.0f° 之间，当前为 %.4g°"
            % (MIN_LATITUDE, MAX_LATITUDE, value)
        )
    return value


def validate_hour(hour: Number) -> float:
    """校验单个时刻，返回浮点值。"""
    if not _is_number(hour):
        raise SundialError("时刻必须是数字")
    value = float(hour)
    if not math.isfinite(value):
        raise SundialError("时刻必须是有限数字")
    if value < MIN_HOUR or value > MAX_HOUR:
        raise SundialError(
            "时刻必须在 %d 到 %d 点之间，当前为 %.4g 点"
            % (MIN_HOUR, MAX_HOUR, value)
        )
    return value


def validate_hour_range(start_hour: int, end_hour: int) -> Tuple[int, int]:
    """校验起止整点，返回整数时刻。"""
    for value, name in ((start_hour, "起始时刻"), (end_hour, "结束时刻")):
        if isinstance(value, bool) or not isinstance(value, int):
            raise SundialError("%s必须是整数" % name)
        if value < MIN_HOUR or value > MAX_HOUR:
            raise SundialError(
                "%s必须在 %d 到 %d 点之间，当前为 %d 点"
                % (name, MIN_HOUR, MAX_HOUR, value)
            )
    if start_hour >= end_hour:
        raise SundialError("起始时刻必须早于结束时刻")
    return start_hour, end_hour


def validate_title(title: str) -> str:
    """校验标题，返回去掉首尾空白后的文本。"""
    if not isinstance(title, str):
        raise SundialError("标题必须是文本")
    cleaned = title.strip()
    if not cleaned:
        raise SundialError("标题不能为空")
    if len(cleaned) > MAX_TITLE_LENGTH:
        raise SundialError("标题最多 %d 个字符" % MAX_TITLE_LENGTH)
    if any(char in cleaned for char in "\r\n\t"):
        raise SundialError("标题不能包含换行或制表符")
    return cleaned


def validate_length(value: Number, name: str = "长度") -> float:
    """校验长度为正的有限数。"""
    if not _is_number(value):
        raise SundialError("%s必须是数字" % name)
    result = float(value)
    if not math.isfinite(result):
        raise SundialError("%s必须是有限数字" % name)
    if result <= 0.0:
        raise SundialError("%s必须大于 0" % name)
    return result


def validate_coordinate(value: Number, name: str) -> float:
    """校验坐标分量为有限数。"""
    if not _is_number(value):
        raise SundialError("%s必须是数字" % name)
    result = float(value)
    if not math.isfinite(result):
        raise SundialError("%s必须是有限数字" % name)
    return result


def hour_angle(latitude: Number, hour: Number) -> float:
    """计算时刻线相对正午线的有符号方位角，单位为度。

    参数:
        latitude: 纬度，范围 -66°~66°，北正南负。
        hour: 地方真太阳时，范围 5~19 点，可带小数。

    返回:
        角度，范围 [-90°, 90°]。正午为 0°；6:00 与 18:00 恰好为 ±90°。
        北半球上午为负、下午为正；南半球符号相反（左右镜像）。
    """
    latitude_value = validate_latitude(latitude)
    hour_value = validate_hour(hour)

    if hour_value == 12.0:
        return 0.0

    delta = DEGREES_PER_HOUR * (hour_value - 12.0)
    if abs(delta) == 90.0:
        base = -90.0 if delta < 0.0 else 90.0
        return -base if latitude_value < 0.0 else base

    product = math.sin(math.radians(latitude_value)) * math.tan(
        math.radians(delta)
    )
    angle = math.degrees(math.atan(product))
    if not math.isfinite(angle):
        raise SundialError("时刻线角度计算失败：结果不是有限数")
    if abs(angle) > 90.0 + 1e-9:
        raise SundialError("时刻线角度超出 ±90°")
    return angle


def hour_line_endpoint(
    latitude: Number,
    hour: Number,
    radius_mm: Number,
    center_x_mm: Number = 0.0,
    center_y_mm: Number = 0.0,
) -> Tuple[float, float]:
    """计算时刻线端点的毫米坐标，坐标系 y 轴向下（SVG 约定）。

    北半球正午线朝上（y 减小），南半球正午线朝下（y 增大）；
    因此南北半球的 6:00 线都落在盘面左侧（西侧）。
    """
    latitude_value = validate_latitude(latitude)
    hour_value = validate_hour(hour)
    radius = validate_length(radius_mm, "半径")
    center_x = validate_coordinate(center_x_mm, "中心横坐标")
    center_y = validate_coordinate(center_y_mm, "中心纵坐标")

    angle = math.radians(hour_angle(latitude_value, hour_value))
    if latitude_value >= 0.0:
        x = center_x + radius * math.sin(angle)
        y = center_y - radius * math.cos(angle)
    else:
        x = center_x - radius * math.sin(angle)
        y = center_y + radius * math.cos(angle)
    return (x, y)


@dataclass(frozen=True)
class HourLine:
    """一条时刻线：整点或半点，以及相对正午线的角度。"""

    hour: float
    angle_deg: float
    half_hour: bool = False

    def __post_init__(self: "HourLine") -> None:
        hour_value = validate_hour(self.hour)
        if isinstance(self.angle_deg, bool) or not isinstance(
            self.angle_deg, (int, float)
        ):
            raise SundialError("时刻线角度必须是数字")
        angle = float(self.angle_deg)
        if not math.isfinite(angle):
            raise SundialError("时刻线角度必须是有限数字")
        if abs(angle) > 90.0 + 1e-9:
            raise SundialError("时刻线角度超出 ±90°")
        if not isinstance(self.half_hour, bool):
            raise SundialError("半点标记必须是布尔值")
        object.__setattr__(self, "hour", hour_value)
        object.__setattr__(self, "angle_deg", angle)

    @property
    def label(self: "HourLine") -> str:
        """整点的钟点文本，例如 ``6:00``。"""
        whole = int(math.floor(self.hour))
        minutes = int(round((self.hour - whole) * 60.0))
        if minutes == 60:
            whole += 1
            minutes = 0
        return "%02d:%02d" % (whole, minutes)


def hour_lines(
    latitude: Number,
    start_hour: int,
    end_hour: int,
    include_half_hours: bool = False,
) -> Tuple[HourLine, ...]:
    """生成起止时刻之间的时刻线，按时间升序返回。"""
    latitude_value = validate_latitude(latitude)
    start, end = validate_hour_range(start_hour, end_hour)
    if not isinstance(include_half_hours, bool):
        raise SundialError("半点标记必须是布尔值")

    lines = [
        HourLine(float(hour), hour_angle(latitude_value, float(hour)))
        for hour in range(start, end + 1)
    ]
    if include_half_hours:
        lines.extend(
            HourLine(
                hour + 0.5,
                hour_angle(latitude_value, hour + 0.5),
                True,
            )
            for hour in range(start, end)
        )
        lines.sort(key=lambda item: item.hour)
    return tuple(lines)


def angle_table(
    latitude: Number, start_hour: int, end_hour: int
) -> Tuple[HourLine, ...]:
    """返回整点角度表，与 :func:`hour_lines` 的整点结果一致。"""
    return hour_lines(latitude, start_hour, end_hour, include_half_hours=False)


def gnomon_dimensions(
    latitude: Number, base_mm: Number = GNOMON_BASE_MM
) -> Tuple[float, float, float]:
    """计算三角晷针尺寸（底边、竖边、斜边），单位为毫米。

    锐角等于纬度绝对值：``height = base * tan(|phi|)``，
    ``hypotenuse = base / cos(|phi|)``。
    """
    latitude_value = validate_latitude(latitude)
    base = validate_length(base_mm, "晷针底边")
    angle = math.radians(abs(latitude_value))
    height = base * math.tan(angle)
    hypotenuse = base / math.cos(angle)
    return (base, height, hypotenuse)


def format_angle(angle_deg: Number) -> str:
    """把角度格式化为一位小数，避免出现 ``-0.0``。"""
    if not _is_number(angle_deg):
        raise SundialError("角度必须是数字")
    value = float(angle_deg)
    if not math.isfinite(value):
        raise SundialError("角度必须是有限数字")
    text = "%.1f" % value
    if text == "-0.0":
        return "0.0"
    return text


@dataclass(frozen=True)
class Sundial:
    """一份日晷制作参数。"""

    latitude: float = DEFAULT_LATITUDE
    start_hour: int = DEFAULT_START_HOUR
    end_hour: int = DEFAULT_END_HOUR
    title: str = DEFAULT_TITLE

    def __post_init__(self: "Sundial") -> None:
        latitude = validate_latitude(self.latitude)
        start, end = validate_hour_range(self.start_hour, self.end_hour)
        title = validate_title(self.title)
        object.__setattr__(self, "latitude", latitude)
        object.__setattr__(self, "start_hour", start)
        object.__setattr__(self, "end_hour", end)
        object.__setattr__(self, "title", title)

    @property
    def is_southern(self: "Sundial") -> bool:
        """是否位于南半球。"""
        return self.latitude < 0.0

    @property
    def hemisphere(self: "Sundial") -> str:
        """半球名称。"""
        if self.latitude < 0.0:
            return "南纬"
        if self.latitude > 0.0:
            return "北纬"
        return "赤道"

    @property
    def location_text(self: "Sundial") -> str:
        """纬度展示文本，例如 ``北纬 31.2°``。"""
        if self.latitude == 0.0:
            return "赤道 0°"
        return "%s %.1f°" % (self.hemisphere, abs(self.latitude))

    def hour_lines(
        self: "Sundial", include_half_hours: bool = False
    ) -> Tuple[HourLine, ...]:
        """生成本配置的时刻线。"""
        return hour_lines(
            self.latitude,
            self.start_hour,
            self.end_hour,
            include_half_hours=include_half_hours,
        )

    def angle_table(self: "Sundial") -> Tuple[HourLine, ...]:
        """生成本配置的整点角度表。"""
        return angle_table(self.latitude, self.start_hour, self.end_hour)

    def gnomon_dimensions(self: "Sundial") -> Tuple[float, float, float]:
        """生成本配置的三角晷针尺寸。"""
        return gnomon_dimensions(self.latitude)
