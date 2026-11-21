"""model 模块单元测试：几何、校验与数据模型。"""

from __future__ import annotations

import math
import unittest

from sundial.model import (
    DEFAULT_END_HOUR,
    DEFAULT_LATITUDE,
    DEFAULT_START_HOUR,
    DEFAULT_TITLE,
    GNOMON_BASE_MM,
    HourLine,
    Sundial,
    SundialError,
    angle_table,
    format_angle,
    gnomon_dimensions,
    hour_angle,
    hour_line_endpoint,
    hour_lines,
)


class HourAngleTest(unittest.TestCase):
    def test_noon_zero_north(self) -> None:
        self.assertEqual(hour_angle(31.2, 12), 0.0)

    def test_noon_zero_south(self) -> None:
        self.assertEqual(hour_angle(-31.2, 12), 0.0)

    def test_six_north(self) -> None:
        self.assertEqual(hour_angle(31.2, 6), -90.0)

    def test_eighteen_north(self) -> None:
        self.assertEqual(hour_angle(31.2, 18), 90.0)

    def test_six_south(self) -> None:
        self.assertEqual(hour_angle(-31.2, 6), 90.0)

    def test_eighteen_south(self) -> None:
        self.assertEqual(hour_angle(-31.2, 18), -90.0)

    def test_symmetry_north(self) -> None:
        for hour in (7, 8, 9, 10, 11):
            self.assertAlmostEqual(
                hour_angle(31.2, hour),
                -hour_angle(31.2, 24 - hour),
                places=9,
            )

    def test_symmetry_south(self) -> None:
        for hour in (7, 8, 9, 10, 11):
            self.assertAlmostEqual(
                hour_angle(-31.2, hour),
                -hour_angle(-31.2, 24 - hour),
                places=9,
            )

    def test_hemisphere_mirror(self) -> None:
        for hour in range(6, 19):
            self.assertAlmostEqual(
                hour_angle(31.2, hour),
                -hour_angle(-31.2, hour),
                places=9,
            )

    def test_equator_interior_zero(self) -> None:
        for hour in (7, 8, 9, 10, 11, 13, 14, 15, 16, 17):
            self.assertAlmostEqual(hour_angle(0, hour), 0.0, places=9)

    def test_equator_boundaries(self) -> None:
        self.assertEqual(hour_angle(0, 6), -90.0)
        self.assertEqual(hour_angle(0, 18), 90.0)

    def test_boundary_latitudes_are_finite(self) -> None:
        for latitude in (-66.0, 66.0):
            for hour in range(6, 19):
                self.assertTrue(math.isfinite(hour_angle(latitude, hour)))

    def test_boundary_latitudes_mirror(self) -> None:
        for hour in range(6, 19):
            self.assertAlmostEqual(
                hour_angle(66.0, hour),
                -hour_angle(-66.0, hour),
                places=9,
            )

    def test_all_angles_within_limits(self) -> None:
        for latitude in (-66.0, -31.2, 0.0, 31.2, 66.0):
            for hour in range(5, 20):
                self.assertLessEqual(abs(hour_angle(latitude, hour)), 90.0)

    def test_afternoon_opposite_of_morning(self) -> None:
        self.assertLess(hour_angle(31.2, 9), 0.0)
        self.assertGreater(hour_angle(31.2, 15), 0.0)
        self.assertGreater(hour_angle(-31.2, 9), 0.0)
        self.assertLess(hour_angle(-31.2, 15), 0.0)

    def test_fractional_hour(self) -> None:
        self.assertAlmostEqual(
            hour_angle(31.2, 12.5),
            -hour_angle(31.2, 11.5),
            places=9,
        )

    def test_invalid_latitudes(self) -> None:
        for latitude in (-66.1, 66.1, "31", None, True, float("nan"), float("inf")):
            with self.assertRaises(SundialError):
                hour_angle(latitude, 12)  # type: ignore[arg-type]

    def test_invalid_hours(self) -> None:
        for hour in (4.9, 19.1, "12", None, False, float("nan"), float("inf")):
            with self.assertRaises(SundialError):
                hour_angle(31.2, hour)  # type: ignore[arg-type]


class EndpointTest(unittest.TestCase):
    def test_north_noon_points_up(self) -> None:
        x, y = hour_line_endpoint(31.2, 12, 100.0)
        self.assertAlmostEqual(x, 0.0, places=9)
        self.assertAlmostEqual(y, -100.0, places=9)

    def test_south_noon_points_down(self) -> None:
        x, y = hour_line_endpoint(-31.2, 12, 100.0)
        self.assertAlmostEqual(x, 0.0, places=9)
        self.assertAlmostEqual(y, 100.0, places=9)

    def test_six_west_in_both_hemispheres(self) -> None:
        for latitude in (31.2, -31.2):
            x, y = hour_line_endpoint(latitude, 6, 100.0)
            self.assertAlmostEqual(x, -100.0, places=9)
            self.assertAlmostEqual(y, 0.0, places=9)

    def test_eighteen_east_in_both_hemispheres(self) -> None:
        for latitude in (31.2, -31.2):
            x, y = hour_line_endpoint(latitude, 18, 100.0)
            self.assertAlmostEqual(x, 100.0, places=9)
            self.assertAlmostEqual(y, 0.0, places=9)

    def test_center_offset(self) -> None:
        x, y = hour_line_endpoint(31.2, 12, 10.0, 93.0, 93.0)
        self.assertAlmostEqual(x, 93.0, places=9)
        self.assertAlmostEqual(y, 83.0, places=9)

    def test_invalid_radius(self) -> None:
        for radius in (0.0, -5.0, "10", None, float("nan")):
            with self.assertRaises(SundialError):
                hour_line_endpoint(31.2, 12, radius)  # type: ignore[arg-type]

    def test_invalid_center(self) -> None:
        with self.assertRaises(SundialError):
            hour_line_endpoint(31.2, 12, 10.0, "x", 0.0)  # type: ignore[arg-type]
        with self.assertRaises(SundialError):
            hour_line_endpoint(31.2, 12, 10.0, 0.0, float("nan"))

    def test_invalid_hour(self) -> None:
        with self.assertRaises(SundialError):
            hour_line_endpoint(31.2, 20, 10.0)

    def test_invalid_latitude(self) -> None:
        with self.assertRaises(SundialError):
            hour_line_endpoint(67.0, 12, 10.0)


class HourLinesTest(unittest.TestCase):
    def test_default_count(self) -> None:
        self.assertEqual(len(hour_lines(31.2, 6, 18)), 13)

    def test_first_and_last(self) -> None:
        lines = hour_lines(31.2, 6, 18)
        self.assertEqual(lines[0].hour, 6.0)
        self.assertEqual(lines[-1].hour, 18.0)
        self.assertEqual(lines[0].angle_deg, -90.0)
        self.assertEqual(lines[-1].angle_deg, 90.0)

    def test_angles_match_function(self) -> None:
        for line in hour_lines(31.2, 6, 18):
            self.assertAlmostEqual(
                line.angle_deg, hour_angle(31.2, line.hour), places=9
            )

    def test_half_hour_count(self) -> None:
        lines = hour_lines(31.2, 6, 18, include_half_hours=True)
        self.assertEqual(len(lines), 25)
        self.assertEqual(sum(1 for line in lines if line.half_hour), 12)

    def test_half_hour_labels(self) -> None:
        lines = hour_lines(31.2, 6, 18, include_half_hours=True)
        labels = [line.label for line in lines if line.half_hour]
        self.assertIn("06:30", labels)
        self.assertIn("17:30", labels)

    def test_angle_table_matches(self) -> None:
        table = angle_table(31.2, 6, 18)
        left = [(line.hour, line.angle_deg) for line in table]
        right = [(line.hour, line.angle_deg) for line in hour_lines(31.2, 6, 18)]
        self.assertEqual(left, right)

    def test_custom_range_count(self) -> None:
        self.assertEqual(len(hour_lines(31.2, 8, 16)), 9)

    def test_full_range_count(self) -> None:
        self.assertEqual(len(hour_lines(31.2, 5, 19)), 15)

    def test_invalid_ranges(self) -> None:
        for start, end in ((6, 6), (10, 8), (4, 12), (6, 20)):
            with self.assertRaises(SundialError):
                hour_lines(31.2, start, end)

    def test_non_integer_range(self) -> None:
        for start, end in ((6.0, 18), (6, "18"), (True, 18)):
            with self.assertRaises(SundialError):
                hour_lines(31.2, start, end)  # type: ignore[arg-type]

    def test_non_boolean_flag(self) -> None:
        with self.assertRaises(SundialError):
            hour_lines(31.2, 6, 18, include_half_hours=1)  # type: ignore[arg-type]

    def test_invalid_latitude(self) -> None:
        with self.assertRaises(SundialError):
            hour_lines(70.0, 6, 18)


class HourLineTest(unittest.TestCase):
    def test_label(self) -> None:
        self.assertEqual(HourLine(6.0, -90.0).label, "06:00")
        self.assertEqual(HourLine(12.0, 0.0).label, "12:00")
        self.assertEqual(HourLine(6.5, -80.0, True).label, "06:30")

    def test_invalid_angle(self) -> None:
        for angle in (90.1, -91.0, "0", None, float("nan")):
            with self.assertRaises(SundialError):
                HourLine(12.0, angle)  # type: ignore[arg-type]

    def test_invalid_half_hour_flag(self) -> None:
        with self.assertRaises(SundialError):
            HourLine(12.0, 0.0, 1)  # type: ignore[arg-type]

    def test_invalid_hour(self) -> None:
        with self.assertRaises(SundialError):
            HourLine(20.0, 0.0)


class SundialTest(unittest.TestCase):
    def test_defaults(self) -> None:
        sundial = Sundial()
        self.assertEqual(sundial.latitude, DEFAULT_LATITUDE)
        self.assertEqual(sundial.start_hour, DEFAULT_START_HOUR)
        self.assertEqual(sundial.end_hour, DEFAULT_END_HOUR)
        self.assertEqual(sundial.title, DEFAULT_TITLE)

    def test_hemisphere_properties(self) -> None:
        self.assertTrue(Sundial(latitude=-31.2).is_southern)
        self.assertFalse(Sundial(latitude=31.2).is_southern)
        self.assertEqual(Sundial(latitude=31.2).hemisphere, "北纬")
        self.assertEqual(Sundial(latitude=-31.2).hemisphere, "南纬")
        self.assertEqual(Sundial(latitude=0).hemisphere, "赤道")

    def test_location_text(self) -> None:
        self.assertEqual(Sundial(latitude=31.2).location_text, "北纬 31.2°")
        self.assertEqual(Sundial(latitude=-31.2).location_text, "南纬 31.2°")
        self.assertEqual(Sundial(latitude=0).location_text, "赤道 0°")

    def test_title_trimmed(self) -> None:
        self.assertEqual(Sundial(title="  日晷  ").title, "日晷")

    def test_invalid_titles(self) -> None:
        for title in ("", "   ", "字" * 41, "a\nb", 123):
            with self.assertRaises(SundialError):
                Sundial(title=title)  # type: ignore[arg-type]

    def test_title_max_length(self) -> None:
        self.assertEqual(len(Sundial(title="字" * 40).title), 40)

    def test_invalid_hours(self) -> None:
        with self.assertRaises(SundialError):
            Sundial(start_hour=4)
        with self.assertRaises(SundialError):
            Sundial(end_hour=20)
        with self.assertRaises(SundialError):
            Sundial(start_hour=12, end_hour=12)

    def test_hour_lines(self) -> None:
        self.assertEqual(len(Sundial().hour_lines()), 13)
        self.assertEqual(len(Sundial().hour_lines(True)), 25)
        self.assertEqual(len(Sundial().angle_table()), 13)

    def test_gnomon_dimensions(self) -> None:
        base, height, hypotenuse = Sundial(latitude=31.2).gnomon_dimensions()
        self.assertEqual(base, GNOMON_BASE_MM)
        self.assertAlmostEqual(height / base, math.tan(math.radians(31.2)))
        self.assertAlmostEqual(hypotenuse * math.cos(math.radians(31.2)), base)

    def test_gnomon_zero_latitude(self) -> None:
        base, height, hypotenuse = gnomon_dimensions(0)
        self.assertEqual(base, GNOMON_BASE_MM)
        self.assertEqual(height, 0.0)
        self.assertEqual(hypotenuse, GNOMON_BASE_MM)

    def test_gnomon_hemisphere_symmetry(self) -> None:
        self.assertEqual(gnomon_dimensions(-31.2), gnomon_dimensions(31.2))

    def test_gnomon_invalid_base(self) -> None:
        for base in (0.0, -1.0, "60", float("nan")):
            with self.assertRaises(SundialError):
                gnomon_dimensions(31.2, base)  # type: ignore[arg-type]

    def test_format_angle(self) -> None:
        self.assertEqual(format_angle(0.0), "0.0")
        self.assertEqual(format_angle(-0.01), "0.0")
        self.assertEqual(format_angle(-90.0), "-90.0")
        self.assertEqual(format_angle(31.25), "31.2")

    def test_format_angle_invalid(self) -> None:
        for value in ("1", None, float("nan")):
            with self.assertRaises(SundialError):
                format_angle(value)  # type: ignore[arg-type]


if __name__ == "__main__":
    unittest.main()
