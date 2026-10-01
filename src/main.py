"""Точка входа эмулятора командной оболочки."""

from src.repl import Repl, build_prompt, current_host, current_user
from src.shell import Shell


def main():
    """Запускает эмулятор в интерактивном режиме."""
    prompt = build_prompt(current_user(), current_host())
    Repl(Shell(), prompt).loop()


if __name__ == "__main__":
    main()
