#!/usr/bin/env python3
"""
Example usage of Smart PDF Toolkit core components.
"""

from smart_pdf_toolkit import (
    config_manager, ApplicationConfig, FileManager, 
    setup_logging, get_logger, plugin_manager
)


def main():
    """Demonstrate core functionality."""
    print("Smart PDF Toolkit - Core Components Demo")
    print("=" * 40)
    
    # 1. Configuration Management
    print("\n1. Configuration Management:")
    config = config_manager.load_config()
    print(f"   - Temp directory: {config.temp_directory}")
    print(f"   - Max file size: {config.max_file_size / (1024*1024):.1f} MB")
    print(f"   - OCR languages: {config.ocr_languages}")
    print(f"   - Log level: {config.log_level}")
    
    # 2. Logging Setup
    print("\n2. Logging Setup:")
    logger = setup_logging()
    logger.info("Logging system initialized successfully")
    print("   - Logger configured and ready")
    
    # 3. File Management
    print("\n3. File Management:")
    with FileManager() as fm:
        temp_file = fm.create_temp_file(suffix=".pdf", prefix="demo_")
        temp_dir = fm.create_temp_dir(prefix="demo_")
        print(f"   - Created temp file: {temp_file}")
        print(f"   - Created temp directory: {temp_dir}")
        print("   - Temporary files will be cleaned up automatically")
    
    # 4. Plugin System
    print("\n4. Plugin System:")
    discovered_plugins = plugin_manager.discover_plugins()
    available_plugins = plugin_manager.list_available_plugins()
    loaded_plugins = plugin_manager.list_loaded_plugins()
    
    print(f"   - Discovered plugins: {len(discovered_plugins)}")
    print(f"   - Available plugins: {len(available_plugins)}")
    print(f"   - Loaded plugins: {len(loaded_plugins)}")
    
    # 5. System Information
    print("\n5. System Information:")
    print(f"   - Configuration directory: {config_manager.config_dir}")
    print(f"   - App config file: {config_manager.app_config_file}")
    print(f"   - Plugins config file: {config_manager.plugins_config_file}")
    
    print("\n" + "=" * 40)
    print("Core components initialized successfully!")
    print("Ready for PDF processing operations.")


if __name__ == "__main__":
    main()