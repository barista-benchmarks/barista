#!/usr/bin/env bash
set -euo pipefail

CONTAINER_NAME="oracle-free"
IMAGE_DEFAULT="container-registry.oracle.com/database/free:latest"
IMAGE="$IMAGE_DEFAULT"
HOST_PORT=1521
ORACLE_PASSWORD="mypassword"
APP_USER="appuser"
APP_USER_PASSWORD="mypassword"
READINESS_PATTERN="DATABASE IS READY TO USE!"
POLL_INTERVAL=5
TIMEOUT_SEC=900 # 15 minutes max wait

log() { echo "[setup_oracle_free] $*"; }

require_cmd() {
  command -v "$1" >/dev/null 2>&1 || { echo "Error: required command '$1' not found" >&2; exit 1; }
}

# Parse options and engine (engine can appear anywhere)
ENGINE=""
while [[ $# -gt 0 ]]; do
  case "$1" in
    --image)
      if [[ -z "${2:-}" ]]; then
        echo "Error: --image requires a value" >&2
        echo "Usage: $0 <docker|podman> [--image <image>]" >&2
        exit 2
      fi
      IMAGE="$2"
      shift 2
      ;;
    docker|podman)
      if [[ -n "$ENGINE" ]]; then
        echo "Error: container engine specified multiple times" >&2
        echo "Usage: $0 <docker|podman> [--image <image>]" >&2
        exit 2
      fi
      ENGINE="$1"
      shift
      ;;
    --)
      shift
      break
      ;;
    -* )
      echo "Unknown option: $1" >&2
      echo "Usage: $0 <docker|podman> [--image <image>]" >&2
      exit 2
      ;;
    * )
      echo "Unknown argument: $1" >&2
      echo "Usage: $0 <docker|podman> [--image <image>]" >&2
      exit 2
      ;;
  esac
done

if [[ -z "$ENGINE" ]]; then
  echo "Usage: $0 <docker|podman> [--image <image>]" >&2
  exit 2
fi

require_cmd "$ENGINE"

# Stop and remove existing container if present
if "$ENGINE" ps -a --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
  log "Stopping existing container ${CONTAINER_NAME} (if running)"
  "$ENGINE" rm -f "${CONTAINER_NAME}" >/dev/null 2>&1 || true
fi

log "Starting Oracle Free container '${CONTAINER_NAME}' on port ${HOST_PORT}"
"$ENGINE" run -d \
  -p ${HOST_PORT}:1521 \
  --name "${CONTAINER_NAME}" \
  -e ORACLE_PASSWORD="${ORACLE_PASSWORD}" \
  -e APP_USER="${APP_USER}" \
  -e APP_USER_PASSWORD="${APP_USER_PASSWORD}" \
  "${IMAGE}"

# Wait for readiness banner in logs
log "Waiting for database to be ready (pattern: '${READINESS_PATTERN}')"
start_ts=$(date +%s)
while true; do
  if "$ENGINE" logs "${CONTAINER_NAME}" 2>&1 | grep -q "${READINESS_PATTERN}"; then
    log "Database is ready."
    break
  fi
  now_ts=$(date +%s)
  elapsed=$(( now_ts - start_ts ))
  if (( elapsed > TIMEOUT_SEC )); then
    echo "Error: Timeout waiting for Oracle to become ready after ${TIMEOUT_SEC}s" >&2
    exit 1
  fi
  sleep "${POLL_INTERVAL}"
  log "Still waiting... (${elapsed}s elapsed)"
done

# Run SQL as SYSDBA inside the container to provision PETCLINIC user
log "Provisioning PETCLINIC schema inside container"
"$ENGINE" exec -i "${CONTAINER_NAME}" bash -lc "sqlplus -s / as sysdba <<'SQL'
SET HEADING OFF FEEDBACK OFF VERIFY OFF ECHO OFF PAGESIZE 0
WHENEVER SQLERROR EXIT SQL.SQLCODE
ALTER SESSION SET CONTAINER=FREEPDB1;
-- Create PETCLINIC user and grants
CREATE USER petclinic IDENTIFIED BY petclinic;
GRANT CREATE SESSION TO petclinic;
GRANT CREATE TABLE, CREATE SEQUENCE, CREATE VIEW, CREATE TRIGGER TO petclinic;
ALTER USER petclinic QUOTA UNLIMITED ON USERS;
EXIT;
SQL"

log "Done. Oracle is running in container '${CONTAINER_NAME}' and PETCLINIC schema is provisioned."
