#!/bin/bash

# FINS PostgreSQL Database Management Script

set -e

POSTGRES_DIR="$HOME/.fins/postgres"
DATA_DIR="$POSTGRES_DIR/data"
INIT_DIR="$POSTGRES_DIR/init"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

create_directories() {
    print_status "Creating PostgreSQL directories..."
    mkdir -p "$DATA_DIR"
    mkdir -p "$INIT_DIR"
    print_success "Directories created: $POSTGRES_DIR"
}

start_db() {
    print_status "Starting PostgreSQL database..."
    docker-compose up -d postgres
    
    # Wait for database to be ready
    print_status "Waiting for database to be ready..."
    timeout=60
    counter=0
    while ! docker-compose exec -T postgres pg_isready -U fins -d fins >/dev/null 2>&1; do
        sleep 1
        counter=$((counter + 1))
        if [ $counter -ge $timeout ]; then
            print_error "Database failed to start within $timeout seconds"
            exit 1
        fi
    done
    
    print_success "PostgreSQL is ready!"
    print_status "Connection details:"
    echo "  Host: localhost"
    echo "  Port: 5432"
    echo "  Database: fins"
    echo "  User: fins"
    echo "  Password: *** (hidden)"
}

stop_db() {
    print_status "Stopping PostgreSQL database..."
    docker-compose down
    print_success "Database stopped"
}

restart_db() {
    print_status "Restarting PostgreSQL database..."
    docker-compose restart postgres
    print_success "Database restarted"
}

status_db() {
    print_status "Checking database status..."
    if docker-compose ps postgres | grep -q "Up"; then
        print_success "PostgreSQL is running"
        if docker-compose exec -T postgres pg_isready -U fins -d fins >/dev/null 2>&1; then
            print_success "Database is accepting connections"
        else
            print_warning "Database is running but not ready for connections"
        fi
    else
        print_warning "PostgreSQL is not running"
    fi
}

logs_db() {
    print_status "Showing database logs..."
    docker-compose logs postgres
}

backup_db() {
    print_status "Creating database backup..."
    backup_file="$POSTGRES_DIR/backup_$(date +%Y%m%d_%H%M%S).sql"
    docker-compose exec -T postgres pg_dump -U fins fins > "$backup_file"
    print_success "Backup created: $backup_file"
}

restore_db() {
    if [ -z "$1" ]; then
        print_error "Please specify backup file to restore"
        echo "Usage: $0 restore <backup_file>"
        exit 1
    fi
    
    backup_file="$1"
    if [ ! -f "$backup_file" ]; then
        print_error "Backup file not found: $backup_file"
        exit 1
    fi
    
    print_warning "This will overwrite the current database!"
    read -p "Are you sure? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        print_status "Restoring database from: $backup_file"
        docker-compose exec -T postgres psql -U fins -d fins -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"
        docker-compose exec -T postgres psql -U fins -d fins < "$backup_file"
        print_success "Database restored"
    else
        print_status "Restore cancelled"
    fi
}

clean_db() {
    print_warning "This will delete all database data!"
    read -p "Are you sure? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        print_status "Stopping database..."
        docker-compose down
        print_status "Removing data directory..."
        rm -rf "$DATA_DIR"
        print_success "Database data cleaned"
    else
        print_status "Clean cancelled"
    fi
}

case "$1" in
    start)
        create_directories
        start_db
        ;;
    stop)
        stop_db
        ;;
    restart)
        restart_db
        ;;
    status)
        status_db
        ;;
    logs)
        logs_db
        ;;
    backup)
        backup_db
        ;;
    restore)
        restore_db "$2"
        ;;
    clean)
        clean_db
        ;;
    *)
        echo "FINS PostgreSQL Database Management"
        echo "=================================="
        echo ""
        echo "Usage: $0 {start|stop|restart|status|logs|backup|restore|clean}"
        echo ""
        echo "Commands:"
        echo "  start   - Start the PostgreSQL database"
        echo "  stop    - Stop the PostgreSQL database"
        echo "  restart - Restart the PostgreSQL database"
        echo "  status  - Check database status"
        echo "  logs    - Show database logs"
        echo "  backup  - Create a database backup"
        echo "  restore - Restore from backup file"
        echo "  clean   - Remove all database data"
        echo ""
        echo "Data directory: $POSTGRES_DIR"
        exit 1
        ;;
esac 