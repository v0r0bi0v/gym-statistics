#!/bin/bash

# Переходим в директорию проекта
cd ~/projects/gym-statistics || exit

# Функция для запуска бота
start_bot() {
    if pgrep -f "python3 main.py --bot gym" > /dev/null; then
        echo "Gym-бот уже запущен."
    else
        nohup python3 main.py --bot gym > gym_bot.log 2>&1 &
        echo "Gym-бот запущен."
    fi
}

# Функция для запуска дашборда
start_dashboard() {
    if pgrep -f "python3 dashboard.py --bot gym" > /dev/null; then
        echo "Gym-дашборд уже запущен."
    else
        nohup python3 dashboard.py --bot gym > gym_dashboard.log 2>&1 &
        echo "Gym-дашборд запущен."
    fi
}

# Функция для авто-коммитов
start_autocommit() {
    if pgrep -f "gym_autocommit.sh" > /dev/null; then
        echo "Gym-автокоммиты уже запущены."
    else
        cat > gym_autocommit.sh << 'EOL'
#!/bin/bash
while true; do
    datetime=$(date '+%Y-%m-%d %H:%M:%S %Z')
    git pull
    git add -A
    git commit -m "GYM AUTOCOMMIT $datetime" --allow-empty
    git push
    sleep 3600
done
EOL
        chmod +x gym_autocommit.sh
        nohup ./gym_autocommit.sh > gym_autocommit.log 2>&1 &
        echo "Gym-автокоммиты запущены."
    fi
}

# Останавливаем все процессы Gym-бота
stop_all() {
    pkill -f "python3 main.py --bot gym"
    pkill -f "python3 dashboard.py --bot gym"
    pkill -f "gym_autocommit.sh"
    echo "Все процессы Gym-бота остановлены."
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
