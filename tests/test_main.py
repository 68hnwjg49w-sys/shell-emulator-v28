"""Модульные тесты точки входа."""

import io
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

from src.main import EXIT_CONFIG_ERROR, EXIT_OK, main, make_prompt
from src.shell import Shell
from src.vfs import Vfs, VfsDir


class MainTest(unittest.TestCase):
    """Проверяет запуск эмулятора с параметрами."""

    def setUp(self):
        """Создаёт временный каталог со стартовым скриптом."""
        self._tmp = tempfile.TemporaryDirectory()
        self.script = Path(self._tmp.name) / "start.txt"
        self.script.write_text("cal 2 2024\nexit\n", encoding="utf-8")

    def tearDown(self):
        """Удаляет временный каталог."""
        self._tmp.cleanup()

    def _main(self, argv):
        """Запускает main и возвращает код, вывод и ошибки."""
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            code = main(argv)
        return code, out.getvalue(), err.getvalue()

    def test_debug_output_and_script(self):
        """Параметры выводятся при запуске, затем выполняется скрипт."""
        code, out, _ = self._main(["--script", str(self.script)])
        self.assertEqual(code, EXIT_OK)
        self.assertIn("[debug]   vfs = (не задан)", out)
        self.assertIn("[debug]   script = " + str(self.script), out)
        self.assertIn("February 2024", out)

    def test_vfs_motd_is_printed(self):
        """При запуске выводится сводка по VFS и текст motd."""
        vfs = Path(self._tmp.name) / "vfs"
        vfs.mkdir()
        (vfs / "motd").write_text("Привет из VFS\n", encoding="utf-8")
        code, out, _ = self._main(["--vfs", str(vfs),
                                   "--script", str(self.script)])
        self.assertEqual(code, EXIT_OK)
        self.assertIn("VFS в памяти: каталогов 0, файлов 1", out)
        self.assertIn("Привет из VFS", out)

    def test_missing_vfs(self):
        """Отсутствующая VFS — ошибка запуска с кодом 1."""
        code, _, err = self._main(["--vfs", "no/such/vfs"])
        self.assertEqual(code, EXIT_CONFIG_ERROR)
        self.assertIn("VFS не найдена", err)

    def test_missing_script(self):
        """Отсутствующий скрипт — ошибка запуска с кодом 1."""
        code, out, err = self._main(["--script", "no/such.txt"])
        self.assertEqual(code, EXIT_CONFIG_ERROR)
        self.assertIn("[debug]", out)
        self.assertIn("ошибка запуска", err)


class PromptTest(unittest.TestCase):
    """Проверяет приглашение с текущим каталогом."""

    def test_prompt_follows_directory(self):
        """После cd в приглашении появляется путь внутри VFS."""
        shell = Shell(Vfs(VfsDir({"home": VfsDir()})))
        prompt = make_prompt(shell)
        self.assertTrue(prompt().endswith(":~$ "))
        shell.execute("cd home")
        self.assertTrue(prompt().endswith(":~/home$ "))


if __name__ == "__main__":
    unittest.main()
