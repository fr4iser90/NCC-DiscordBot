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

# Check if local_config.sh exists, if not create it from example
if [ ! -f "./utils/config/local_config.sh" ]; then
    echo "No local configuration found. Creating from example..."
    if [ -f "./utils/config/local_config.example.sh" ]; then
        cp "./utils/config/local_config.example.sh" "./utils/config/local_config.sh"
        # Replace $(date) with actual date in the copied file
        sed -i "s/\$(date)/$(date)/g" "./utils/config/local_config.sh"
        echo "✅ Created local_config.sh from example."
        echo "⚠️ Please review and edit ./utils/config/local_config.sh to match your environment before proceeding."
        echo "    You can press Ctrl+C now to exit and edit the file,"
        echo "    or continue with default values."
        read -p "Press Enter to continue or Ctrl+C to exit..." response
    else
        echo "❌ Error: Could not find local_config.example.sh!"
        echo "Please create ./utils/config/local_config.sh manually before continuing."
        exit 1
    fi
fi

# Check for Docker .env file and load if it exists
if [ -f "../docker/.env" ]; then
    echo "Loading environment variables from ../docker/.env..."
    # Only export valid VAR=VALUE lines, properly handling comments
    set -a
    source <(grep -E '^[A-Za-z0-9_]+=.+' ../docker/.env | sed '/^#/d')
    set +a
fi

# Global Variables
export RUN_LOCALLY=false
export AUTO_START=true
export AUTO_BUILD=true
export REMOVE_VOLUMES=false
export SKIP_CONFIRMATION=false
export DIRECT_DEPLOY=false

# Parse command line arguments for local mode
for arg in "$@"; do
    case $arg in
        --local)
            export RUN_LOCALLY=true
            echo "Running in local mode with project directory: $LOCAL_PROJECT_DIR"
            shift
            ;;
    esac
done

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
source "./utils/menus/auto_start_menu.sh"
source "./utils/menus/watch_menu.sh"

# ------------------------------------------------------
# Main function
# ------------------------------------------------------
main() {
    # Parse command line arguments
    parse_cli_args "$@"
    
    # Validate configuration first
    validate_config
    
    # Handle direct deployment options first (bypass menus)
    if [ "$DIRECT_DEPLOY" = true ]; then
        # Skip showing any menus and run the requested deployment directly
        exit $?
    fi
    
    # Handle special execution modes
    if [ "$WATCH_CONSOLE" = true ]; then
        # Direct to deployment with monitoring
        print_info "Starting deployment with console monitoring..."
        run_deployment_with_monitoring "$WATCH_SERVICES"
        exit $?
    fi
    
    if [ "$INIT_ONLY" = true ]; then
        print_info "Running initialization only..."
        run_initial_setup
        exit $?
    fi
        
    # Display main menu
    show_main_menu
}

# Parse command line arguments
parse_cli_args() {
    for arg in "$@"; do
        case $arg in
            --auto-start)
                export AUTO_START=true
                ;;
            --no-auto-start)
                export AUTO_START=false
                ;;
            --watch-console)
                export WATCH_CONSOLE=true
                ;;
            --watch=*)
                export WATCH_SERVICES="${arg#*=}"
                export WATCH_CONSOLE=true
                ;;
            --feedback=*)
                export AUTO_START_FEEDBACK="${arg#*=}"
                ;;
            --init-only)
                export INIT_ONLY=true
                ;;
            --env-file=*)
                export ENV_FILE="${arg#*=}"
                if [ -f "$ENV_FILE" ]; then
                    echo "Loading environment variables from $ENV_FILE..."
                    # Only export valid VAR=VALUE lines, properly handling comments
                    set -a
                    source <(grep -E '^[A-Za-z0-9_]+=.+' "$ENV_FILE" | sed '/^#/d')
                    set +a
                else
                    echo "Warning: Environment file $ENV_FILE not found"
                fi
                ;;
            --quick-deploy)
                export DIRECT_DEPLOY=true
                run_quick_deploy
                ;;
            --quick-deploy-attach)
                export DIRECT_DEPLOY=true
                run_quick_deploy_attach
                ;;
            --partial-deploy)
                export DIRECT_DEPLOY=true
                run_partial_deploy
                ;;
            --full-reset)
                export DIRECT_DEPLOY=true
                if [ "$SKIP_CONFIRMATION" != "true" ]; then
                    print_error "⚠️ WARNING: This will COMPLETELY ERASE your database and all data! ⚠️"
                    if ! get_confirmed_input "Are you absolutely sure you want to DELETE ALL DATA?" "DELETE"; then
                        print_info "Full reset deployment cancelled"
                        exit 1
                    fi
                fi
                run_full_reset_deploy
                ;;
            --remove-volumes)
                export REMOVE_VOLUMES=true
                ;;
            --skip-confirmation)
                export SKIP_CONFIRMATION=true
                ;;
            --deploy-with-monitoring)
                export DIRECT_DEPLOY=true
                run_deployment_with_monitoring "all"
                ;;
            --deploy-with-auto-start)
                export DIRECT_DEPLOY=true
                run_quick_deploy_with_auto_start
                ;;
            --test-ALL)
                export DIRECT_ACTION=true
                run_tests_with_docker_container "all"
                exit $?
                ;;
            --test-unit)
                export DIRECT_ACTION=true
                run_unit_tests
                exit $?
                ;;
            --test-integration)
                export DIRECT_ACTION=true
                run_integration_tests
                exit $?
                ;;
            --test-system)
                export DIRECT_ACTION=true
                run_system_tests
                exit $?
                ;;
            --test-dashboard)
                run_dashboard_tests
                exit 0
                ;;
            --test-simple)
                run_simple_test
                exit 0
                ;;
            --test-ordered)
                export DIRECT_ACTION=true
                run_ordered_tests
                exit $?
                ;;
            --sync-results)
                export DIRECT_ACTION=true
                log_info "Synchronizing test results between directories..."
                sync_test_results
                exit 0
                ;;
            --sequential-tests)
                export DIRECT_ACTION=true
                run_sequential_tests
                exit $?
                ;;
            *)
                # Pass other arguments to the common parser
                ;;
        esac
    done
}

# Run the main function with all command line arguments
main "$@"
