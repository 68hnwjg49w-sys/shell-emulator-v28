#!/bin/sh
# Проверка обработки ошибок при запуске и в стартовом скрипте.
cd "$(dirname "$0")/.." || exit 1

echo "=== 1. Ошибка в стартовом скрипте: выполнение останавливается ==="
./run.sh --script examples/start_error.txt < /dev/null
echo "код завершения: $?"

echo "=== 2. Стартовый скрипт не существует ==="
./run.sh --script examples/no_such_script.txt < /dev/null
echo "код завершения: $?"

echo "=== 3. Вместо файла скрипта указан каталог ==="
./run.sh --script examples < /dev/null
echo "код завершения: $?"

echo "=== 4. Пустой путь к скрипту ==="
./run.sh --script "" < /dev/null
echo "код завершения: $?"

echo "=== 5. Неизвестный параметр ==="
./run.sh --wat < /dev/null
echo "код завершения: $?"
