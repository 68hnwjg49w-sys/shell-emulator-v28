"""Размеры в удобном для чтения виде."""

BLOCK = 1024
UNITS = ("B", "K", "M", "G")


def human(size, byte_unit="B"):
    """Размер в удобном виде: 512B, 1.5K, 2.0M; byte_unit — для байтов."""
    value = float(size)
    for unit in UNITS[:-1]:
        if value < BLOCK:
            return _short(value, unit, byte_unit)
        value /= BLOCK
    return _short(value, UNITS[-1], byte_unit)


def _short(value, unit, byte_unit):
    """Подписывает число единицей измерения."""
    if unit == UNITS[0]:
        return "{:.0f}{}".format(value, byte_unit)
    return "{:.1f}{}".format(value, unit)
