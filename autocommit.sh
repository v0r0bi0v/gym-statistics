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
    # Ждем 5 минут
    sleep 300
done
