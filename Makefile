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
django-test: ## Run django tests (keeps existing test db).
	docker-compose exec web bash -c "python3.6 -m pytest tests/$(path) -p no:sugar"

.PHONY: django-test-create-db
django-test-create-db: ## Run django tests (recreates test db).
	docker-compose exec web bash -c "python3.6 -m pytest --create-db tests/$(path) -p no:sugar"

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

__dumpfile := market_access_$(shell date +%Y%m%d_%H%M).gz
.PHONY: pg-dump
pg-dump: ## Creates a DB backup in ./db_dumps folder.
	@echo "$$(tput setaf 3)🥟   Creating dump file ./db_dumps/$(__dumpfile)  🙈"
	@docker-compose exec db bash -c "mkdir -p /var/lib/postgresql/dumps && pg_dump -U postgres market_access | gzip > /var/lib/postgresql/dumps/$(__dumpfile)"

dumpfile =
.PHONY: restore-db
restore-db: ## Restores a DB backup
ifeq ($(dumpfile),)
	@echo "⚠️   Please use  dumpfile=<file-name>  to provide a filename from ./db_dumps"
	@echo "You may pick from the following:\n"
	@ls -1 ./db_dumps
else
	@echo "$$(tput setaf 3)🥟   Restoring DB from ./db_dumps/$(dumpfile)  🙈\n"
	@docker-compose exec db bash -c "./docker-entrypoint-initdb.d/utils/drop_db_dmas_api.sh && ./docker-entrypoint-initdb.d/utils/create_db_dmas_api.sh && ./docker-entrypoint-initdb.d/utils/restore_dump_dmas_api.sh $(dumpfile)"
endif


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
