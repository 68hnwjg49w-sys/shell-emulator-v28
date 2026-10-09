"""Модульные тесты команд ls и cd."""

import unittest

from src.errors import CommandError
from src.vfs import VfsFile
from tests.helpers import make_shell


class LsTest(unittest.TestCase):
    """Проверяет команду ls."""

    def setUp(self):
        """Создаёт ядро с готовой VFS."""
        self.shell = make_shell()

    def test_root_listing(self):
        """Без аргументов выводится содержимое текущего каталога."""
        answer = self.shell.execute("ls")
        self.assertEqual(answer, "home  motd  readme.txt")

    def test_hidden_files(self):
        """Скрытые файлы видны только с опцией -a."""
        self.assertEqual(self.shell.execute("ls home"), "julia")
        answer = self.shell.execute("ls -a home")
        self.assertEqual(answer, ".  ..  .hidden  julia")

    def test_long_format(self):
        """Опция -l показывает тип и размер в байтах."""
        answer = self.shell.execute("ls -l home/julia/docs")
        self.assertEqual(answer.split("\n"), [
            "-     1500 a.txt",
            "-        2 b.txt",
        ])

    def test_long_format_marks_directories(self):
        """В подробном списке каталоги отмечены буквой d."""
        answer = self.shell.execute("ls -l home/julia")
        self.assertEqual(answer.split("\n")[1], "d        0 empty")

    def test_combined_options(self):
        """Опции можно объединять: -la."""
        answer = self.shell.execute("ls -la home")
        self.assertIn(".hidden", answer)
        self.assertTrue(answer.startswith("d "))

    def test_file_operand(self):
        """Для файла выводится его имя."""
        self.assertEqual(self.shell.execute("ls motd"), "motd")

    def test_several_operands(self):
        """Несколько путей: файлы сверху, у каталогов заголовки."""
        answer = self.shell.execute("ls motd home home/julia")
        self.assertEqual(
            answer, "motd\n\nhome:\njulia\n\nhome/julia:\ndocs  empty"
        )

    def test_relative_to_current_directory(self):
        """Пути отсчитываются от текущего каталога."""
        self.shell.execute("cd home/julia")
        self.assertEqual(self.shell.execute("ls docs"), "a.txt  b.txt")
        self.assertEqual(self.shell.execute("ls .."), "julia")

    def test_empty_directory(self):
        """Пустой каталог даёт пустой ответ."""
        self.assertEqual(self.shell.execute("ls home/julia/empty"), "")

    def test_human_readable_sizes(self):
        """Опция -h с -l показывает размер с единицей измерения."""
        self.shell.vfs.put(["big"], VfsFile(b"0" * 1536))
        self.assertEqual(self.shell.execute("ls -lh big"),
                         "-     1.5K big")
        self.assertEqual(self.shell.execute("ls -lh motd"),
                         "-        2 motd")

    def test_human_option_without_long_format(self):
        """Без -l опция -h ни на что не влияет."""
        self.assertEqual(self.shell.execute("ls -h"),
                         self.shell.execute("ls"))

    def test_option_combinations(self):
        """Ключи -l -h -a можно писать вместе, врозь и в любом порядке."""
        same = self.shell.execute("ls -l -h -a home")
        for line in ("ls -lha home", "ls -hal home", "ls -alh home",
                     "ls -l -ha home", "ls -a -l -h home"):
            self.assertEqual(self.shell.execute(line), same)
        self.assertIn(".hidden", same)

    def test_all_documented_forms(self):
        """Все формы вызова из задания работают."""
        for line in ("ls -l -h -a", "ls -lhq", "ls -hal", "ls -lh",
                     "ls -la"):
            self.assertIn("home", self.shell.execute(line))

    def test_quiet_option(self):
        """Опция -q заменяет непечатные символы в именах на «?»."""
        self.shell.vfs.put(["a\tb"], VfsFile(b""))
        self.assertIn("a\tb", self.shell.execute("ls"))
        self.assertIn("a?b", self.shell.execute("ls -q"))
        self.assertIn("a?b", self.shell.execute("ls -lhq"))

    def test_missing_path(self):
        """Несуществующий путь — ошибка."""
        with self.assertRaisesRegex(CommandError, "Нет такого файла"):
            self.shell.execute("ls nope")

    def test_unknown_option(self):
        """Неизвестная опция — ошибка."""
        with self.assertRaisesRegex(CommandError, "неизвестная опция"):
            self.shell.execute("ls -z")
        with self.assertRaisesRegex(CommandError, "неизвестная опция"):
            self.shell.execute("ls --all")

    def test_double_dash_ends_options(self):
        """После -- аргументы считаются путями."""
        with self.assertRaisesRegex(CommandError, "'-l'"):
            self.shell.execute("ls -- -l")


class CdTest(unittest.TestCase):
    """Проверяет команду cd и текущий каталог."""

    def setUp(self):
        """Создаёт ядро с готовой VFS."""
        self.shell = make_shell()

    def test_enter_and_leave(self):
        """Команда cd входит в каталог, cd .. возвращает на уровень выше."""
        self.shell.execute("cd home/julia")
        self.assertEqual(self.shell.cwd_label(), "~/home/julia")
        self.shell.execute("cd ..")
        self.assertEqual(self.shell.cwd_label(), "~/home")

    def test_without_argument_goes_home(self):
        """Команда cd без аргумента возвращает в корень VFS."""
        self.shell.execute("cd home/julia")
        self.shell.execute("cd")
        self.assertEqual(self.shell.cwd_label(), "~")

    def test_absolute_and_home_paths(self):
        """Пути с / и ~ отсчитываются от корня VFS."""
        self.shell.execute("cd /home/julia/docs")
        self.assertEqual(self.shell.cwd_label(), "~/home/julia/docs")
        self.shell.execute("cd ~/home")
        self.assertEqual(self.shell.cwd_label(), "~/home")
        self.shell.execute("cd /")
        self.assertEqual(self.shell.cwd_label(), "~")

    def test_parent_of_root_is_root(self):
        """Выше корня подняться нельзя."""
        self.shell.execute("cd ../..")
        self.assertEqual(self.shell.cwd_label(), "~")

    def test_dot_and_repeated_slashes(self):
        """Элементы . и лишние / не влияют на путь."""
        self.shell.execute("cd ./home//julia/./docs")
        self.assertEqual(self.shell.cwd_label(), "~/home/julia/docs")

    def test_missing_directory(self):
        """Несуществующий каталог — ошибка, каталог не меняется."""
        with self.assertRaisesRegex(CommandError, "Нет такого файла"):
            self.shell.execute("cd nope")
        self.assertEqual(self.shell.cwd_label(), "~")

    def test_file_is_not_directory(self):
        """Переход в файл — ошибка."""
        with self.assertRaisesRegex(CommandError, "Не является каталогом"):
            self.shell.execute("cd motd")

    def test_too_many_arguments(self):
        """Больше одного аргумента — ошибка."""
        with self.assertRaisesRegex(CommandError, "слишком много"):
            self.shell.execute("cd a b")


if __name__ == "__main__":
    unittest.main()
