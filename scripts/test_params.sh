#!/bin/sh
# Проверка параметров командной строки эмулятора.
# Ввод закрыт (< /dev/null): после стартового скрипта эмулятор
# получает конец ввода и завершается, не ожидая команд.
cd "$(dirname "$0")/.." || exit 1

echo
echo "1. Без параметров:"
./run.sh < /dev/null

echo
echo "2. Только путь к VFS:"
./run.sh --vfs vfs/deep < /dev/null

echo
echo "3. Только стартовый скрипт:"
./run.sh --script examples/start_demo.txt < /dev/null

echo
echo "4. Оба параметра:"
./run.sh --vfs vfs/deep --script examples/start_demo.txt < /dev/null
