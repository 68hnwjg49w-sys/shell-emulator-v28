"""Разбор путей VFS."""

PARENT = ".."
CURRENT = "."
HOME = "~"
SEPARATOR = "/"


def resolve(cwd, text):
    """Приводит путь к списку имён от корня VFS.

    Корень VFS играет роль домашнего каталога: «/» и «~» ведут в него.
    Элементы «.» и «..» обрабатываются как в UNIX.
    """
    home = text == HOME or text.startswith(HOME + SEPARATOR)
    if home:
        text = text[1:]
    parts = [] if home or text.startswith(SEPARATOR) else list(cwd)
    for item in text.split(SEPARATOR):
        if item == PARENT:
            if parts:
                parts.pop()
        elif item not in ("", CURRENT):
            parts.append(item)
    return parts
