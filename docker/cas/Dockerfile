# ============================================
# ISIC CAS Server - Custom Image
# ============================================
# Base sur Apereo CAS 6.6.15 avec:
#   - Support LDAP (cas-server-support-ldap)
#   - Branding ISIC (logo, CSS, JS)
#
# Strategie: Gradle telecharge les JARs LDAP,
# puis on les copie dans le WAR CAS extrait.
# ============================================

# ------------------------------------------
# Stage 1: Telecharger les JARs LDAP
# ------------------------------------------
FROM gradle:7.6-jdk11 AS builder

WORKDIR /cas-overlay
COPY overlay-build/ .
RUN gradle clean build -x test --no-daemon

# ------------------------------------------
# Stage 2: Runtime CAS + LDAP + Branding ISIC
# ------------------------------------------
FROM apereo/cas:6.6.15

USER root

# S'assurer que le repertoire de build Tomcat est accessible
RUN mkdir -p /docker/cas/war/build/tomcat && \
    chown -R 1000:1000 /docker/cas/war/build

# Copier les JARs LDAP depuis le builder
COPY --from=builder /cas-overlay/build/ldap-jars/ /tmp/ldap-jars/

# Injecter les JARs LDAP dans le WAR CAS:
# 1. Extraire le WAR original
# 2. Copier les JARs LDAP (seulement ceux pas deja presents)
# 3. Repackager le WAR avec le meme manifest
RUN cd /tmp && \
    mkdir cas-extract && cd cas-extract && \
    jar xf /docker/cas/war/cas.war && \
    for jar in /tmp/ldap-jars/*.jar; do \
        basename=$(basename "$jar"); \
        if [ ! -f "WEB-INF/lib/$basename" ]; then \
            cp "$jar" WEB-INF/lib/; \
        fi; \
    done && \
    jar cf0M /docker/cas/war/cas.war . && \
    cd /tmp && rm -rf cas-extract ldap-jars

# Creer le repertoire de surcharge statique
RUN mkdir -p /etc/cas/static/css \
             /etc/cas/static/js \
             /etc/cas/static/images

# CSS combine (CAS original + overrides ISIC)
COPY overlay/static-override/css/cas.css /etc/cas/static/css/cas.css

# JS combine (CAS original + ISIC DOM loader)
COPY overlay/static-override/js/cas.js /etc/cas/static/js/cas.js

# Logo ISIC (PNG officiel)
COPY overlay/static-override/images/isic-logo.png /etc/cas/static/images/isic-logo.png

# Configuration CAS et services
COPY config/ /etc/cas/config/
COPY services/ /etc/cas/services/

USER 1000

EXPOSE 8443

HEALTHCHECK --interval=30s --timeout=10s --retries=10 --start-period=120s \
    CMD curl -f http://localhost:8443/cas/login || exit 1
