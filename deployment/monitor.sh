#!/bin/bash

# ============================================
# MAYA SOC ENTERPRISE - MONITORING SCRIPT
# ============================================
# Real-time monitoring of services
# Usage: ./monitor.sh

PROJECT_DIR="/root/maya-mvp"
DB_USER="${POSTGRES_USER:-soc_user}"
DB_NAME="${POSTGRES_DB:-maya_soc}"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

clear_screen() {
    clear
}

show_header() {
    echo -e "${BLUE}╔════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║${NC}  MAYA SOC ENTERPRISE - SYSTEM MONITOR                        ${BLUE}║${NC}"
    echo -e "${BLUE}║${NC}  $(date '+%Y-%m-%d %H:%M:%S')                                      ${BLUE}║${NC}"
    echo -e "${BLUE}╚════════════════════════════════════════════════════════════════╝${NC}"
    echo ""
}

check_service_health() {
    local service=$1
    local port=$2
    
    if docker compose -f "$PROJECT_DIR/docker-compose.yml" ps "$service" | grep -q "Up"; then
        echo -e "${GREEN}✓${NC} $service (port $port)"
        return 0
    else
        echo -e "${RED}✗${NC} $service (port $port) - NOT RUNNING"
        return 1
    fi
}

show_services_status() {
    echo -e "${BLUE}━━━ SERVICES STATUS ━━━${NC}"
    cd "$PROJECT_DIR"
    
    docker compose ps --format "table {{.Names}}\t{{.Status}}" | while read name status; do
        if [[ "$name" != "NAME" ]]; then
            if echo "$status" | grep -q "Up"; then
                echo -e "${GREEN}✓${NC} $name ($status)"
            else
                echo -e "${RED}✗${NC} $name ($status)"
            fi
        fi
    done
    echo ""
}

show_resource_usage() {
    echo -e "${BLUE}━━━ RESOURCE USAGE ━━━${NC}"
    cd "$PROJECT_DIR"
    
    docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}" | \
    awk 'NR>1 {printf "%-20s CPU: %-8s Memory: %s\n", $1, $2, $3}'
    echo ""
}

show_disk_space() {
    echo -e "${BLUE}━━━ DISK SPACE ━━━${NC}"
    
    root_usage=$(df / | awk 'NR==2 {printf "%.1f%%", $5}')
    root_available=$(df / | awk 'NR==2 {printf "%.1fG", $4/1024/1024}')
    
    echo "Root Filesystem: $root_usage used, $root_available available"
    
    if [ -d "/root/backups" ]; then
        backup_size=$(du -sh "/root/backups" | cut -f1)
        echo "Backups: $backup_size"
    fi
    echo ""
}

show_logs_summary() {
    echo -e "${BLUE}━━━ RECENT ERRORS ━━━${NC}"
    cd "$PROJECT_DIR"
    
    error_count=$(docker compose logs --tail=100 | grep -i "error" | wc -l)
    warning_count=$(docker compose logs --tail=100 | grep -i "warning" | wc -l)
    
    echo "Errors in last 100 lines: $error_count"
    echo "Warnings in last 100 lines: $warning_count"
    
    if [ $error_count -gt 0 ]; then
        echo -e "${RED}Recent errors:${NC}"
        docker compose logs --tail=100 | grep -i "error" | tail -3
    fi
    echo ""
}

show_api_health() {
    echo -e "${BLUE}━━━ API HEALTH CHECK ━━━${NC}"
    
    if curl -s -f http://localhost:8000/health > /dev/null 2>&1; then
        echo -e "${GREEN}✓${NC} Backend API is responding"
    else
        echo -e "${RED}✗${NC} Backend API is not responding"
    fi
    
    if curl -s -f http://localhost:5173 > /dev/null 2>&1; then
        echo -e "${GREEN}✓${NC} Frontend is responding"
    else
        echo -e "${RED}✗${NC} Frontend is not responding"
    fi
    echo ""
}

show_database_stats() {
    echo -e "${BLUE}━━━ DATABASE STATS ━━━${NC}"
    cd "$PROJECT_DIR"
    
    conn_count=$(docker compose exec -T db psql -U "$DB_USER" -d "$DB_NAME" -c "SELECT count(*) FROM pg_stat_activity;" 2>/dev/null | grep -o "[0-9]\+" | head -1)
    if [ -n "$conn_count" ]; then
        echo "Active connections: $conn_count"
    fi
    
    size=$(docker compose exec -T db psql -U "$DB_USER" -d "$DB_NAME" -c "SELECT pg_size_pretty(pg_database_size('$DB_NAME'));" 2>/dev/null | grep -v "pg_size_pretty" | tr -d ' ')
    if [ -n "$size" ]; then
        echo "Database size: $size"
    fi
    echo ""
}

show_footer() {
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo "Press Ctrl+C to exit. Refreshing every 10 seconds..."
    echo ""
}

# Main monitoring loop
while true; do
    clear_screen
    show_header
    show_services_status
    show_resource_usage
    show_disk_space
    show_api_health
    show_database_stats
    show_logs_summary
    show_footer
    sleep 10
done
