#!/usr/bin/env bash
# Usage: ./scripts/demo.sh <step>   (run from the CC-Assignment folder)
# Steps: test build scan secret up health failover recover release-bad rollback summary down
set -u
cd "$(dirname "$0")/.."
EV=evidence; mkdir -p $EV
URL=http://localhost:8080

case "${1:-help}" in
test)    # unit tests inside a throwaway container
  docker run --rm -v "$PWD":/w -w /w python:3.12.16-slim-bookworm \
    sh -c "pip install -q -r app/requirements.txt pytest && pytest tests -q" | tee $EV/01-unit-tests.txt ;;
build)
  docker build --build-arg APP_VERSION=1.0.0 -t campuscart-api:1.0.0 . | tee $EV/02-build-1.0.0.txt
  docker build --build-arg APP_VERSION=1.1.0 --build-arg FAIL_HEALTH=1 -t campuscart-api:1.1.0 . | tee $EV/02-build-1.1.0.txt ;;
scan)    # Trivy via container; fail on HIGH/CRITICAL
  docker run --rm -v /var/run/docker.sock:/var/run/docker.sock aquasec/trivy:latest image \
    --severity HIGH,CRITICAL --ignore-unfixed --exit-code 1 campuscart-api:1.0.0 | tee $EV/03-scan-1.0.0.txt ;;
secret)
  [ -f secrets/db_password.txt ] || { openssl rand -base64 18 | tr -d '\n' > secrets/db_password.txt; }
  chmod 644 secrets/db_password.txt  # readable by the non-root container user
  echo "secret file ready (not in image, git or .dockerignore'd)" ;;
up)
  TAG=${TAG:-1.0.0} docker compose up -d && sleep 8 && docker compose ps | tee $EV/04-compose-ps.txt ;;
health)
  { echo "# GET /health x6 via proxy"; for i in 1 2 3 4 5 6; do curl -s $URL/health; echo; done
    echo "# POST + GET /orders"; curl -s -XPOST -H 'Content-Type: application/json' -d '{"item":"Notebook","qty":2}' $URL/orders; echo
    curl -s $URL/orders; echo
    echo "# Runs as user:"; docker compose exec -T api1 id
    echo "# Secret NOT in image env/history:"; docker history --no-trunc campuscart-api:1.0.0 | grep -ci password
  } | tee $EV/05-health.txt ;;
failover)
  { docker compose stop api1; echo "api1 stopped"; for i in 1 2 3 4 5 6; do curl -s -o /dev/null -w "%{http_code} " $URL/health; done; echo
    curl -s $URL/health; echo; } | tee $EV/06-failover.txt ;;
recover) docker compose start api1 ;;
release-bad)  # deploy faulty 1.1.0, observe unhealthy
  { TAG=1.1.0 docker compose up -d api1 api2; sleep 45; docker ps --format '{{.Names}} {{.Image}} {{.Status}}'
    for i in 1 2 3; do curl -s -o /dev/null -w "%{http_code} " $URL/health; done; echo; } | tee $EV/07-bad-release.txt ;;
rollback)
  { echo "Rolling back to campuscart-api:1.0.0"; TAG=1.0.0 docker compose up -d api1 api2; sleep 45
    docker ps --format '{{.Names}} {{.Image}} {{.Status}}'
    for i in 1 2 3; do curl -s $URL/health; echo; done; } | tee $EV/08-rollback.txt ;;
summary)
  { docker images campuscart-api; docker image inspect campuscart-api:1.0.0 --format 'User={{.Config.User}} Ports={{.Config.ExposedPorts}} Size={{.Size}}'
    docker history campuscart-api:1.0.0; } | tee $EV/09-image-summary.txt ;;
down) docker compose down -v ;;
*) sed -n 2,3p "$0" ;;
esac
