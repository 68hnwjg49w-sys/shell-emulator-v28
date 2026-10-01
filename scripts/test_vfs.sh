#!/bin/sh
# Проверка работы с разными VFS: загрузка в память, motd, vfs-save.
# Каждая VFS сохраняется командой vfs-save в каталог out/,
# затем сохранённая копия сравнивается с исходным каталогом.
cd "$(dirname "$0")/.." || exit 1
rm -rf out
mkdir -p out

for name in minimal flat deep; do
    echo
    echo "VFS vfs/$name:"
    printf 'vfs-save out/%s\n' "$name" > "out/save_$name.txt"
    ./run.sh --vfs "vfs/$name" --script "out/save_$name.txt" < /dev/null
    echo "Сохранённая копия:"
    find "out/$name" | sort
    if diff -r "vfs/$name" "out/$name" > /dev/null; then
        echo "копия совпадает с исходной VFS"
    else
        echo "ОШИБКА: копия отличается от исходной VFS"
    fi
done

echo
echo "Все команды этапов 1-3 со стартовым скриптом:"
./run.sh --vfs vfs/deep --script examples/start_vfs.txt < /dev/null
