# Home Assistant Migration and Redesign Plan

## Overview
This plan outlines the design of a Poetry project to read the current Home Assistant setup using the [HomeAssistantAPI](https://github.com/GrandMoff100/HomeAssistantAPI) library and store it in a structured, easily editable format. The goal is to facilitate the redesign and migration of rooms, devices, and automations with proper naming conventions and automated assistance.

## Project Structure

```
home_assistant_migration/
├── pyproject.toml          # Poetry configuration
├── src/
│   ├── __init__.py
│   ├── main.py             # Main script to fetch and store data
│   ├── models.py           # Data models for rooms, devices, automations
│   ├── hass_client.py      # Home Assistant API client using HomeAssistantAPI
│   ├── storage.py          # File storage logic
│   ├── naming.py           # Naming conventions and suggestions
│   ├── automation_design.py # Automation design assistance
│   └── utils.py            # Utility functions
├── tests/
│   ├── __init__.py
│   └── test_models.py      # Unit tests for data models
├── config/
│   └── config.toml         # Configuration for API and storage
└── migration/
    ├── current/            # Current setup (read-only)
    │   ├── rooms/           # Current room configurations
    │   ├── devices/         # Current device configurations
    │   └── automations/      # Current automation configurations
    ├── desired/             # Desired setup (editable)
    │   ├── rooms/           # Desired room configurations
    │   ├── devices/         # Desired device configurations
    │   └── automations/      # Desired automation configurations
    └── migrations/          # Migration scripts
        ├── 001_initial_setup.toml  # Initial migration
        ├── 002_add_new_devices.toml  # Subsequent migrations
        └── ...
```

## Components

### 1. Poetry Project Setup
- **`pyproject.toml`**: Configure the Poetry project with dependencies like `HomeAssistantAPI`, `pydantic`, and `pyyaml`.
- **Dependencies**:
  - `HomeAssistantAPI`: For interacting with the Home Assistant API.
  - `pydantic`: For data validation and modeling.
  - `pyyaml`: For YAML file handling.
  - `openai` (optional): For LLM-assisted naming and automation design.

### 2. Data Models (`models.py`)
Define Pydantic models for:
- **Rooms**: Room names, IDs, and associated devices.
- **Devices**: Device names, IDs, room assignments, and capabilities.
- **Automations**: Automation names, triggers, actions, and conditions.

### 3. Home Assistant API Client (`hass_client.py`)
- Use the [HomeAssistantAPI](https://github.com/GrandMoff100/HomeAssistantAPI) library to fetch data from Home Assistant.
- Implement functions to:
  - Fetch all rooms (areas).
  - Fetch all devices.
  - Fetch all automations.
  - Fetch entity states and configurations.

### 4. Storage Logic (`storage.py`)
- **File Storage**: Store configurations in TOML files for easy editing and better compatibility with Python tools.
  - Current Setup: `migration/current/<category>/<name>.toml`
  - Desired Setup: `migration/desired/<category>/<name>.toml`
  - Migration Scripts: `migration/migrations/<timestamp>_<description>.toml`
- **Database Storage**: Use SQLite to store known states of Home Assistant configurations for tracking and comparison.
  - Database Schema: Track unique IDs, names, rooms, and other metadata for devices, rooms, and automations.
  - Migration History: Store a complete history of applied migrations, including timestamps, descriptions, and changes.
- **Migration Tracking**: Track applied migrations in the SQLite database to ensure proper sequencing and replication.
- **Migration Script Generation**: Provide tools to generate migration scripts that can modify multiple TOML files in a single migration. Each migration script should include:
  - A list of changes to apply (e.g., rename a device, add a new automation).
  - Dependencies on previous migrations.
  - Rollback instructions (optional).
- **Migration Merging**: Provide tools to merge multiple migration steps into a single migration script for replication or deployment purposes.

### 5. Naming Assistance (`naming.py`)
- Provide naming conventions and suggestions for rooms, devices, and automations.
- Use LLM (e.g., OpenAI) to generate meaningful names based on device capabilities and room contexts.

### 6. Automation Design (`automation_design.py`)
- Assist in designing new automations based on available devices and rooms.
- Use LLM to suggest automation rules and conditions.

### 7. Main Script (`main.py`)
- Orchestrate the fetching, storing, and migration of data.
- Steps:
  1. Initialize the Home Assistant API client.
  2. Fetch all rooms, devices, and automations, focusing on unique IDs for stability.
  3. Validate and structure the data using Pydantic models.
  4. Store the current setup in `migration/current` as TOML files, overwriting or deleting existing files to ensure the directory reflects the latest state from Home Assistant.
  5. Store the current state in the SQLite database for tracking and comparison, including migration history.
  6. Provide tools for designing the desired setup in `migration/desired` by editing TOML files.
  7. Compare the desired setup with the current state in the database to identify changes.
  8. Generate migration scripts to transform the current setup into the desired setup. Each script can modify multiple TOML files and should use unique IDs for reference.
  9. Apply migration scripts from `migration/migrations` in sequence.
  10. After applying migrations, re-fetch the current setup from Home Assistant to update the `current` directory and SQLite database. This ensures that the local files and database always reflect the actual state of Home Assistant.
  11. Track applied migrations in the SQLite database to ensure proper sequencing and avoid reapplying.
  12. Provide tools to merge multiple migration steps into a single migration script for replication or deployment purposes.

### 8. Configuration (`config.toml`)
- Store non-sensitive settings:
  ```toml
  [home_assistant]
  url = "http://homeassistant.local:8123"

  [storage]
  path = "./migration"  # Path for migration data
  format = "toml"       # Output format (toml, json, or csv)

  [naming]
  use_llm = true          # Use LLM for naming suggestions
  llm_model = "gpt-4"     # LLM model to use
  ```
- **Secure Credential Storage**:
  - Use environment variables or a secure secrets management tool (e.g., `python-dotenv`, `keyring`, or a dedicated secrets manager) to store sensitive credentials like `HASS_TOKEN` and LLM API keys.
  - Example `.env` file:
    ```env
    HASS_TOKEN=your_long_lived_access_token
    OPENAI_API_KEY=your_openai_api_key
    ```
  - Load credentials in your application using:
    ```python
    from dotenv import load_dotenv
    import os
    
    load_dotenv()  # Load environment variables from .env file
    hass_token = os.getenv("HASS_TOKEN")
    openai_api_key = os.getenv("OPENAI_API_KEY")
    ```

## Workflow

1. **Fetch Current Setup**: Use the [HomeAssistantAPI](https://github.com/GrandMoff100/HomeAssistantAPI) library to fetch all rooms, devices, and automations from Home Assistant, focusing on unique IDs for stability.
2. **Store Current Setup**: Save the current setup in `migration/current` as TOML files and store the state in the SQLite database for tracking and comparison. Overwrite or delete existing local files to ensure the `current` directory always reflects the latest state from Home Assistant.
3. **Design Desired Setup**: Edit the TOML files in `migration/desired` to reflect the desired setup, using unique IDs to reference devices and rooms.
4. **Compare Setups**: Use the SQLite database to compare the current and desired setups, identifying changes based on unique IDs.
5. **Generate Migration Scripts**: Automatically generate migration scripts in `migration/migrations` to transform the current setup into the desired setup. Each migration script can modify multiple TOML files and should be idempotent, using unique IDs for reference.
6. **Review Migration Scripts**: Manually review and edit the generated migration scripts to ensure correctness.
7. **Apply Migrations**: Run migration scripts in sequence to apply changes to the Home Assistant setup. After applying migrations, re-fetch the current setup from Home Assistant to update the `current` directory and SQLite database. This ensures that the local files and database always reflect the actual state of Home Assistant.
8. **Review and Edit**: Manually review and edit the desired setup files or migration scripts using a text editor or other tools.
9. **Deploy Desired Setup (Future)**: Implement a script to deploy the desired setup back to Home Assistant using the migration scripts.

## Example Output Structure

### Current Rooms (`migration/current/rooms/living_room.toml`)
```toml
id = "living_room"
name = "Living Room"
devices = ["light.living_room", "binary_sensor.motion_living_room"]
```

### Desired Rooms (`migration/desired/rooms/living_room.toml`)
```toml
id = "living_room"
name = "Living Room"
devices = ["light.living_room_main", "binary_sensor.motion_living_room_primary"]
```

### Current Devices (`migration/current/devices/light.living_room.toml`)
```toml
id = "light.living_room"
name = "Living Room Light"
room = "living_room"
model = "Philips Hue"
manufacturer = "Philips"
```

### Desired Devices (`migration/desired/devices/light.living_room_main.toml`)
```toml
id = "light.living_room_main"
name = "Living Room Main Light"
room = "living_room"
model = "Philips Hue"
manufacturer = "Philips"
```

### Current Automations (`migration/current/automations/turn_on_lights.toml`)
```toml
id = "turn_on_lights"
name = "Turn on lights when motion is detected"

[trigger]
platform = "state"
entity_id = "binary_sensor.motion_living_room"
to = "on"

action = { service = "light.turn_on", entity_id = "light.living_room" }
```

### Desired Automations (`migration/desired/automations/turn_on_living_room_lights.toml`)
```toml
id = "turn_on_living_room_lights"
name = "Turn on living room lights when motion is detected"

[trigger]
platform = "state"
entity_id = "binary_sensor.motion_living_room_primary"
to = "on"

action = { service = "light.turn_on", entity_id = "light.living_room_main" }
```

## Future Enhancements
- **Deployment Script**: Add functionality to deploy the desired setup back to Home Assistant using the [HomeAssistantAPI](https://github.com/GrandMoff100/HomeAssistantAPI) library. Include rollback procedures and environment-specific configurations.
- **Versioning**: Implement versioning for configurations to track changes over time, allowing for easy rollback and history tracking.
- **Validation**: Add validation to ensure configurations are correct before deployment, including schema validation and dependency checks.
- **UI**: Develop a simple UI for editing configurations, with features for previewing changes and managing migrations.
- **Diff Tool**: Create a tool to compare the current and desired setups and highlight differences based on unique IDs, with options for generating migration scripts.
- **Migration Method**: Implement a migration system similar to database migrations, where each migration builds on the previous state. Store migration paths to allow replication of changes from scratch.
- **Migration Script Generation**: Enhance the tool to automatically generate migration scripts based on differences between the current and desired setups, using unique IDs for reference.
- **Database Schema Enhancements**: Extend the SQLite database schema to support more complex queries and tracking of migration history, including timestamps and user metadata.
- **Migration Replication**: Add functionality to replicate migration history and apply it to a new Home Assistant instance, ensuring consistency across environments.
- **Migration Merging**: Enhance the tool to merge multiple migration steps into a single migration script for easier deployment and replication.

## Risk Management
- **API Changes**: The Home Assistant API may change over time, potentially breaking the integration. Mitigation: Use versioned API endpoints and implement fallback mechanisms.
- **Data Corruption**: Corruption in the SQLite database or YAML files could lead to data loss. Mitigation: Implement regular backups and validation checks.
- **Migration Failures**: Migrations may fail due to dependencies or conflicts. Mitigation: Include rollback procedures and thorough testing for each migration script.
- **Dependency Issues**: Dependencies (e.g., `HomeAssistantAPI`, `pydantic`) may introduce breaking changes. Mitigation: Pin dependency versions and monitor for updates.

## Testing Strategy
- **Unit Testing**: Test individual components (e.g., `hass_client.py`, `storage.py`) to ensure they function correctly in isolation.
- **Integration Testing**: Test interactions between components (e.g., fetching data from Home Assistant and storing it in the database).
- **End-to-End Testing**: Test the entire workflow, from fetching data to applying migrations, to ensure the system works as expected.
- **Regression Testing**: Ensure that new changes do not break existing functionality by running tests against previous versions of the setup.

## Deployment Strategy
- **Rollback Procedures**: Implement rollback procedures for deployments to quickly revert to a previous state in case of failures.
- **Environment-Specific Configurations**: Support different configurations for development, staging, and production environments.
- **Automated Deployments**: Use CI/CD pipelines to automate the deployment process, ensuring consistency and reducing human error.

## Documentation Plan
- **API Documentation**: Document the API endpoints and data models used in the project for developers.
- **User Guides**: Provide guides for end-users on how to use the tool, including setup, migration, and deployment instructions.
- **Developer Documentation**: Include documentation for developers on how to extend or modify the tool, including architecture diagrams and code examples.

## Conclusion
This plan provides a structured approach to reading, redesigning, and migrating Home Assistant configurations. The focus is on using unique IDs to ensure stability and reliability, while allowing for flexible renaming and reassignment of devices and rooms. The migration system tracks and applies changes incrementally, with SQLite used to store known states and track migration history. Future enhancements include deployment scripts, versioning, validation, and a UI for editing configurations.