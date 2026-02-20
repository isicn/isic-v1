# ========================================
# ISIC Odoo 19 - Dockerfile
# ========================================
# Based on official Odoo 19 image + custom addons

FROM odoo:19.0

LABEL maintainer="ISIC Rabat <isicnumerique@gmail.com>"
LABEL description="Odoo 19 - ISIC Academic Management System"
LABEL version="19.0.1.0.0"

USER root

# Install additional system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    # LDAP support
    libldap2-dev \
    libsasl2-dev \
    # Log rotation
    logrotate \
    # Utilities
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install additional Python packages
COPY requirements.txt /tmp/requirements.txt
RUN pip3 install --no-cache-dir --break-system-packages -r /tmp/requirements.txt && rm /tmp/requirements.txt

# Copy custom addons
COPY custom-addons /mnt/extra-addons

# Copy logrotate configuration
COPY docker/logrotate/odoo.conf /etc/logrotate.d/odoo

# Ensure odoo user owns config and data directories
RUN chown -R odoo:odoo /etc/odoo /var/lib/odoo /mnt/extra-addons

# Copy entrypoint script
COPY docker/entrypoint.sh /entrypoint-isic.sh
RUN chmod +x /entrypoint-isic.sh

# Switch back to odoo user
USER odoo

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8069/web/health || exit 1

ENTRYPOINT ["/entrypoint-isic.sh"]
CMD ["odoo"]
