"""把日晷参数渲染为 A4 三页可打印制作卡。"""

from __future__ import annotations

import html
import math
from typing import List, Tuple

from .model import (
    DEFAULT_END_HOUR,
    DEFAULT_LATITUDE,
    DEFAULT_START_HOUR,
    DEFAULT_TITLE,
    Sundial,
    SundialError,
    format_angle,
    hour_line_endpoint,
)

PAGE_WIDTH_MM = 210.0
PAGE_HEIGHT_MM = 297.0
DIAL_RADIUS_MM = 80.0
DIAL_DIAMETER_MM = DIAL_RADIUS_MM * 2.0
DIAL_SVG_MM = 186.0
DIAL_CENTER_MM = DIAL_SVG_MM / 2.0
HOUR_LINE_RADIUS_MM = 76.0
HALF_HOUR_RADIUS_MM = 71.0
LABEL_RADIUS_MM = 65.0
GNOMON_SVG_WIDTH_MM = 186.0
GNOMON_BASE_X_MM = 58.0
GNOMON_TAB_HEIGHT_MM = 8.0


def _mm(value: float) -> str:
    """把毫米坐标格式化为紧凑文本。"""
    text = "%.2f" % float(value)
    if abs(float(text)) < 0.005:
        return "0"
    text = text.rstrip("0").rstrip(".")
    return text or "0"


def _hour_text(hour: float) -> str:
    """整点的简短数字文本。"""
    whole = int(round(hour))
    return str(whole)


def _dial_svg(sundial: Sundial) -> str:
    """绘制晷面盘：外圆、时刻线、数字、正午线与指北箭头。"""
    center = DIAL_CENTER_MM
    parts: List[str] = [
        '<svg class="dial" width="%smm" height="%smm" viewBox="0 0 %s %s" '
        'role="img" aria-label="%s">'
        % (
            _mm(DIAL_SVG_MM),
            _mm(DIAL_SVG_MM),
            _mm(DIAL_SVG_MM),
            _mm(DIAL_SVG_MM),
            html.escape("水平日晷晷面盘，%s" % sundial.location_text, quote=True),
        ),
        "<title>%s</title>" % html.escape(sundial.title),
        '<circle class="ring" cx="%s" cy="%s" r="%s"/>'
        % (_mm(center), _mm(center), _mm(DIAL_RADIUS_MM)),
        '<circle class="ring-inner" cx="%s" cy="%s" r="%s"/>'
        % (_mm(center), _mm(center), _mm(DIAL_RADIUS_MM - 2.2)),
    ]

    lines = sundial.hour_lines(include_half_hours=True)
    for line in lines:
        if line.half_hour:
            x, y = _line_endpoint(sundial, line.hour, HALF_HOUR_RADIUS_MM)
            parts.append(
                '<line class="half-hour-line" x1="%s" y1="%s" x2="%s" y2="%s" '
                'data-half-hour="%s" data-angle="%s"/>'
                % (
                    _mm(center),
                    _mm(center),
                    _mm(x),
                    _mm(y),
                    _mm(line.hour),
                    format_angle(line.angle_deg),
                )
            )
        else:
            x, y = _line_endpoint(sundial, line.hour, HOUR_LINE_RADIUS_MM)
            parts.append(
                '<line class="hour-line" x1="%s" y1="%s" x2="%s" y2="%s" '
                'data-hour="%s" data-angle="%s"/>'
                % (
                    _mm(center),
                    _mm(center),
                    _mm(x),
                    _mm(y),
                    _mm(line.hour),
                    format_angle(line.angle_deg),
                )
            )

    if sundial.is_southern:
        parts.append(
            '<line class="noon-line" x1="%s" y1="%s" x2="%s" y2="%s" '
            'data-noon-line="south"/>'
            % (_mm(center), _mm(center), _mm(center), _mm(center + DIAL_RADIUS_MM))
        )
        parts.extend(
            [
                '<line class="compass-line" x1="%s" y1="%s" x2="%s" y2="%s"/>'
                % (_mm(center), _mm(center - DIAL_RADIUS_MM + 1.0), _mm(center), "10.5"),
                '<polygon class="compass-head" points="%s,6 %s,10.5 %s,10.5"/>'
                % (_mm(center), _mm(center - 2.6), _mm(center + 2.6)),
                '<text class="compass-label" x="%s" y="8.5">北</text>'
                % _mm(center + 4.0),
            ]
        )
    else:
        parts.append(
            '<line class="noon-line" x1="%s" y1="%s" x2="%s" y2="%s" '
            'data-noon-line="north"/>'
            % (_mm(center), _mm(center), _mm(center), "10.5")
        )
        parts.extend(
            [
                '<polygon class="compass-head" points="%s,6 %s,10.5 %s,10.5"/>'
                % (_mm(center), _mm(center - 2.6), _mm(center + 2.6)),
                '<text class="compass-label" x="%s" y="8.5">北</text>'
                % _mm(center + 4.0),
            ]
        )

    parts.extend(
        [
            '<g class="center-mark">',
            '<circle cx="%s" cy="%s" r="7.5" fill="none" stroke="#9ca3af" '
            'stroke-width="0.2" stroke-dasharray="1.4 1.4"/>'
            % (_mm(center), _mm(center)),
            '<path d="M %s %s H %s M %s %s V %s" fill="none" stroke="#111827" '
            'stroke-width="0.45"/>'
            % (
                _mm(center - 6.0),
                _mm(center),
                _mm(center + 6.0),
                _mm(center),
                _mm(center - 6.0),
                _mm(center + 6.0),
            ),
            '<circle cx="%s" cy="%s" r="0.9" fill="#111827"/>'
            % (_mm(center), _mm(center)),
            "</g>",
        ]
    )
    for line in lines:
        if line.half_hour:
            continue
        x, y = _line_endpoint(sundial, line.hour, LABEL_RADIUS_MM)
        parts.append(
            '<text class="hour-label" x="%s" y="%s" data-label="%s">%s</text>'
            % (_mm(x), _mm(y), _mm(line.hour), _hour_text(line.hour))
        )

    parts.append("</svg>")
    return "".join(parts)


def _line_endpoint(sundial: Sundial, hour: float, radius: float) -> Tuple[float, float]:
    """在盘面上取某时刻线的端点。"""
    return hour_line_endpoint(
        sundial.latitude,
        hour,
        radius,
        DIAL_CENTER_MM,
        DIAL_CENTER_MM,
    )


def _gnomon_svg(sundial: Sundial) -> str:
    """绘制 1:1 三角晷针模板，含剪切线、折叠线与尺寸标注。"""
    base, height, hypotenuse = sundial.gnomon_dimensions()
    x0 = GNOMON_BASE_X_MM
    svg_height = max(70.0, height + 34.0)
    y0 = svg_height - 24.0
    x1 = x0 + base
    top = y0 - height
    tab_bottom = y0 + GNOMON_TAB_HEIGHT_MM
    ruler_y = svg_height - 3.0

    parts: List[str] = [
        '<svg class="gnomon" width="%smm" height="%smm" viewBox="0 0 %s %s" '
        'role="img" aria-label="%s">'
        % (
            _mm(GNOMON_SVG_WIDTH_MM),
            _mm(svg_height),
            _mm(GNOMON_SVG_WIDTH_MM),
            _mm(svg_height),
            html.escape("三角晷针模板，锐角 %.1f 度" % abs(sundial.latitude), quote=True),
        ),
        "<title>三角晷针模板</title>",
        # 外边剪裁线：A -> 折片左下 -> 折片右下 -> B -> C -> A
        '<path class="template-cut" d="M %s %s L %s %s L %s %s L %s %s L %s %s Z"/>'
        % (
            _mm(x0),
            _mm(y0),
            _mm(x0),
            _mm(tab_bottom),
            _mm(x1),
            _mm(tab_bottom),
            _mm(x1),
            _mm(y0),
            _mm(x1),
            _mm(top),
        ),
        '<path class="template-tab" d="M %s %s L %s %s L %s %s L %s %s Z"/>'
        % (
            _mm(x0),
            _mm(y0),
            _mm(x0),
            _mm(tab_bottom),
            _mm(x1),
            _mm(tab_bottom),
            _mm(x1),
            _mm(y0),
        ),
        # 折叠线 AB
        '<line class="template-fold" x1="%s" y1="%s" x2="%s" y2="%s"/>'
        % (_mm(x0), _mm(y0), _mm(x1), _mm(y0)),
    ]

    if height >= 0.5:
        parts.append(
            '<path class="template-guide" d="M %s %s L %s %s L %s %s"/>'
            % (_mm(x1 - 5.0), _mm(y0), _mm(x1 - 5.0), _mm(y0 - 5.0), _mm(x1), _mm(y0 - 5.0))
        )
        radius = 13.0
        end_x = x0 + radius * math.cos(math.radians(abs(sundial.latitude)))
        end_y = y0 - radius * math.sin(math.radians(abs(sundial.latitude)))
        parts.append(
            '<path class="template-guide" d="M %s %s A %s %s 0 0 0 %s %s"/>'
            % (
                _mm(x0 + radius),
                _mm(y0),
                _mm(radius),
                _mm(radius),
                _mm(end_x),
                _mm(end_y),
            )
        )
        label_x = x0 + 21.0 * math.cos(math.radians(abs(sundial.latitude) / 2.0))
        label_y = y0 - 21.0 * math.sin(math.radians(abs(sundial.latitude) / 2.0))
        parts.append(
            '<text class="template-label" x="%s" y="%s">φ=%s°</text>'
            % (_mm(label_x), _mm(label_y), format_angle(abs(sundial.latitude)))
        )
    else:
        parts.append(
            '<text class="template-warning" x="%s" y="%s">纬度 0°：晷针高度为 0，无法竖立</text>'
            % (_mm(x1 + 6.0), _mm(y0 - 4.0))
        )

    parts.extend(
        [
            # 点标注
            '<text class="template-label" x="%s" y="%s" text-anchor="end">A（盘心）</text>'
            % (_mm(x0 - 2.0), _mm(y0 - 3.0)),
            '<text class="template-label" x="%s" y="%s">B（直角）</text>'
            % (_mm(x1 + 2.0), _mm(y0 + 3.0)),
            '<text class="template-label" x="%s" y="%s">C</text>'
            % (_mm(x1 + 2.0), _mm(max(top + 1.0, 3.0))),
            # 折片文字
            '<text class="template-dim" x="%s" y="%s">折片（粘在盘面）</text>'
            % (_mm((x0 + x1) / 2.0), _mm(y0 + 5.0)),
            # 底边尺寸
            '<line class="template-ruler" x1="%s" y1="%s" x2="%s" y2="%s"/>'
            % (_mm(x0), _mm(y0 + 14.0), _mm(x1), _mm(y0 + 14.0)),
            '<line class="template-ruler" x1="%s" y1="%s" x2="%s" y2="%s"/>'
            % (_mm(x0), _mm(y0 + 12.8), _mm(x0), _mm(y0 + 15.2)),
            '<line class="template-ruler" x1="%s" y1="%s" x2="%s" y2="%s"/>'
            % (_mm(x1), _mm(y0 + 12.8), _mm(x1), _mm(y0 + 15.2)),
            '<text class="template-dim" x="%s" y="%s">底边 %s mm</text>'
            % (_mm((x0 + x1) / 2.0), _mm(y0 + 12.8), format_angle(base)),
            # 竖边尺寸
            '<line class="template-ruler" x1="128" y1="%s" x2="128" y2="%s"/>'
            % (_mm(top), _mm(y0)),
            '<line class="template-ruler" x1="126.5" y1="%s" x2="130.5" y2="%s"/>'
            % (_mm(top), _mm(top)),
            '<line class="template-ruler" x1="126.5" y1="%s" x2="130.5" y2="%s"/>'
            % (_mm(y0), _mm(y0)),
            '<text class="template-dim" x="132" y="%s" text-anchor="start">竖边 %s mm</text>'
            % (_mm((top + y0) / 2.0), format_angle(height)),
            # 斜边尺寸
            '<text class="template-dim" x="132" y="%s" text-anchor="start">斜边 %s mm</text>'
            % (_mm((top + y0) / 2.0 + 6.0), format_angle(hypotenuse)),
            # 50 mm 校准尺
            '<text class="template-dim" x="132" y="%s" text-anchor="start">50 mm 校准尺</text>'
            % _mm(ruler_y - 4.0),
            '<line class="template-ruler" x1="132" y1="%s" x2="182" y2="%s"/>'
            % (_mm(ruler_y), _mm(ruler_y)),
            '<line class="template-ruler" x1="132" y1="%s" x2="132" y2="%s"/>'
            % (_mm(ruler_y - 1.6), _mm(ruler_y + 1.6)),
            '<line class="template-ruler" x1="157" y1="%s" x2="157" y2="%s"/>'
            % (_mm(ruler_y - 1.2), _mm(ruler_y + 1.2)),
            '<line class="template-ruler" x1="182" y1="%s" x2="182" y2="%s"/>'
            % (_mm(ruler_y - 1.6), _mm(ruler_y + 1.6)),
            "</svg>",
        ]
    )
    return "".join(parts)


def _angle_rows(sundial: Sundial) -> str:
    """生成角度表行。"""
    rows: List[str] = []
    for line in sundial.angle_table():
        if line.hour < 12.0:
            side = "上午侧"
        elif line.hour > 12.0:
            side = "下午侧"
        else:
            side = "正午线"
        rows.append(
            '<tr class="angle-row" data-hour="%s"><td>%s</td><td>%s</td><td>%s</td></tr>'
            % (
                _mm(line.hour),
                line.label,
                format_angle(line.angle_deg),
                side,
            )
        )
    return "".join(rows)


def _guide_text(sundial: Sundial) -> str:
    """制作、校准与误差说明。"""
    base, height, hypotenuse = sundial.gnomon_dimensions()
    if sundial.is_southern:
        orient = (
            "南纬：把 12 时线朝向正南，指北箭头朝向地理北；"
            "晷针斜边必须朝南。"
        )
        reverse = (
            "<p><strong>南纬反向安装：</strong>把晷针模板绕盘心水平旋转 180°，"
            "让底边 AB 与斜边一起转向正南（与指北箭头相反）。若斜边朝北，"
            "影子会落在错误的一侧。</p>"
        )
        south_note = "南纬 θ 符号与北纬相反；把 12 时线朝南摆放后按盘面读数。"
    else:
        orient = "北纬：把 12 时线朝向正北，指北箭头朝向地理北；晷针斜边朝北。"
        reverse = (
            "<p><strong>南纬安装：</strong>若在南半球使用，把模板绕盘心旋转 180°，"
            "让斜边朝南，并把 12 时线朝向正南。</p>"
        )
        south_note = "符号表示盘面两侧；南半球符号相反。"

    if abs(sundial.latitude) < 0.05:
        equator_warning = (
            '<p class="warn"><strong>纬度 0°：</strong>晷针竖边高度为 0，'
            "本模板无法竖立，请改用赤道式日晷。</p>"
        )
    else:
        equator_warning = ""

    return (
        '<div class="guide-grid">'
        "<div>"
        "<h2>1 打印与裁剪</h2>"
        "<ul>"
        "<li>A4 纵向、缩放 100%%（不要选“适合页面”），用直尺核对 50 mm 校准尺。</li>"
        "<li>沿实线剪下晷面圆盘和晷针；虚线只折，不剪。</li>"
        "</ul>"
        "<h2>2 组装</h2>"
        "<ol>"
        "<li>沿晷针 AB 虚线把折片向背面折 90°。</li>"
        "<li>折片平贴在盘心，A 点对准十字，斜边 A→C 落在正午线上。</li>"
        "<li>%s</li>"
        "</ol>"
        "%s"
        "<h2>3 校准</h2>"
        "<p>把晷面放在水平台面。当地真太阳时正午（太阳最高、影子最短）时，"
        "转动晷面，使晷针影子与 12 时线重合；此时正午线指向正北（南纬指向正南）。</p>"
        "<p>影子落在哪条整点线上，就读该时刻的地方真太阳时；细虚线为半点。</p>"
        "<h2>4 真太阳时与钟表时间</h2>"
        "<p>钟表时间 ≈ 真太阳时 − 均时差 +（120° − 当地经度）× 4 分钟。"
        "均时差全年约在 −14 到 +16 分钟之间；中国统一使用东经 120° 区时，"
        "经度每差 1° 约差 4 分钟。</p>"
        "<h2>5 误差与注意</h2>"
        "<ul>"
        "<li>本卡按春分/秋分（太阳赤纬 0°）绘制；主要误差来自晷针角度、"
        "盘面是否水平、12 时线是否对准正北/正南。</li>"
        "<li>纬度改变必须重新生成：时刻线角随 sin φ 变化，晷针锐角也要等于新纬度。</li>"
        "<li>打印缩放会改变 160 mm 直径与晷针角度，请务必 100%% 打印。</li>"
        "<li>5 点、19 点等超出 6–18 点的线仅作延长参考，实际日出日落随季节变化。</li>"
        "</ul>"
        "<h2>6 常见问题</h2>"
        "<ul>"
        "<li>影子落在两线之间：按比例估读；整点读数以整点线为准。</li>"
        "<li>与钟表相差约 1 小时：先做经度修正（每 1° 约 4 分钟），再查均时差。</li>"
        "<li>南纬读数左右相反：确认 12 时线朝南、晷针斜边朝南。</li>"
        "</ul>"
        "</div>"
        "<div>"
        '<div class="fact">'
        "<strong>本卡尺寸</strong>"
        "<span>晷面直径 160 mm</span>"
        "<span>晷针底边 %s mm · 竖边 %s mm</span>"
        "<span>斜边 %s mm · 锐角 %s°</span>"
        "</div>"
        '<table class="angles">'
        "<caption>%s · 时刻线角度表</caption>"
        "<thead><tr><th>时刻</th><th>θ（°）</th><th>位置</th></tr></thead>"
        "<tbody>%s</tbody>"
        "</table>"
        '<p class="note-small">θ 自正午线起算，−90°～90°。%s</p>'
        '<p class="note-small">纬度改变后请重新生成，不要沿用旧晷针。</p>'
        "</div>"
        "</div>"
        % (
            orient,
            reverse,
            format_angle(base),
            format_angle(height),
            format_angle(hypotenuse),
            format_angle(abs(sundial.latitude)),
            html.escape(sundial.location_text),
            _angle_rows(sundial),
            south_note,
        )
        + equator_warning
    )


def render_sundial(sundial: Sundial) -> str:
    """渲染完整三页 HTML。"""
    if not isinstance(sundial, Sundial):
        raise SundialError("sundial 必须是 Sundial 对象")

    title = html.escape(sundial.title)
    title_class = ' class="long"' if len(sundial.title) > 20 else ""
    location = html.escape(sundial.location_text)
    period = "%02d:00–%02d:00" % (sundial.start_hour, sundial.end_hour)
    base, height, hypotenuse = sundial.gnomon_dimensions()

    if abs(sundial.latitude) < 0.05:
        dial_note = (
            "赤道 0°：水平晷面退化，内部时刻线重合于正午线，本盘仅作教学演示；"
            "请改用赤道式日晷。"
        )
    elif sundial.is_southern:
        dial_note = (
            "12 时线在本盘下方（朝南），指北箭头仍朝地理北。"
            "南纬安装时晷针斜边必须朝南。"
        )
    else:
        dial_note = "12 时线在本盘上方（朝北），指北箭头朝地理北。"

    page1 = (
        '<section class="sheet" data-page="1">'
        '<header class="sheet-head">'
        '<p class="kicker">水平日晷 · 制作卡</p>'
        "<h1%s>%s</h1>"
        '<p class="sub">%s · 时刻线 %s（地方真太阳时）</p>'
        "</header>"
        '<figure class="dial-wrap">%s<figcaption>表盘外圆直径 160 mm · '
        "盘心十字为晷针粘贴位</figcaption></figure>"
        '<div class="dial-notes">'
        "<p><strong>读法：</strong>影子落在哪条整点线上，就是该时刻的地方真太阳时；"
        "细虚线为半点。</p>"
        "<p><strong>定向：</strong>%s</p>"
        "</div>"
        '<footer class="sheet-foot"><span>%s</span><span>第 1 / 3 页</span></footer>'
        "</section>"
        % (
            title_class,
            title,
            location,
            period,
            _dial_svg(sundial),
            dial_note,
            title,
        )
    )

    page2 = (
        '<section class="sheet" data-page="2">'
        '<header class="sheet-head compact">'
        '<p class="kicker">晷针模板 · 1:1</p>'
        "<h1>三角晷针</h1>"
        '<p class="sub">锐角 = |φ| = %s° · 底边 %s mm · 竖边 %s mm · 斜边 %s mm</p>'
        "</header>"
        "%s"
        '<div class="two-col notes">'
        "<div>"
        "<h3>剪切、折叠与粘贴</h3>"
        "<ol>"
        "<li>沿实线剪下三角形与下方折片，AB 虚线不要剪。</li>"
        "<li>沿 AB 虚线把折片向三角形背面折 90°。</li>"
        "<li>折片平贴在盘心，A 点对准十字，斜边 A→C 落在正午线上。</li>"
        "<li>北纬斜边朝北；南纬按右侧说明反向安装。</li>"
        "</ol>"
        "</div>"
        "<div>"
        "<h3>南纬反向安装</h3>"
        "<p>北纬：斜边朝北，指向北天极。南纬：把模板绕盘心水平旋转 180° 再粘，"
        "让底边 AB 与斜边一起转向正南（与指北箭头相反），绝不能朝北。</p>"
        "%s"
        '<p class="note-small">剪切线为实线，折叠线 AB 为虚线；'
        "打印后先核对 50 mm 校准尺。</p>"
        "</div>"
        "</div>"
        '<footer class="sheet-foot"><span>%s · %s</span>'
        "<span>第 2 / 3 页</span></footer>"
        "</section>"
        % (
            format_angle(abs(sundial.latitude)),
            format_angle(base),
            format_angle(height),
            format_angle(hypotenuse),
            _gnomon_svg(sundial),
            (
                '<p class="warn"><strong>纬度 0°：</strong>晷针高度为 0，'
                "本模板无法竖立，请改用赤道式日晷。</p>"
                if abs(sundial.latitude) < 0.05
                else ""
            ),
            title,
            location,
        )
    )

    page3 = (
        '<section class="sheet" data-page="3">'
        '<header class="sheet-head compact">'
        '<p class="kicker">制作 · 校准 · 角度表</p>'
        "<h1>制作说明</h1>"
        '<p class="sub">%s · 晷针锐角 %s° · 时刻线 %s</p>'
        "</header>"
        "%s"
        '<footer class="sheet-foot"><span>%s · 零依赖生成</span>'
        "<span>第 3 / 3 页</span></footer>"
        "</section>"
        % (
            location,
            format_angle(abs(sundial.latitude)),
            period,
            _guide_text(sundial),
            title,
        )
    )

    toolbar = (
        '<div class="toolbar"><strong>%s</strong>'
        "<span>%s · 时刻线 %s · 3 页 A4</span></div>"
        % (title, location, period)
    )

    return (
        "<!doctype html>\n"
        '<html lang="zh-CN">\n<head>\n<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        "<title>%s</title>\n<style>%s</style>\n</head>\n<body>\n"
        "%s\n%s\n%s\n%s\n</body>\n</html>\n"
        % (title, _style(), toolbar, page1, page2, page3)
    )


def render_html(
    latitude: float = DEFAULT_LATITUDE,
    start_hour: int = DEFAULT_START_HOUR,
    end_hour: int = DEFAULT_END_HOUR,
    title: str = DEFAULT_TITLE,
) -> str:
    """按参数构造 :class:`Sundial` 并渲染 HTML。"""
    return render_sundial(
        Sundial(
            latitude=latitude,
            start_hour=start_hour,
            end_hour=end_hour,
            title=title,
        )
    )


def _style() -> str:
    """返回自包含样式：屏幕自适应，打印保持毫米真实尺寸。"""
    return """
  :root { color-scheme: light; }
  * { box-sizing: border-box; }
  body {
    margin: 0;
    padding: 10mm 0 14mm;
    background: #e5e7eb;
    color: #111827;
    font-family: "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei",
      "Noto Sans CJK SC", sans-serif;
    line-height: 1.45;
  }
  .toolbar {
    width: 210mm;
    max-width: calc(100% - 8mm);
    margin: 0 auto 4mm;
    display: flex;
    flex-wrap: wrap;
    align-items: baseline;
    justify-content: space-between;
    gap: 4mm;
    color: #374151;
    font-size: 9pt;
  }
  .toolbar strong { letter-spacing: 1pt; overflow-wrap: anywhere; }
  .sheet {
    width: 210mm;
    height: 297mm;
    padding: 12mm 12mm 9mm;
    margin: 0 auto 6mm;
    background: #fff;
    box-shadow: 0 4px 18px rgba(15, 23, 42, 0.18);
    page-break-after: always;
    break-after: page;
    overflow: hidden;
    display: flex;
    flex-direction: column;
  }
  .sheet:last-child { page-break-after: auto; break-after: auto; }
  .sheet-head { text-align: center; margin-bottom: 2mm; }
  .sheet-head.compact { margin-bottom: 1mm; }
  .kicker {
    margin: 0 0 1mm;
    font-size: 7.5pt;
    letter-spacing: 2.4pt;
    color: #6b7280;
  }
  h1 {
    margin: 0;
    font-size: 20pt;
    font-weight: 600;
    letter-spacing: 3pt;
    overflow-wrap: anywhere;
  }
  .sheet-head h1.long { font-size: 15pt; letter-spacing: 1pt; }
  .sheet-head.compact h1 { font-size: 15pt; letter-spacing: 2pt; }
  .sub { margin: 1mm 0 0; font-size: 9pt; color: #374151; }
  .dial-wrap { margin: 0; text-align: center; }
  .dial-wrap figcaption {
    margin-top: 1mm;
    font-size: 8pt;
    color: #4b5563;
  }
  .dial, .gnomon {
    display: block;
    max-width: 100%;
    height: auto;
    margin: 0 auto;
  }
  .dial-notes {
    margin-top: 2mm;
    padding-top: 2mm;
    border-top: 0.3mm solid #d1d5db;
    display: grid;
    grid-template-columns: 1.15fr 0.85fr;
    gap: 4mm;
    font-size: 8.5pt;
    color: #374151;
  }
  .dial-notes p { margin: 0; }
  .two-col {
    display: grid;
    grid-template-columns: 1.05fr 0.95fr;
    gap: 6mm;
  }
  .notes {
    margin-top: 2mm;
    padding-top: 2mm;
    border-top: 0.3mm solid #d1d5db;
    font-size: 8.5pt;
    color: #374151;
  }
  .notes h3, .guide-grid h2 {
    margin: 0 0 1mm;
    font-size: 10pt;
    color: #111827;
  }
  .notes ol, .notes ul, .guide-grid ol, .guide-grid ul {
    margin: 0;
    padding-left: 4.5mm;
  }
  .notes li, .guide-grid li { margin-bottom: 0.8mm; }
  .notes p { margin: 0 0 1.2mm; }
  .guide-grid {
    display: grid;
    grid-template-columns: 1.08fr 0.92fr;
    gap: 6mm;
    align-items: start;
    font-size: 9.2pt;
    line-height: 1.55;
    color: #1f2937;
  }
  .sheet:last-child .guide-grid {
    margin-top: auto;
    margin-bottom: auto;
  }
  .guide-grid h2 {
    margin: 2mm 0 1.2mm;
    padding-left: 2mm;
    border-left: 1.2mm solid #b91c1c;
    font-size: 11pt;
  }
  .guide-grid h2:first-child { margin-top: 0; }
  .guide-grid p { margin: 0 0 1.2mm; }
  .fact {
    display: flex;
    flex-direction: column;
    gap: 0.6mm;
    margin-bottom: 3mm;
    padding: 2mm 2.5mm;
    border: 0.25mm solid #d1d5db;
    background: #f9fafb;
    font-size: 9pt;
    color: #374151;
  }
  .fact strong { color: #111827; font-size: 9.6pt; }
  table.angles {
    width: 100%;
    border-collapse: collapse;
    font-size: 8.8pt;
    table-layout: fixed;
  }
  table.angles caption {
    caption-side: top;
    padding-bottom: 1mm;
    font-size: 9.5pt;
    font-weight: 600;
    color: #111827;
  }
  table.angles th, table.angles td {
    border: 0.2mm solid #9ca3af;
    padding: 1.1mm 1.2mm;
    text-align: center;
  }
  table.angles th { background: #f3f4f6; font-weight: 600; }
  table.angles tbody tr:nth-child(even) { background: #f9fafb; }
  .note-small { font-size: 8pt; color: #6b7280; }
  .warn {
    margin: 1mm 0;
    padding: 1.2mm 2mm;
    border-left: 1mm solid #b91c1c;
    background: #fef2f2;
    color: #7f1d1d;
  }
  .sheet-foot {
    margin-top: auto;
    padding-top: 2mm;
    border-top: 0.25mm solid #e5e7eb;
    display: flex;
    justify-content: space-between;
    font-size: 7.5pt;
    color: #6b7280;
  }
  .ring { fill: #fff; stroke: #111827; stroke-width: 0.6; }
  .ring-inner { fill: none; stroke: #9ca3af; stroke-width: 0.2; }
  .hour-line { stroke: #374151; stroke-width: 0.35; }
  .half-hour-line {
    stroke: #9ca3af;
    stroke-width: 0.18;
    stroke-dasharray: 0.9 0.9;
  }
  .noon-line { stroke: #b91c1c; stroke-width: 0.65; }
  .hour-label {
    fill: #111827;
    font-size: 3.4px;
    font-weight: 600;
    text-anchor: middle;
    dominant-baseline: central;
    paint-order: stroke;
    stroke: #fff;
    stroke-width: 1.4;
  }
  .compass-line { stroke: #111827; stroke-width: 0.45; }
  .compass-head { fill: #111827; }
  .compass-label {
    fill: #111827;
    font-size: 3.2px;
    font-weight: 600;
  }
  .template-cut { fill: #f9fafb; stroke: #111827; stroke-width: 0.5; }
  .template-tab { fill: #f3f4f6; stroke: none; }
  .template-fold {
    fill: none;
    stroke: #1d4ed8;
    stroke-width: 0.45;
    stroke-dasharray: 2 1.2;
  }
  .template-guide { fill: none; stroke: #6b7280; stroke-width: 0.2; }
  .template-ruler { stroke: #111827; stroke-width: 0.2; }
  .template-label { fill: #111827; font-size: 3px; }
  .template-dim {
    fill: #374151;
    font-size: 2.8px;
    text-anchor: middle;
  }
  .template-warning { fill: #b91c1c; font-size: 3px; font-weight: 600; }
  @page { size: A4 portrait; margin: 0; }
  @media print {
    body { background: #fff; padding: 0; }
    .toolbar { display: none; }
    .sheet { margin: 0; box-shadow: none; }
    * { -webkit-print-color-adjust: exact; print-color-adjust: exact; }
  }
  @media screen and (max-width: 820px) {
    body { padding: 4mm 3mm 10mm; }
    .toolbar { width: 100%; max-width: 100%; flex-wrap: wrap; }
    .sheet {
      width: 100%;
      height: auto;
      min-height: 0;
      padding: 6mm 5mm;
      margin-bottom: 4mm;
    }
    h1 { font-size: 15pt; letter-spacing: 1.5pt; }
    .sheet-head.compact h1 { font-size: 13pt; }
    .dial-notes, .two-col, .guide-grid { grid-template-columns: 1fr; }
  }
"""
