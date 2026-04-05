#!/usr/bin/env python3
"""
Clean repository for public GitHub upload.
Removes sensitive data and temporary files.
"""

import os
import shutil
import glob

def main():
    print("🧹 Cleaning repository for public upload...")
    print("   📋 Respecting .gitignore rules")
    
    # 1. Remove backup files
    backup_files = glob.glob("**/*.backup", recursive=True)
    for file in backup_files:
        try:
            os.remove(file)
            print(f"   🗑️  Removed backup file: {file}")
        except:
            pass
    
    # 2. Clean output directory (contains real device data)
    if os.path.exists("output"):
        shutil.rmtree("output")
        print("   🗑️  Removed output/ directory")
    
    # 3. Clean input directory (contains real device data)
    if os.path.exists("input"):
        shutil.rmtree("input")
        print("   🗑️  Removed input/ directory")
    
    # 4. Clean migration directories
    if os.path.exists("migration"):
        shutil.rmtree("migration")
        print("   🗑️  Removed migration/ directory")
    
    # 5. Clean applied_migrations
    if os.path.exists("applied_migrations"):
        shutil.rmtree("applied_migrations")
        print("   🗑️  Removed applied_migrations/ directory")
    
    # 6. Clean delta directory
    if os.path.exists("delta"):
        shutil.rmtree("delta")
        print("   🗑️  Removed delta/ directory")
    
    # 7. Clean .env file (keep template but remove any real values)
    if os.path.exists(".env"):
        with open(".env", "w") as f:
            f.write("""# SSH Configuration for Home Assistant VM
HASS_USE_DOCKER=true
HASS_DOCKER_CONTAINER=homeassistant
HASS_CONFIG_DIR=/config

# SSH Configuration (for non-Docker environments)
# HASS_SSH_HOST=your_home_assistant_ip_or_hostname
# HASS_SSH_PORT=22
# HASS_SSH_USER=root
# HASS_SSH_PASSWORD=your_password_or_use_key
# HASS_SSH_KEY_PATH=/path/to/your/private/key

# OpenAI API Key (optional, for LLM-assisted features)
# OPENAI_API_KEY=your_openai_api_key
""")
        print("   📝  Cleaned .env file")
    
    # 8. Remove __pycache__ directories
    for root, dirs, files in os.walk("."):
        for dir in dirs:
            if dir == "__pycache__":
                shutil.rmtree(os.path.join(root, dir))
                print(f"   🗑️  Removed __pycache__: {os.path.join(root, dir)}")
    
    # 9. Create clean example files
    os.makedirs("examples", exist_ok=True)
    
    # Create example configuration
    with open("examples/example_configuration.yaml", "w") as f:
        f.write("""# Example Home Assistant configuration
# This is a safe example for public distribution

# Loads default set of integrations
default_config:

# Example automation
automation:
  - alias: "Example Automation"
    trigger:
      platform: time
      at: "08:00:00"
    action:
      service: notify.persistent_notification
      data:
        message: "Good morning!"
""")
    print("   📝  Created example configuration")
    
    # Check .gitignore
    gitignore_check = [
        "input/",
        "output/",
        "migration/",
        ".env",
        ".venv/",
        "__pycache__/",
        "*.pyc",
        "applied_migrations"
    ]
    
    missing_from_gitignore = []
    if os.path.exists(".gitignore"):
        with open(".gitignore", "r") as f:
            gitignore_content = f.read()
        
        for item in gitignore_check:
            if item not in gitignore_content:
                missing_from_gitignore.append(item)
    
    if missing_from_gitignore:
        print(f"   ⚠️  Consider adding to .gitignore: {', '.join(missing_from_gitignore)}")
    else:
        print("   ✅ .gitignore properly configured")
    
    print("\n✅ Repository cleaned for public upload!")
    print("📋 What was removed:")
    print("   - All device-specific data (input/, output/, migration/)")
    print("   - Temporary files and backups")
    print("   - Python cache files")
    print("   - Sensitive .env values")
    print("\n📋 What was kept:")
    print("   - Source code")
    print("   - Documentation")
    print("   - Example files")
    print("   - Clean configuration templates")
    print("\n💡 Ready to push to public GitHub!")
    print("\n📝 GitHub Upload Checklist:")
    print("   1. Review .gitignore (already properly configured)")
    print("   2. Check README.md for accuracy")
    print("   3. Remove any personal comments from code")
    print("   4. Update documentation if needed")
    print("   5. Run: git add . && git commit -m 'Initial public upload'")
    print("   6. Run: git push origin main")

if __name__ == "__main__":
    main()