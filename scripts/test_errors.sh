#!/bin/sh
# Проверка обработки ошибок при запуске и в стартовом скрипте.
cd "$(dirname "$0")/.." || exit 1

echo
echo "1. Ошибка в стартовом скрипте: выполнение останавливается:"
./run.sh --script examples/start_error.txt < /dev/null
echo "код завершения: $?"

echo
echo "2. Стартовый скрипт не существует:"
./run.sh --script examples/no_such_script.txt < /dev/null
echo "код завершения: $?"

echo
echo "3. Вместо файла скрипта указан каталог:"
./run.sh --script examples < /dev/null
echo "код завершения: $?"

echo
echo "4. Пустой путь к скрипту:"
./run.sh --script "" < /dev/null
echo "код завершения: $?"

echo
echo "5. Неизвестный параметр:"
./run.sh --wat < /dev/null
echo "код завершения: $?"

echo
echo "6. VFS не существует:"
./run.sh --vfs vfs/no_such_vfs < /dev/null
echo "код завершения: $?"

echo
echo "7. Вместо каталога VFS указан файл:"
./run.sh --vfs README.md < /dev/null
echo "код завершения: $?"

echo
echo "8. Пустой путь к VFS:"
./run.sh --vfs "" < /dev/null
echo "код завершения: $?"
