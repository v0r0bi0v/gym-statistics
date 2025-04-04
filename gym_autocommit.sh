#!/bin/bash
while true; do
    datetime=$(date '+%Y-%m-%d %H:%M:%S %Z')
    git pull
    git add -A
    git commit -m "GYM AUTOCOMMIT $datetime" --allow-empty
    git push
    sleep 3600
done
