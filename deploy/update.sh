#!/usr/bin/env bash
set -euo pipefail

CMD="${1:-}"

case "$CMD" in
  up)
    docker compose -f ./docker-compose.yml up -d ;;
  down)
    docker compose -f ./docker-compose.yml down ;;
  build)
    docker compose -f ./docker-compose.yml build --no-cache ;;

  app-up)
    docker compose -f ./docker-compose.yml up -d app ;;
  app-down)
    docker compose -f ./docker-compose.yml stop app ;;
  app-build)
    docker compose -f ./docker-compose.yml build --no-cache app ;;

  worker-up)
    docker compose -f ./docker-compose.yml up -d worker ;;
  worker-down)
    docker compose -f ./docker-compose.yml stop worker ;;
  worker-build)
    docker compose -f ./docker-compose.yml build --no-cache worker ;;

  logs)
    docker compose -f ./docker-compose.yml logs -f ;;
  ps)
    docker compose -f ./docker-compose.yml ps ;;

  *)
    echo "Usage: $0 <command>"
    echo ""
    echo "  up / down / build                       all services"
    echo "  app-up / app-down / app-build           app only"
    echo "  worker-up / worker-down / worker-build  worker only (GPU)"
    echo "  logs                                    follow all logs"
    echo "  ps                                      container status"
    exit 1 ;;
esac
