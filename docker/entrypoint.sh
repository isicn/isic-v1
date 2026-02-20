#!/bin/bash
# ========================================
# ISIC Odoo - Docker Entrypoint
# ========================================

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
NC='\033[0m'

log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

wait_for_postgres() {
    local host="${DB_HOST:-db}"
    local port="${DB_PORT:-5432}"
    local max_attempts=30
    local attempt=1

    log_info "Waiting for PostgreSQL at $host:$port..."

    while ! pg_isready -h "$host" -p "$port" -q; do
        if [ $attempt -ge $max_attempts ]; then
            log_error "PostgreSQL is not available after $max_attempts attempts. Exiting."
            exit 1
        fi
        log_warn "PostgreSQL not ready (attempt $attempt/$max_attempts). Retrying..."
        sleep 2
        attempt=$((attempt + 1))
    done

    log_info "PostgreSQL is ready!"
}

generate_config() {
    local config_file="/etc/odoo/odoo.conf"

    log_info "Generating Odoo configuration..."

    cat > "$config_file" << EOF
[options]
; Database
db_host = ${DB_HOST:-db}
db_port = ${DB_PORT:-5432}
db_user = ${DB_USER:-odoo}
db_password = ${DB_PASSWORD:-odoo}
db_name = ${DB_NAME:-}
db_maxconn = ${DB_MAXCONN:-64}

; Paths
$(if find /mnt/extra-addons -maxdepth 2 -name "__manifest__.py" 2>/dev/null | grep -q .; then
echo "addons_path = /mnt/extra-addons,/usr/lib/python3/dist-packages/odoo/addons"
else
echo "addons_path = /usr/lib/python3/dist-packages/odoo/addons"
fi)
data_dir = /var/lib/odoo

; Server
http_port = ${HTTP_PORT:-8069}
http_interface = ${HTTP_INTERFACE:-0.0.0.0}
gevent_port = ${LONGPOLLING_PORT:-8072}
proxy_mode = ${PROXY_MODE:-True}

; Workers
workers = ${WORKERS:-0}
max_cron_threads = ${MAX_CRON_THREADS:-1}

; Logging
log_level = ${LOG_LEVEL:-info}
log_handler = ${LOG_HANDLER:-:INFO}
logfile = ${LOG_FILE:-}

; Security
admin_passwd = ${ADMIN_PASSWD:-admin}
list_db = ${LIST_DB:-False}

; Limits
limit_memory_hard = ${LIMIT_MEMORY_HARD:-2684354560}
limit_memory_soft = ${LIMIT_MEMORY_SOFT:-2147483648}
limit_time_cpu = ${LIMIT_TIME_CPU:-60}
limit_time_real = ${LIMIT_TIME_REAL:-120}
limit_request = ${LIMIT_REQUEST:-8192}

; Email
$(if [ -n "$SMTP_SERVER" ]; then
echo "smtp_server = ${SMTP_SERVER}"
echo "smtp_port = ${SMTP_PORT:-587}"
echo "smtp_user = ${SMTP_USER}"
echo "smtp_password = ${SMTP_PASSWORD}"
echo "smtp_ssl = ${SMTP_SSL:-True}"
fi)

; Redis (session store)
$(if [ -n "$REDIS_HOST" ]; then
echo "session_store = redis"
echo "session_store_redis_host = ${REDIS_HOST}"
echo "session_store_redis_port = ${REDIS_PORT:-6379}"
echo "session_store_redis_prefix = ${REDIS_PREFIX:-odoo_session}"
fi)

; Development
$(if [ -n "$DEV_MODE" ] && [ "$DEV_MODE" != "False" ]; then
echo "dev_mode = ${DEV_MODE}"
fi)
EOF

    log_info "Configuration generated at $config_file"
}

init_database() {
    if [ -n "$DB_NAME" ] && [ "$INIT_DB" = "true" ]; then
        log_info "Initializing database: $DB_NAME"

        if PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -lqt | cut -d \| -f 1 | grep -qw "$DB_NAME"; then
            log_info "Database $DB_NAME already exists"
        else
            log_info "Creating database $DB_NAME..."
            PGPASSWORD="$DB_PASSWORD" createdb -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" "$DB_NAME"
        fi

        if [ -n "$INIT_MODULES" ]; then
            log_info "Installing modules: $INIT_MODULES"
            odoo -c /etc/odoo/odoo.conf -d "$DB_NAME" -i "$INIT_MODULES" --stop-after-init
        fi
    fi
}

update_modules() {
    if [ -n "$DB_NAME" ] && [ -n "$UPDATE_MODULES" ]; then
        log_info "Updating modules: $UPDATE_MODULES"
        odoo -c /etc/odoo/odoo.conf -d "$DB_NAME" -u "$UPDATE_MODULES" --stop-after-init
    fi
}

main() {
    case "$1" in
        odoo)
            wait_for_postgres
            generate_config
            init_database
            update_modules
            log_info "Starting Odoo..."
            exec odoo -c /etc/odoo/odoo.conf
            ;;
        odoo-shell)
            wait_for_postgres
            generate_config
            log_info "Starting Odoo shell..."
            exec odoo shell -c /etc/odoo/odoo.conf -d "${DB_NAME:-odoo}"
            ;;
        odoo-scaffold)
            shift
            exec odoo scaffold "$@"
            ;;
        *)
            exec "$@"
            ;;
    esac
}

main "$@"
