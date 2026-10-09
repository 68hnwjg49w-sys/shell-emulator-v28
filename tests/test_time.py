"""Модульные тесты команд uptime и cal."""

import unittest

from src.errors import CommandError
from tests.helpers import Clock, make_shell


class UptimeTest(unittest.TestCase):
    """Проверяет команду uptime."""

    def setUp(self):
        """Создаёт ядро с управляемыми часами."""
        self.clock = Clock()
        self.shell = make_shell(self.clock)

    def test_just_started(self):
        """Сразу после запуска время работы — 0 минут."""
        self.assertEqual(
            self.shell.execute("uptime"), " 12:00:00 up 0 min, 1 user"
        )

    def test_minutes(self):
        """Меньше часа — минуты."""
        self.clock.advance(minutes=5, seconds=30)
        self.assertEqual(
            self.shell.execute("uptime"), " 12:05:30 up 5 min, 1 user"
        )

    def test_hours(self):
        """Больше часа — часы и минуты."""
        self.clock.advance(hours=2, minutes=3)
        self.assertIn("up 2:03,", self.shell.execute("uptime"))

    def test_days(self):
        """Больше суток — дни, затем часы и минуты."""
        self.clock.advance(days=1, hours=2, minutes=3)
        self.assertIn("up 1 day, 2:03,", self.shell.execute("uptime"))
        self.clock.advance(days=1)
        self.assertIn("up 2 days, 2:03,", self.shell.execute("uptime"))

    def test_rejects_arguments(self):
        """Команда uptime не принимает аргументов."""
        with self.assertRaisesRegex(CommandError, "не поддерживаются"):
            self.shell.execute("uptime -p")


class CalTest(unittest.TestCase):
    """Проверяет команду cal."""

    def setUp(self):
        """Создаёт ядро с управляемыми часами."""
        self.shell = make_shell()

    def test_current_month(self):
        """Без аргументов печатается текущий месяц."""
        answer = self.shell.execute("cal")
        self.assertEqual(answer.split("\n")[0].strip(), "October 2026")
        self.assertIn("Mo Tu We Th Fr Sa Su", answer)

    def test_month_and_year(self):
        """Команда cal МЕСЯЦ ГОД: неделя начинается с понедельника."""
        lines = self.shell.execute("cal 2 2024").split("\n")
        self.assertEqual(lines[0], "   February 2024")
        self.assertEqual(lines[1], "Mo Tu We Th Fr Sa Su")
        self.assertEqual(lines[2], "          1  2  3  4")
        self.assertEqual(lines[-1], "26 27 28 29")

    def test_whole_year(self):
        """Команда cal ГОД: печатаются все двенадцать месяцев."""
        answer = self.shell.execute("cal 2024")
        self.assertIn("2024", answer.split("\n")[0])
        for month in ("January", "June", "December"):
            self.assertIn(month, answer)

    def test_no_trailing_spaces(self):
        """В конце строк нет лишних пробелов."""
        for line in self.shell.execute("cal 2024").split("\n"):
            self.assertEqual(line, line.rstrip())

    def test_bad_month(self):
        """Месяц вне 1..12 — ошибка."""
        with self.assertRaisesRegex(CommandError, "неверный месяц"):
            self.shell.execute("cal 13 2024")

    def test_bad_year(self):
        """Год не число или вне диапазона — ошибка."""
        with self.assertRaisesRegex(CommandError, "неверный год: 'abc'"):
            self.shell.execute("cal 2 abc")
        with self.assertRaisesRegex(CommandError, "неверный год"):
            self.shell.execute("cal 0")
        with self.assertRaisesRegex(CommandError, "неверный год"):
            self.shell.execute("cal 10000")

    def test_too_many_arguments(self):
        """Больше двух аргументов — ошибка."""
        with self.assertRaisesRegex(CommandError, "слишком много"):
            self.shell.execute("cal 1 2 3")


if __name__ == "__main__":
    unittest.main()
