# ==================================================
# IMPORTANT - do NOT add anything above 'help'
# It should always be the first command.
# ==================================================

.PHONY: help
help: ## This help.
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'


# DEV COMMANDS
# ==================================================
.PHONY: django-run
django-run: ## Run django's dev server (tailing).
	docker-compose exec web bash -c "python3.6 /usr/src/app/manage.py runserver 0:8000"

.PHONY: django-run-detached
django-run-detached: ## Run django's dev server (silently).
	docker-compose exec -d web bash -c "python3.6 /usr/src/app/manage.py runserver 0:8000"

.PHONY: django-shell
django-shell: ## Drop into django's shell (with iphython).
	docker-compose exec web bash -c "pip install ipython &&  python3.6 ./manage.py shell_plus"

.PHONY: django-test
django-test: ## Run django tests.
	docker-compose exec web bash -c "python3.6 -m pytest api"

.PHONY: django-tests-coverage
django-tests-coverage: ## Run django tests and generate coverage report.
	docker-compose exec web bash -c "coverage run --source='.' manage.py test"
	docker-compose exec web bash -c "coverage report"

.PHONY: celery-run
celery-run: ## Run the celery dev server.
	docker-compose exec web bash -c "celery -A config.celery worker -l info -B -E"

.PHONY: git-hooks
git-hooks: ## Set up hooks for git.
	# === Setting up pre-commit hooks ========
	docker-compose exec web bash -c "cp tools/git_hooks/pre-commit.sh .git/hooks/pre-commit && chmod +x .git/hooks/pre-commit"
# ==================================================


# MIGRATION COMMANDS
# ==================================================
.PHONY: django-makemigrations
django-makemigrations: ## Create django migrations
	docker-compose exec web bash -c "python3.6 /usr/src/app/manage.py makemigrations"

.PHONY: django-migrate
django-migrate: ## Apply django migrations.
	docker-compose exec web bash -c "python3.6 /usr/src/app/manage.py migrate"

.PHONY: django-showmigrations
django-showmigrations: ## Show django migrations.
	docker-compose exec web bash -c "python3.6 /usr/src/app/manage.py showmigrations"
# ==================================================


# UTIL COMMANDS
# ==================================================
.PHONY: pip-install
pip-install: ## Install pip requirements inside the container.
	@echo "$$(tput setaf 3)🙈  Installing Pip Packages  🙈"
	@docker-compose exec web bash -c "pip3.6 install -r requirements.txt"

.PHONY: pip-deptree
pip-deptree: ## Output pip dependecy tree.
	@echo "$$(tput setaf 0)$$(tput setab 2)  🌳  Pip Dependency Tree  🌳   $$(tput sgr 0)"
	@docker-compose exec web bash -c "pip3.6 install pipdeptree && pipdeptree -fl"


# SSH COMMANDS (to debug via ssh)
# ==================================================
.PHONY: django-debug
django-debug: ## Run the SSH server on `web` - mainly use to expose python interpreter.
	ssh-keygen -R '[api.market-access.local]:8882'
	docker-compose exec -d web bash -c "/usr/bin/ssh-keygen -A; /usr/sbin/sshd -D"

.PHONY: django-ssh
django-ssh: ## Connect to `web` over SSH.
	ssh -p8882 root@api.market-access.local -t 'cd /usr/src/app; bash -l'
# ==================================================
