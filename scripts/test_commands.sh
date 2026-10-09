#!/bin/sh
# Проверка команд этапа 4: стартовый скрипт и отдельные ошибки.
cd "$(dirname "$0")/.." || exit 1
mkdir -p out

echo
echo "Стартовый скрипт этапа 4:"
./run.sh --vfs vfs/deep --script examples/start_stage4.txt < /dev/null

echo
echo "Ошибки команд, каждая в отдельном запуске:"
for line in "ls nope" "ls -z" "ls --all" "cd nope" "cd motd" "cd a b" \
        "du nope" "du -x" "uptime now" "cal 13 2024" "cal 2 abc" \
        "cal 1 2 3"; do
    echo
    printf '%s\n' "$line" > out/one_error.txt
    ./run.sh --vfs vfs/deep --script out/one_error.txt < /dev/null \
        | tail -n 4
done
