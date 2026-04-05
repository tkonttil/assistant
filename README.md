# Home Assistant Migration Tool

## 🎯 Overview

A comprehensive tool for migrating and managing Home Assistant configurations. Designed to help users migrate between different setups, apply changes safely, and track configuration history.

## 🚀 Quick Start

### Using Makefile (Recommended)

```bash
# Install dependencies and set up virtual environment
make venv-install

# Step 1: Setup - Download current state and prepare for modifications
make setup

# Step 2: Make your modifications in migration/desired/
# Edit device areas, entity configurations, etc.

# Step 3: Compute migration based on your changes
MIGRATION_NAME="my_migration" DESCRIPTION="My migration description" make compute

# Step 4: Apply changes to Home Assistant
make apply
```

### Using Python Directly

```bash
# Install dependencies
poetry install

# Run the migration workflow
python -c "
from home_assistant_migration.migration_manager_v2 import MigrationManagerV2
mm = MigrationManagerV2()

# Download current setup
mm.download_to_input()

# Create working setup
mm.create_current_from_input()

# Copy to desired and make modifications
mm.copy_current_to_desired()
# (Edit files in migration/desired/ manually)

# Compute and apply migration
mm.create_migration_data('my_migration', 'Description')
mm.apply_migrations_to_create_output()

# Deploy to container
# python scripts/deploy_output_to_docker.py
"
```

## 📁 Project Structure

```
/homeassistant-migration/
├── src/home_assistant_migration/      # Core migration system
│   ├── migration_manager_v2.py      # Main migration manager (v2)
│   ├── ssh_client.py               # SSH/Docker client
│   ├── storage.py                  # Storage management
│   └── ...                         # Supporting modules
├── scripts/                        # Utility scripts
│   ├── deploy_output_to_docker.py  # Deployment script
│   └── ...                         # Other utilities
├── deprecated/                     # Archived/old files
├── input/                          # Download from HA
├── output/                         # Processed output
└── migration/                      # Migration workflow
    ├── current/                   # Current setup
    ├── desired/                   # Desired setup
    └── migrations/                # Migration scripts
```

## 🎯 Key Features

- **Complete Migration Workflow**: Download → Modify → Deploy
- **Automatic Archiving**: Previous migrations archived automatically
- **Docker Integration**: Full container management support
- **File Preservation**: Minimal changes, maximum preservation
- **User-Friendly**: Clear separation between steps

## 🔧 Makefile Reference

The Makefile provides convenient targets for common tasks:

```bash
# Show help and available targets
make help

# Create virtual environment and install dependencies
make venv-install

# Build the package
make build

# Build wheel distribution
make wheel

# Install wheel
make install-wheel

# Clean build artifacts
make clean

# Run tests
make test

# Migration workflow targets
make setup        # Step 1: Download and prepare
make compute      # Step 2: Compute migration (requires MIGRATION_NAME and DESCRIPTION)
make apply        # Step 3: Apply migration
make migrate      # Full workflow (interactive)
```

## 📚 Usage

### Using Makefile (Recommended)

The Makefile provides a simplified three-step workflow:

#### 1. Setup - Download and Prepare
```bash
make setup
```
- Archives previous migrations
- Downloads current state from Home Assistant
- Creates working setup in `migration/current/`
- Copies to `migration/desired/` for your modifications
- Stops Docker container for safe file modifications

#### 2. Modify
Edit files in `migration/desired/` to make your changes:
- Add/remove areas, devices, entities
- Modify configuration YAML files
- Make any desired changes

#### 3. Compute Migration
```bash
MIGRATION_NAME="my_migration" DESCRIPTION="Description of changes" make compute
```
- Compares `migration/current/` vs `migration/desired/`
- Creates migration in `migration/migrations/`
- Generates output files in `output/`
- Container remains stopped

#### 4. Apply Migration
```bash
make apply
```
- Validates all files
- Uploads changes to Home Assistant
- Restarts Docker container
- Home Assistant runs with new configuration

### Using Python Directly

For more control, use the Python API directly:

```bash
# Step 1: Download
python -c "from home_assistant_migration.migration_manager_v2 import MigrationManagerV2; mm = MigrationManagerV2(); mm.download_to_input()"

# Step 2: Create working setup
python -c "from home_assistant_migration.migration_manager_v2 import MigrationManagerV2; mm = MigrationManagerV2(); mm.create_current_from_input()"

# Step 3: Copy to desired
python -c "from home_assistant_migration.migration_manager_v2 import MigrationManagerV2; mm = MigrationManagerV2(); mm.copy_current_to_desired()"

# Step 4: Make modifications (manual step)

# Step 5: Compute migration
python -c "from home_assistant_migration.migration_manager_v2 import MigrationManagerV2; mm = MigrationManagerV2(); mm.create_migration_data('name', 'description')"

# Step 6: Apply migration
python -c "from home_assistant_migration.migration_manager_v2 import MigrationManagerV2; mm = MigrationManagerV2(); mm.apply_migrations_to_create_output()"
```

## 🔧 Requirements

- Python 3.12+
- Docker (for container deployment)
- Home Assistant container running

## 📋 Best Practices

1. **Start Fresh**: Always begin with `download_to_input()`
2. **Small Changes**: Use incremental migrations
3. **Review Migrations**: Check migration JSON before deploying
4. **Backup**: Backup before major changes
5. **Test First**: Test in development before production

## 🎓 Common Workflows

### Add New Area
1. Download current setup
2. Copy to desired
3. Add area JSON to `migration/desired/areas/`
4. Compute migration
5. Apply and deploy

### Modify Configuration
1. Download current setup
2. Copy to desired
3. Edit YAML files in desired/
4. Compute migration
5. Apply and deploy

### Migrate Between Environments
1. Download from source
2. Apply transformations
3. Deploy to target

## 🚀 Quick Reference

**Download and Setup:**
```bash
python -c "from home_assistant_migration.migration_manager_v2 import MigrationManagerV2 as MM; mm=MM(); mm.download_current_setup()"
```

**Deploy Output:**
```bash
python scripts/deploy_output_to_docker.py
```

**Check Status:**
```bash
docker ps | grep homeassistant
```

## 📚 Documentation

- See `recommended_usage.py` for usage patterns
- Check `deprecated/` for older versions
- Review migration scripts for examples

## 🎉 Success!

The migration tool is ready to use. Start with a fresh Home Assistant container and follow the workflow above to manage your configurations safely and efficiently!
