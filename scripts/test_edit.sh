#!/bin/sh
# Проверка команд этапа 5: rmdir и cp меняют VFS только в памяти.
cd "$(dirname "$0")/.." || exit 1
rm -rf out/vfs_edit out/stage5_vfs
mkdir -p out/vfs_edit/docs out/vfs_edit/empty1 out/vfs_edit/empty2
mkdir -p out/vfs_edit/empty3 out/vfs_edit/tmp/cache
printf 'Файл motd\n' > out/vfs_edit/motd
printf 'первый файл\n' > out/vfs_edit/docs/a.txt
printf 'второй файл\n' > out/vfs_edit/docs/b.txt

echo
echo "Стартовый скрипт этапа 5:"
./run.sh --vfs out/vfs_edit --script examples/start_stage5.txt < /dev/null

echo
echo "Исходная VFS на диске не изменилась:"
find out/vfs_edit | sort

echo
echo "VFS, сохранённая после изменений в памяти:"
find out/stage5_vfs | sort

echo
echo "Ошибки команд, каждая в отдельном запуске:"
for line in "rmdir" "rmdir nope" "rmdir motd" "rmdir docs" "rmdir -p docs" \
        "cp" "cp motd" "cp nope x" "cp docs backup" "cp motd motd" \
        "cp -r docs docs/inner" "cp motd nope/x" "cp motd docs motd" \
        "cp -z motd x"; do
    echo
    printf '%s\n' "$line" > out/one_error.txt
    ./run.sh --vfs out/vfs_edit --script out/one_error.txt < /dev/null \
        | tail -n 4
done
