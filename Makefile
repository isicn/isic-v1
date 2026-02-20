# ========================================
# ISIC Odoo Project - Makefile
# ========================================

CUSTOM_ADDONS = ./custom-addons
DOCKER_COMPOSE = docker compose
MODULE ?=

GREEN = \033[0;32m
YELLOW = \033[0;33m
RED = \033[0;31m
NC = \033[0m

.PHONY: help run stop restart logs shell odoo-shell update scaffold test lint format build build-no-cache pgadmin db-backup db-restore pre-commit clean

help:
	@echo "$(GREEN)ISIC Odoo Project$(NC)"
	@echo ""
	@echo "$(YELLOW)Dev:$(NC)"
	@echo "  make run              Demarrer Odoo + PostgreSQL"
	@echo "  make stop             Arreter les conteneurs"
	@echo "  make restart          Redemarrer"
	@echo "  make logs             Voir les logs"
	@echo "  make shell            Bash dans le conteneur Odoo"
	@echo "  make odoo-shell       Console Odoo interactive"
	@echo "  make update MODULE=x  Mettre a jour un module"
	@echo "  make scaffold NAME=x  Creer un nouveau module"
	@echo ""
	@echo "$(YELLOW)Qualite:$(NC)"
	@echo "  make lint             Verifier le code (ruff)"
	@echo "  make format           Formater le code (ruff)"
	@echo "  make test MODULE=x    Tester un module"
	@echo ""
	@echo "$(YELLOW)Docker:$(NC)"
	@echo "  make build            Construire l'image"
	@echo "  make pgadmin          Demarrer pgAdmin (port 5050)"
	@echo ""
	@echo "$(YELLOW)DB:$(NC)"
	@echo "  make db-backup        Sauvegarder la base"
	@echo "  make db-restore       Restaurer la derniere sauvegarde"

run:
	$(DOCKER_COMPOSE) up -d
	@echo "$(GREEN)Odoo disponible sur http://localhost:8069$(NC)"

stop:
	$(DOCKER_COMPOSE) down

restart:
	$(DOCKER_COMPOSE) restart

logs:
	$(DOCKER_COMPOSE) logs -f

shell:
	$(DOCKER_COMPOSE) exec odoo bash

odoo-shell:
	$(DOCKER_COMPOSE) exec odoo odoo shell -d $${DB_NAME:-isic_dev}

update:
ifndef MODULE
	$(error MODULE requis. Usage: make update MODULE=mon_module)
endif
	$(DOCKER_COMPOSE) exec odoo odoo -d $${DB_NAME:-isic_dev} -u $(MODULE) --stop-after-init
	$(DOCKER_COMPOSE) restart odoo

scaffold:
ifndef NAME
	$(error NAME requis. Usage: make scaffold NAME=mon_module)
endif
	$(DOCKER_COMPOSE) exec odoo odoo scaffold $(NAME) /mnt/extra-addons
	@echo "$(GREEN)Module cree dans custom-addons/$(NAME)/$(NC)"

lint:
	ruff check $(CUSTOM_ADDONS)

format:
	ruff format $(CUSTOM_ADDONS)
	ruff check --fix $(CUSTOM_ADDONS)

test:
ifndef MODULE
	$(error MODULE requis. Usage: make test MODULE=mon_module)
endif
	$(DOCKER_COMPOSE) exec odoo odoo -d test_isic \
		--test-enable --stop-after-init -i $(MODULE) --log-level=test --no-http

build:
	$(DOCKER_COMPOSE) build

build-no-cache:
	$(DOCKER_COMPOSE) build --no-cache

pgadmin:
	$(DOCKER_COMPOSE) --profile tools up -d pgadmin
	@echo "$(GREEN)pgAdmin sur http://localhost:5050$(NC)"

db-backup:
	@mkdir -p backups
	$(DOCKER_COMPOSE) exec db pg_dump -U $${DB_USER:-odoo} $${DB_NAME:-isic_dev} | gzip > backups/isic_$$(date +%Y%m%d_%H%M%S).sql.gz
	@echo "$(GREEN)Sauvegarde creee dans backups/$(NC)"

db-restore:
	@LATEST=$$(ls -t backups/*.sql.gz 2>/dev/null | head -1) && \
	if [ -n "$$LATEST" ]; then \
		gunzip -c $$LATEST | $(DOCKER_COMPOSE) exec -T db psql -U $${DB_USER:-odoo} $${DB_NAME:-isic_dev}; \
		echo "$(GREEN)Restauration de $$LATEST terminee$(NC)"; \
	else \
		echo "$(RED)Aucune sauvegarde trouvee$(NC)"; \
	fi

pre-commit:
	pip install pre-commit
	pre-commit install

clean:
	find $(CUSTOM_ADDONS) -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find $(CUSTOM_ADDONS) -type f -name "*.pyc" -delete 2>/dev/null || true
	rm -rf .pytest_cache .ruff_cache 2>/dev/null || true
