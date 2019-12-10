#!/usr/bin/env bash

if [[ $(git diff --staged --name-only --diff-filter=d | grep -c '\.py') == 0 ]]
then
    echo -e "✨ no python files in commit ✨"
    exit 0
fi

echo -e "╔════════════════════╗"
echo -e "║ Pre-commit started ║"
echo -e "╠════════════════════╣"
echo -e "║ Black Format Check ║"
echo -e "╚════════════════════╝"


cd docker/local
git diff --staged --name-only --diff-filter=d | grep '\.py' | xargs -t docker-compose exec -T django black --check --exclude '/migrations/'

rc=$?
if [[ ${rc} == 1 ]]
then
    echo "🙈 Black is reformatting your code! 🙊"
    git diff --staged --name-only --diff-filter=d | grep '\.py' | xargs -t docker-compose exec -T django black --exclude '/migrations/'
    echo "🙈 You're gonna have to re add these! 🙊"
    exit 1
fi

exit 0;
