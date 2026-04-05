# Agent Instructions - Home Assistant Migration Tool

## 🎯 Current Project State (April 2024)

This document describes the current state of the Home Assistant Migration Tool project after cleanup and organization.

## 📁 Project Structure

```
/homeassistant-migration/
├── src/home_assistant_migration/          # Core migration system (ACTIVE)
│   ├── __init__.py                      # Package initialization
│   ├── database.py                      # Database operations
│   ├── desired_setup.py                 # Desired setup management
│   ├── hass_client.py                   # SSH client (symlink to ssh_client.py)
│   ├── main.py                          # Main entry point
│   ├── migration_generator.py           # Migration generation
│   ├── migration_manager.py             # Original migration manager
│   ├── migration_manager_v2.py          # Enhanced migration manager (PRIMARY)
│   ├── models.py                        # Data models
│   ├── ssh_client.py                    # SSH/Docker client
│   └── storage.py                       # Storage management
├── scripts/                            # Utility scripts (ACTIVE)
│   ├── analyze_entities.py             # Entity analysis
│   ├── apply_migration.py               # Apply migrations
│   ├── check_api_component.py          # API component checks
│   ├── check_areas.py                   # Area verification
│   ├── compare_setups.py                # Setup comparison
│   ├── deploy_output_to_docker.py      # Deployment to Docker
│   ├── direct_area_test.py             # Direct area testing
│   ├── fetch_current_enhanced.py        # Enhanced fetch
│   ├── fetch_current_only.py           # Basic fetch
│   ├── fetch_current_via_ssh.py        # SSH-based fetch
│   ├── fetch_current_with_areas.py     # Fetch with areas
│   ├── fetch_final.py                  # Final fetch
│   ├── fetch_realistic.py              # Realistic fetch
│   ├── fix_setup.py                    # Setup fixes
│   ├── get_area_details.py             # Area details
│   ├── get_area_names.py               # Area names
│   ├── plan_migration.py               # Migration planning
│   ├── search_testin_room.py           # Search test room
│   └── set_desired_to_current.py       # Set desired to current
├── deprecated/                         # Archived files (INACTIVE)
│   ├── *.py                            # Old test scripts
│   ├── *.md                            # Old documentation
│   └── *.backup                        # Backup files
├── input/                              # Download from HA (TEMPORARY)
├── output/                             # Processed output (TEMPORARY)
├── migration/                          # Migration workflow (TEMPORARY)
│   ├── current/                       # Current setup
│   ├── desired/                       # Desired setup
│   └── migrations/                    # Migration scripts
├── README.md                           # Project documentation
├── AGENT_INSTRUCTIONS.md              # Agent instructions
└── recommended_usage.py               # Usage examples
```

## 🎯 Key Components

### 1. Core Migration System (`src/home_assistant_migration/`)

**Primary Component:** `migration_manager_v2.py`
- Handles complete migration workflow
- Downloads from Home Assistant
- Creates current/desired setups
- Computes and applies migrations
- Generates output for deployment

**Supporting Components:**
- `ssh_client.py`: SSH/Docker container access
- `storage.py`: Local storage management
- `models.py`: Data models and structures

### 2. Utility Scripts (`scripts/`)

**Key Scripts:**
- `deploy_output_to_docker.py`: Deploy output to Docker container
- `fetch_current_via_ssh.py`: Fetch current setup via SSH
- Other scripts: Various utility functions

### 3. Archived Files (`deprecated/`)

Old test scripts, backup files, and documentation moved here for cleanup.

## 🚀 Current Workflow

### Standard Migration Process

1. **Download Current Setup**
   ```bash
   python -c "from home_assistant_migration.migration_manager_v2 import MigrationManagerV2; mm = MigrationManagerV2(); mm.download_to_input()"
   ```

2. **Create Working Setup**
   ```bash
   python -c "from home_assistant_migration.migration_manager_v2 import MigrationManagerV2; mm = MigrationManagerV2(); mm.create_current_from_input()"
   ```

3. **Copy to Desired**
   ```bash
   python -c "from home_assistant_migration.migration_manager_v2 import MigrationManagerV2; mm = MigrationManagerV2(); mm.copy_current_to_desired()"
   ```

4. **Modify Desired Setup** (User Step)
   - Edit files in `migration/desired/`
   - Add/remove areas, devices, entities
   - Update configuration files

5. **Compute Migration**
   ```bash
   python -c "from home_assistant_migration.migration_manager_v2 import MigrationManagerV2; mm = MigrationManagerV2(); mm.create_migration_data('name', 'description')"
   ```

6. **Apply Migration**
   ```bash
   python -c "from home_assistant_migration.migration_manager_v2 import MigrationManagerV2; mm = MigrationManagerV2(); mm.apply_migrations_to_create_output()"
   ```

7. **Deploy to Container**
   ```bash
   python scripts/deploy_output_to_docker.py
   ```

### Key Features

- **Automatic Archiving**: Previous migrations archived to `applied_migrations/`
- **Docker Integration**: Full container management via SSH client
- **File Preservation**: All unchanged files preserved during migrations
- **User-Friendly**: Clear separation between automated and manual steps

## 📚 Documentation

- **README.md**: Project overview and quick start guide
- **AGENT_INSTRUCTIONS.md**: Current state and component analysis
- **recommended_usage.py**: Usage patterns and examples
- **deprecated/**: Archived documentation and scripts

## 🎯 Current Status

**✅ Working Components:**
- Core migration system (v2)
- Docker deployment script
- SSH client with Docker support
- Storage management

**📋 Organization:**
- Clean project structure
- Unnecessary files archived
- Clear documentation
- Logical separation of concerns

**🚀 Ready For:**
- Production use
- New migrations
- Testing
- Development

## 🎓 Recommendations

1. **Use Migration Manager V2**: Primary interface for all operations
2. **Follow Workflow**: Standard 7-step process for consistency
3. **Archive Old Files**: Keep deprecated/ for reference
4. **Document Changes**: Update documentation as needed
5. **Test First**: Verify in development before production

## 📈 Future Enhancements

- **Automated Testing**: Add test suite
- **CI/CD Integration**: Setup deployment pipeline
- **Enhanced Error Handling**: Better validation
- **Performance Optimization**: Faster operations
- **Additional Integrations**: More platforms

## 🎉 Success!

The project is clean, organized, and ready for production use. All components are working, documentation is updated, and the system is prepared for future development!
