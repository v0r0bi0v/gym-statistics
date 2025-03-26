#!/bin/bash

# Переходим в директорию проекта
cd ~/projects/gym-statistics || exit

# Функция для запуска бота
start_bot() {
    # Проверяем, не запущен ли уже бот
    if pgrep -f "python3 main.py" > /dev/null; then
        echo "Бот уже запущен."
    else
        # Запускаем бота в фоновом режиме с nohup
        nohup python3 main.py > bot.log 2>&1 &
        echo "Бот (main.py) запущен."
    fi
}

# Функция для запуска дашборда
start_dashboard() {
    # Проверяем, не запущен ли уже дашборд
    if pgrep -f "python3 dashboard.py" > /dev/null; then
        echo "Дашборд уже запущен."
    else
        # Запускаем дашборд в фоновом режиме с nohup
        nohup python3 dashboard.py > dashboard.log 2>&1 &
        echo "Дашборд (dashboard.py) запущен."
    fi
}

# Функция для авто-коммитов
start_autocommit() {
    # Проверяем, не запущен ли уже скрипт авто-коммитов
    if pgrep -f "autocommit.sh" > /dev/null; then
        echo "Авто-коммиты уже запущены."
    else
        # Создаем отдельный скрипт для авто-коммитов
        cat > autocommit.sh << 'EOL'
#!/bin/bash
while true; do
    # Получаем текущую дату и время с часовым поясом
    datetime=$(date '+%Y-%m-%d %H:%M:%S %Z')
    # Добавляем все изменения
    git add -A
    # Создаем коммит
    git commit -m "AUTOCOMMIT $datetime" --allow-empty
    # Пушим изменения
    git push
    # Ждем час
    sleep 3600
done
EOL
        # Делаем скрипт исполняемым
        chmod +x autocommit.sh
        # Запускаем его в фоновом режиме с nohup
        nohup ./autocommit.sh > autocommit.log 2>&1 &
        echo "Авто-коммиты запущены."
    fi
}

# Останавливаем все процессы
stop_all() {
    pkill -f "python3 main.py"
    pkill -f "python3 dashboard.py"
    pkill -f "autocommit.sh"
    echo "Все процессы остановлены."
}

# Проверяем аргументы командной строки
case "$1" in
    start)
        start_bot
        start_dashboard
        start_autocommit
        ;;
    stop)
        stop_all
        ;;
    *)
        echo "Использование: $0 {start|stop}"
        exit 1
        ;;
esac

exit 0
