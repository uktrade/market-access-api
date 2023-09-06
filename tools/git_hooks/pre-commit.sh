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

container_name=web

# if the IGNORE_DOCKER environment variable is set, then we don't want to run the docker commands, so we check if it
# hasn't been defined before running
if [[ -z "${IGNORE_DOCKER}" ]]
then
  cd docker/local
  git diff --staged --name-only --diff-filter=d | grep '\.py' | xargs -t docker-compose exec -T ${container_name} black --check --exclude '/migrations/'
fi
rc=$?
if [[ ${rc} == 1 ]]
then
    echo "🙈  Black is reformatting your code!  🙊"
    git diff --staged --name-only --diff-filter=d | grep '\.py' | xargs -t docker-compose exec -T ${container_name} black --exclude '/migrations/'
    echo "🙈 You're gonna have to re add these! 🙊"
    exit 1
fi

exit 0;
