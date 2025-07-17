"""
GUI application launcher for Smart PDF Toolkit.
"""

import sys
import os
from pathlib import Path
from typing import Optional

# Add the parent directory to the path so we can import the toolkit
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

try:
    from PyQt6.QtWidgets import QApplication, QMessageBox
    from PyQt6.QtCore import Qt
    from PyQt6.QtGui import QIcon
    PYQT_AVAILABLE = True
except ImportError:
    PYQT_AVAILABLE = False

from smart_pdf_toolkit.core.config import Config
from smart_pdf_toolkit.gui.main_window import MainWindow


def check_dependencies() -> tuple[bool, str]:
    """Check if all required dependencies are available."""
    missing_deps = []
    
    if not PYQT_AVAILABLE:
        missing_deps.append("PyQt6")
    
    if missing_deps:
        return False, f"Missing dependencies: {', '.join(missing_deps)}"
    
    return True, ""


def create_application() -> QApplication:
    """Create and configure the QApplication."""
    app = QApplication(sys.argv)
    
    # Set application properties
    app.setApplicationName("Smart PDF Toolkit")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("Smart PDF Toolkit")
    app.setOrganizationDomain("smart-pdf-toolkit.com")
    
    # Set application icon if available
    icon_path = Path(__file__).parent / "resources" / "icon.png"
    if icon_path.exists():
        app.setWindowIcon(QIcon(str(icon_path)))
    
    # Set application style
    app.setStyle("Fusion")  # Use Fusion style for consistent look
    
    return app


def show_error_dialog(title: str, message: str):
    """Show an error dialog."""
    if PYQT_AVAILABLE:
        app = QApplication(sys.argv)
        QMessageBox.critical(None, title, message)
        app.quit()
    else:
        print(f"ERROR: {title}")
        print(message)


def main(config_path: Optional[str] = None) -> int:
    """Main entry point for the GUI application."""
    
    # Check dependencies
    deps_ok, deps_msg = check_dependencies()
    if not deps_ok:
        show_error_dialog("Missing Dependencies", deps_msg)
        return 1
    
    try:
        # Create application
        app = create_application()
        
        # Load configuration
        config = Config()
        if config_path:
            config.load_from_file(config_path)
        
        # Create and show main window
        window = MainWindow(config)
        window.show()
        
        # Run application
        return app.exec()
        
    except Exception as e:
        show_error_dialog("Application Error", f"Failed to start application: {str(e)}")
        return 1


if __name__ == "__main__":
    # Parse command line arguments
    config_path = None
    if len(sys.argv) > 1:
        config_path = sys.argv[1]
    
    sys.exit(main(config_path))