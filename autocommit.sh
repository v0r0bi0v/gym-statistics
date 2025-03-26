#!/bin/bash
while true; do
    # Получаем текущую дату и время с часовым поясом
    datetime=$(date '+%Y-%m-%d %H:%M:%S %Z')
    git pull
    # Добавляем все изменения
    git add -A
    # Создаем коммит
    git commit -m "AUTOCOMMIT $datetime" --allow-empty
    # Пушим изменения
    git push
    # Ждем час
    sleep 3600
done
