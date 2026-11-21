"""render 模块单元测试：三页结构、SVG、转义与打印样式。"""

from __future__ import annotations

import unittest

from sundial.model import Sundial, SundialError
from sundial.render import render_html, render_sundial


class RenderHtmlTest(unittest.TestCase):
    def setUp(self) -> None:
        self.page = render_html()

    def test_doctype_and_language(self) -> None:
        self.assertTrue(self.page.startswith("<!doctype html>"))
        self.assertIn('<html lang="zh-CN">', self.page)
        self.assertIn('name="viewport"', self.page)

    def test_three_pages(self) -> None:
        self.assertEqual(self.page.count('class="sheet"'), 3)
        for number in (1, 2, 3):
            self.assertIn('data-page="%d"' % number, self.page)
        self.assertEqual(self.page.count("data-page="), 3)

    def test_a4_portrait(self) -> None:
        self.assertIn("@page { size: A4 portrait; margin: 0; }", self.page)
        self.assertIn("width: 210mm", self.page)
        self.assertIn("height: 297mm", self.page)
        self.assertIn("break-after: page", self.page)

    def test_screen_responsive(self) -> None:
        self.assertIn("@media screen and (max-width: 820px)", self.page)
        self.assertIn("max-width: 100%", self.page)

    def test_dial_size(self) -> None:
        self.assertIn("表盘外圆直径 160 mm", self.page)
        self.assertIn('width="186mm"', self.page)
        self.assertIn('viewBox="0 0 186 186"', self.page)

    def test_hour_lines_count(self) -> None:
        self.assertEqual(self.page.count('class="hour-line"'), 13)

    def test_half_hour_lines_count(self) -> None:
        self.assertEqual(self.page.count('class="half-hour-line"'), 12)
        self.assertIn('data-half-hour="6.5"', self.page)
        self.assertIn('data-half-hour="17.5"', self.page)

    def test_hour_labels(self) -> None:
        self.assertEqual(self.page.count('class="hour-label"'), 13)
        for hour in range(6, 19):
            self.assertIn('data-label="%d"' % hour, self.page)

    def test_noon_line_north(self) -> None:
        self.assertIn('data-noon-line="north"', self.page)
        self.assertNotIn('data-noon-line="south"', self.page)

    def test_center_cross(self) -> None:
        self.assertIn('class="center-mark"', self.page)

    def test_north_arrow(self) -> None:
        self.assertIn('class="compass-head"', self.page)
        self.assertIn("北", self.page)

    def test_angle_table_rows(self) -> None:
        self.assertEqual(self.page.count('class="angle-row"'), 13)

    def test_angle_table_values(self) -> None:
        self.assertIn("<td>06:00</td><td>-90.0</td>", self.page)
        self.assertIn("<td>12:00</td><td>0.0</td>", self.page)
        self.assertIn("<td>18:00</td><td>90.0</td>", self.page)

    def test_angle_table_position(self) -> None:
        self.assertIn("上午侧", self.page)
        self.assertIn("下午侧", self.page)
        self.assertIn("正午线", self.page)

    def test_location_in_page(self) -> None:
        self.assertIn("北纬 31.2°", self.page)

    def test_title_escaped(self) -> None:
        page = render_html(title="<b>日晷</b>")
        self.assertIn("&lt;b&gt;日晷&lt;/b&gt;", page)
        self.assertNotIn("<b>日晷</b>", page)

    def test_title_in_head(self) -> None:
        page = render_html(title="我的日晷")
        self.assertIn("<title>我的日晷</title>", page)

    def test_gnomon_page(self) -> None:
        self.assertIn("三角晷针", self.page)
        self.assertIn("折片（粘在盘面）", self.page)
        self.assertIn("剪切、折叠与粘贴", self.page)
        self.assertIn("50 mm 校准尺", self.page)
        self.assertIn('class="template-cut"', self.page)
        self.assertIn('class="template-fold"', self.page)

    def test_gnomon_dimensions_text(self) -> None:
        self.assertIn("底边 60.0 mm", self.page)
        self.assertIn("锐角 = |φ| = 31.2°", self.page)

    def test_guide_content(self) -> None:
        for text in ("校准", "真太阳时", "均时差", "纬度改变必须重新生成", "100% 打印"):
            self.assertIn(text, self.page)

    def test_no_network_resources(self) -> None:
        for token in ("http://", "https://", "<script", "<link", "@import", "url("):
            self.assertNotIn(token, self.page)

    def test_print_color_adjust(self) -> None:
        self.assertIn("print-color-adjust: exact", self.page)

    def test_custom_range(self) -> None:
        page = render_html(start_hour=8, end_hour=16)
        self.assertEqual(page.count('class="hour-line"'), 9)
        self.assertEqual(page.count('class="angle-row"'), 9)
        self.assertIn("08:00–16:00", page)
        self.assertIn("<td>08:00</td>", page)
        self.assertNotIn("<td>06:00</td>", page)

    def test_custom_title(self) -> None:
        page = render_html(title="阳台日晷")
        self.assertEqual(page.count("阳台日晷"), 7)

    def test_south_hemisphere(self) -> None:
        page = render_html(latitude=-31.2)
        self.assertIn('data-noon-line="south"', page)
        self.assertIn("南纬 31.2°", page)
        self.assertIn("南纬反向安装", page)
        self.assertIn("水平旋转 180°", page)
        self.assertIn("12 时线在本盘下方", page)

    def test_north_installation_hint(self) -> None:
        self.assertIn("北纬：斜边朝北", self.page)
        self.assertIn("南纬安装", self.page)

    def test_equator_warning(self) -> None:
        page = render_html(latitude=0)
        self.assertIn("赤道 0°", page)
        self.assertIn("无法竖立", page)
        self.assertIn("纬度 0°：", page)

    def test_boundary_latitude(self) -> None:
        for latitude in (-66.0, 66.0):
            page = render_html(latitude=latitude)
            self.assertIn("锐角 = |φ| = 66.0°", page)

    def test_southern_angle_table(self) -> None:
        page = render_html(latitude=-31.2)
        self.assertIn("<td>06:00</td><td>90.0</td>", page)
        self.assertIn("<td>18:00</td><td>-90.0</td>", page)

    def test_render_sundial(self) -> None:
        page = render_sundial(Sundial(latitude=10.0))
        self.assertIn("北纬 10.0°", page)

    def test_invalid_sundial(self) -> None:
        with self.assertRaises(SundialError):
            render_sundial("sundial")  # type: ignore[arg-type]

    def test_invalid_latitude(self) -> None:
        with self.assertRaises(SundialError):
            render_html(latitude=70.0)

    def test_invalid_range(self) -> None:
        with self.assertRaises(SundialError):
            render_html(start_hour=12, end_hour=12)
        with self.assertRaises(SundialError):
            render_html(start_hour=4)

    def test_invalid_title(self) -> None:
        with self.assertRaises(SundialError):
            render_html(title="")
        with self.assertRaises(SundialError):
            render_html(title="字" * 41)

    def test_render_deterministic(self) -> None:
        self.assertEqual(render_html(), render_html())


if __name__ == "__main__":
    unittest.main()
