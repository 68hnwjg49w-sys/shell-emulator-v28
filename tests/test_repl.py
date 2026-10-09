"""Модульные тесты консольного интерфейса."""

import unittest

from src.repl import Repl, build_prompt, current_host, current_user
from src.shell import Shell
from tests.helpers import make_shell

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
        console = self._run(["du -b nope", "wat", "cal 2 2024", "exit"])
        self.assertEqual(console.output[:2], [
            "du: не удаётся получить доступ к 'nope': "
            "Нет такого файла или каталога",
            "wat: команда не найдена",
        ])
        self.assertIn("February 2024", console.output[2])

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
        console = self._run([KeyboardInterrupt(), "wat", "exit"])
        self.assertIn("wat: команда не найдена", console.output)


class RunScriptTest(unittest.TestCase):
    """Проверяет выполнение стартового скрипта."""

    def setUp(self):
        """Создаёт ядро, консоль-заглушку и интерфейс."""
        self.shell = Shell()
        self.console = FakeConsole([])
        self.repl = Repl(
            self.shell, PROMPT, self.console.read, self.console.write
        )

    def test_input_and_output_are_shown(self):
        """На экране видны и команды, и ответы, как в диалоге."""
        done = self.repl.run_script([(1, "cd"), (2, "cal 2 2024")])
        self.assertTrue(done)
        self.assertEqual(self.console.output[0], PROMPT + "cd")
        self.assertEqual(self.console.output[1], PROMPT + "cal 2 2024")
        self.assertIn("February 2024", self.console.output[2])

    def test_stops_at_first_error(self):
        """Скрипт останавливается на первой ошибке."""
        commands = [(1, "ls"), (4, "wat"), (5, "cd")]
        self.assertFalse(self.repl.run_script(commands))
        self.assertEqual(self.console.output[-2:], [
            "wat: команда не найдена",
            "стартовый скрипт остановлен: ошибка в строке 4",
        ])
        self.assertNotIn(PROMPT + "cd", self.console.output)

    def test_exit_stops_script(self):
        """Команда exit завершает скрипт и работу эмулятора."""
        self.repl.run_script([(1, "exit"), (2, "ls")])
        self.assertFalse(self.shell.running)
        self.assertEqual(self.console.output, [PROMPT + "exit"])


class DynamicPromptTest(unittest.TestCase):
    """Проверяет приглашение, зависящее от текущего каталога."""

    def test_prompt_changes_after_cd(self):
        """Приглашение показывает каталог, в который перешли."""
        shell = make_shell()
        console = FakeConsole(["cd home", "cd julia", "cd", "exit"])

        def prompt():
            return build_prompt("julia", "mac", shell.cwd_label())

        Repl(shell, prompt, console.read, console.write).loop()
        self.assertEqual(console.prompts, [
            "julia@mac:~$ ",
            "julia@mac:~/home$ ",
            "julia@mac:~/home/julia$ ",
            "julia@mac:~$ ",
        ])

    def test_script_echo_uses_current_directory(self):
        """В диалоге скрипта приглашение тоже меняется."""
        shell = make_shell()
        console = FakeConsole([])

        def prompt():
            return build_prompt("julia", "mac", shell.cwd_label())

        repl = Repl(shell, prompt, console.read, console.write)
        repl.run_script([(1, "cd home"), (2, "cd julia")])
        self.assertEqual(console.output, [
            "julia@mac:~$ cd home",
            "julia@mac:~/home$ cd julia",
        ])


if __name__ == "__main__":
    unittest.main()
