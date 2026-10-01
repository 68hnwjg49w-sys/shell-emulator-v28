"""Модульные тесты консольного интерфейса."""

import unittest

from src.repl import Repl, build_prompt, current_host, current_user
from src.shell import Shell

PROMPT = "julia@mac:~$ "


class FakeConsole:
    """Консоль-заглушка: выдаёт заранее заданный ввод и копит вывод."""

    def __init__(self, lines):
        """Запоминает строки ввода; исключения выбрасываются как есть."""
        self._lines = list(lines)
        self.output = []
        self.prompts = []

    def read(self, prompt):
        """Возвращает следующую строку ввода или выбрасывает исключение."""
        self.prompts.append(prompt)
        if not self._lines:
            raise EOFError
        item = self._lines.pop(0)
        if isinstance(item, BaseException):
            raise item
        return item

    def write(self, text):
        """Запоминает выведенный текст."""
        self.output.append(text)


class PromptTest(unittest.TestCase):
    """Проверяет приглашение к вводу."""

    def test_prompt_format(self):
        """Приглашение имеет вид username@hostname:~$."""
        self.assertEqual(build_prompt("julia", "mac"), PROMPT)

    def test_real_os_data(self):
        """Имя пользователя и компьютера берутся из ОС и не пусты."""
        self.assertTrue(current_user())
        self.assertTrue(current_host())
        self.assertNotIn(".", current_host())


class ReplTest(unittest.TestCase):
    """Проверяет интерактивный цикл."""

    def _run(self, lines):
        """Запускает цикл на заданном вводе и возвращает консоль."""
        console = FakeConsole(lines)
        Repl(Shell(), PROMPT, console.read, console.write).loop()
        return console

    def test_prompt_is_shown(self):
        """Перед каждой командой выводится приглашение."""
        console = self._run(["ls", "exit"])
        self.assertEqual(console.prompts, [PROMPT, PROMPT])

    def test_answers_and_errors_are_printed(self):
        """Ответы и ошибки выводятся, цикл продолжает работу."""
        console = self._run(["ls a", "wat", "cd x", "exit"])
        self.assertEqual(console.output, [
            "ls: аргументы: a",
            "wat: команда не найдена",
            "cd: аргументы: x",
        ])

    def test_exit_stops_loop(self):
        """После exit ввод больше не читается."""
        console = self._run(["exit", "ls"])
        self.assertEqual(len(console.prompts), 1)

    def test_end_of_input_stops_loop(self):
        """Конец ввода (Ctrl+D) завершает работу, как в bash."""
        console = self._run(["ls"])
        self.assertEqual(console.output[-1], "exit")

    def test_ctrl_c_does_not_stop_loop(self):
        """Ctrl+D завершает работу, а Ctrl+C только сбрасывает строку."""
        console = self._run([KeyboardInterrupt(), "cd y", "exit"])
        self.assertIn("cd: аргументы: y", console.output)


if __name__ == "__main__":
    unittest.main()
