#!/bin/bash
# ============================================
# Initialize LDAP with ISIC data + memberOf
# VPS version - uses relative paths and compose project
# ============================================
# Usage: bash init-ldap-vps.sh
# Run from: ~/isic/docker/

set -e

COMPOSE_FILE="docker-compose.auth-vps.yml"
ENV_FILE=".env.vps3"
LDAP_CONTAINER="isic-ldap-vps"
BOOTSTRAP_DIR="./ldap/bootstrap"

# Load LDAP password from env file
if [ -f "$ENV_FILE" ]; then
    source "$ENV_FILE"
else
    echo "ERROR: $ENV_FILE not found. Create it from .env.vps3.template"
    exit 1
fi

LDAP_PASS="${LDAP_ADMIN_PASSWORD}"

if [ -z "$LDAP_PASS" ] || [ "$LDAP_PASS" = "CHANGE_ME_STRONG_PASSWORD_HERE" ]; then
    echo "ERROR: LDAP_ADMIN_PASSWORD is not set or is still the default value."
    echo "Edit $ENV_FILE and set a strong password."
    exit 1
fi

echo "Waiting for LDAP to be ready..."
sleep 20

echo "=== Enabling memberOf overlay ==="
docker exec "$LDAP_CONTAINER" ldapmodify -Y EXTERNAL -H ldapi:/// -Q <<'LDIF'
dn: cn=module{0},cn=config
changetype: modify
add: olcModuleLoad
olcModuleLoad: memberof.la
LDIF

docker exec "$LDAP_CONTAINER" ldapmodify -Y EXTERNAL -H ldapi:/// -Q <<'LDIF'
dn: olcOverlay=memberof,olcDatabase={1}mdb,cn=config
changetype: add
objectClass: olcConfig
objectClass: olcMemberOf
objectClass: olcOverlayConfig
olcOverlay: memberof
olcMemberOfRefint: TRUE
olcMemberOfDangling: ignore
olcMemberOfGroupOC: groupOfNames
olcMemberOfMemberAD: member
olcMemberOfMemberOfAD: memberOf
LDIF

echo "=== Enabling refint overlay ==="
docker exec "$LDAP_CONTAINER" ldapmodify -Y EXTERNAL -H ldapi:/// -Q <<'LDIF'
dn: cn=module{0},cn=config
changetype: modify
add: olcModuleLoad
olcModuleLoad: refint.la
LDIF

docker exec "$LDAP_CONTAINER" ldapmodify -Y EXTERNAL -H ldapi:/// -Q <<'LDIF'
dn: olcOverlay=refint,olcDatabase={1}mdb,cn=config
changetype: add
objectClass: olcConfig
objectClass: olcRefintConfig
objectClass: olcOverlayConfig
olcOverlay: refint
olcRefintAttribute: memberOf member manager owner
LDIF

echo "=== Loading ISIC directory structure ==="
docker cp "${BOOTSTRAP_DIR}/01-isic-structure.ldif" "${LDAP_CONTAINER}:/tmp/01-isic-structure.ldif"

docker exec "$LDAP_CONTAINER" ldapadd -x -H ldap://localhost:389 \
  -D "cn=admin,dc=isic,dc=ac,dc=ma" -w "$LDAP_PASS" \
  -f /tmp/01-isic-structure.ldif

echo "=== Verifying users ==="
docker exec "$LDAP_CONTAINER" ldapsearch -x -H ldap://localhost:389 \
  -D "cn=admin,dc=isic,dc=ac,dc=ma" -w "$LDAP_PASS" \
  -b "ou=People,dc=isic,dc=ac,dc=ma" "(objectClass=inetOrgPerson)" uid cn | grep -E "^(dn:|uid:|cn:)"

echo "=== Verifying memberOf ==="
docker exec "$LDAP_CONTAINER" ldapsearch -x -H ldap://localhost:389 \
  -D "cn=admin,dc=isic,dc=ac,dc=ma" -w "$LDAP_PASS" \
  -b "ou=People,dc=isic,dc=ac,dc=ma" "(uid=directeur)" memberOf | grep -E "^(dn:|memberOf:)"

echo ""
echo "LDAP initialization complete!"
echo "Test connection from VPS-4:"
echo "  ldapsearch -H ldap://<VPS3_IP>:1389 -x -b 'dc=isic,dc=ac,dc=ma' -D 'cn=admin,dc=isic,dc=ac,dc=ma' -W"
