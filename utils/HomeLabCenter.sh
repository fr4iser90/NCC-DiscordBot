#!/usr/bin/env bash

# =======================================================
# HomeLab Discord Bot - Central Management Interface
# =======================================================

# Move to project root directory regardless of where script is called from
cd "$(dirname "${BASH_SOURCE[0]}")/.." || exit 1

# Apply permissions to all scripts first 
echo "Setting executable permissions for all utility scripts..."
find utils -name "*.sh" -type f -exec chmod +x {} \;
find utils -name "*.py" -type f -exec chmod +x {} \;
echo "Permissions set successfully."

# Global Variables
export RUN_LOCALLY=false

# Source common utilities and configuration
source "./utils/config/config.sh"
source "./utils/lib/common.sh"

# Source UI modules
source "./utils/ui/display_functions.sh"
source "./utils/ui/input_functions.sh"

# Source function modules
source "./utils/functions/deployment_functions.sh"
source "./utils/functions/container_functions.sh"
source "./utils/functions/database_functions.sh"
source "./utils/functions/testing_functions.sh"
source "./utils/functions/development_functions.sh"
source "./utils/functions/log_functions.sh"

# Source menu modules
source "./utils/menus/main_menu.sh"
source "./utils/menus/deployment_menu.sh"
source "./utils/menus/container_menu.sh"
source "./utils/menus/database_menu.sh"
source "./utils/menus/testing_menu.sh"
source "./utils/menus/development_menu.sh"
source "./utils/menus/logs_menu.sh"
source "./utils/menus/env_files_menu.sh"

# ------------------------------------------------------
# Main function
# ------------------------------------------------------
main() {
    # Validate configuration first
    validate_config
    
    # Ensure directories exist on remote server
    if [ "$RUN_LOCALLY" = false ]; then
        echo "Checking remote directories..."
        if check_ssh_connection; then
            # Check project directory and create if needed
            if ! ssh -p "${SERVER_PORT}" "${SERVER_USER}@${SERVER_HOST}" "test -d ${PROJECT_ROOT_DIR}" > /dev/null 2>&1; then
                echo -e "${YELLOW}Project directory not found: ${PROJECT_ROOT_DIR}${NC}"
                if get_yes_no "Would you like to create the directory structure?"; then
                    ssh -p "${SERVER_PORT}" "${SERVER_USER}@${SERVER_HOST}" "mkdir -p ${PROJECT_ROOT_DIR}/{docker,app,web,backups}"
                    echo -e "${GREEN}Directory structure created.${NC}"
                fi
            fi
            
            # Check Docker directory and create if needed
            if ! ssh -p "${SERVER_PORT}" "${SERVER_USER}@${SERVER_HOST}" "test -d ${DOCKER_DIR}" > /dev/null 2>&1; then
                echo -e "${YELLOW}Docker directory not found: ${DOCKER_DIR}${NC}"
                if get_yes_no "Would you like to create the Docker directory?"; then
                    ssh -p "${SERVER_PORT}" "${SERVER_USER}@${SERVER_HOST}" "mkdir -p ${DOCKER_DIR}"
                    echo -e "${GREEN}Docker directory created.${NC}"
                fi
            fi
        fi
    fi
    
    # Display main menu
    show_main_menu
}

# Run the main function
main
