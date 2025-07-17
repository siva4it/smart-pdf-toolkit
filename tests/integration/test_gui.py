"""
Unit tests for GUI components.
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

# Try to import PyQt6, skip tests if not available
try:
    from PyQt6.QtWidgets import QApplication
    from PyQt6.QtTest import QTest
    from PyQt6.QtCore import Qt
    PYQT_AVAILABLE = True
except ImportError:
    PYQT_AVAILABLE = False

from smart_pdf_toolkit.core.config import Config

if PYQT_AVAILABLE:
    from smart_pdf_toolkit.gui.main_window import MainWindow
    from smart_pdf_toolkit.gui.file_browser import FileBrowser
    from smart_pdf_toolkit.gui.operation_tabs import OperationTabs, PDFOperationsTab
    from smart_pdf_toolkit.gui.progress_dialog import ProgressDialog


@pytest.mark.skipif(not PYQT_AVAILABLE, reason="PyQt6 not available")
class TestGUIComponents:
    """Test GUI components."""
    
    @pytest.fixture(scope="class")
    def qapp(self):
        """Create QApplication for testing."""
        if not QApplication.instance():
            app = QApplication([])
        else:
            app = QApplication.instance()
        yield app
        
    @pytest.fixture
    def config(self):
        """Create test configuration."""
        return Config()
        
    @pytest.fixture
    def main_window(self, qapp, config):
        """Create main window for testing."""
        window = MainWindow(config)
        yield window
        window.close()
        
    @pytest.fixture
    def file_browser(self, qapp, config):
        """Create file browser for testing."""
        browser = FileBrowser(config)
        yield browser
        browser.close()
        
    @pytest.fixture
    def operation_tabs(self, qapp, config):
        """Create operation tabs for testing."""
        tabs = OperationTabs(config)
        yield tabs
        tabs.close()
        
    @pytest.fixture
    def progress_dialog(self, qapp):
        """Create progress dialog for testing."""
        dialog = ProgressDialog()
        yield dialog
        dialog.close()
        
    def test_main_window_creation(self, main_window):
        """Test main window creation."""
        assert main_window.windowTitle() == "Smart PDF Toolkit"
        assert main_window.config is not None
        assert main_window.file_browser is not None
        assert main_window.operation_tabs is not None
        
    def test_main_window_drag_drop_setup(self, main_window):
        """Test drag and drop setup."""
        assert main_window.acceptDrops() is True
        
    def test_file_browser_creation(self, file_browser):
        """Test file browser creation."""
        assert file_browser.config is not None
        assert file_browser.files == []
        assert file_browser.file_list is not None
        
    def test_file_browser_add_files(self, file_browser):
        """Test adding files to file browser."""
        test_files = [Path("test1.pdf"), Path("test2.pdf")]
        file_browser.add_files(test_files)
        
        assert len(file_browser.files) == 2
        assert file_browser.files == test_files
        
    def test_file_browser_clear_files(self, file_browser):
        """Test clearing files from file browser."""
        test_files = [Path("test1.pdf"), Path("test2.pdf")]
        file_browser.add_files(test_files)
        
        # Mock the message box to always return Yes
        with patch('smart_pdf_toolkit.gui.file_browser.QMessageBox.question', 
                  return_value=QMessageBox.StandardButton.Yes):
            file_browser.clear_files()
            
        assert len(file_browser.files) == 0
        
    def test_operation_tabs_creation(self, operation_tabs):
        """Test operation tabs creation."""
        assert operation_tabs.config is not None
        assert operation_tabs.count() >= 2  # At least PDF ops and content extraction
        
    def test_pdf_operations_tab(self, qapp, config):
        """Test PDF operations tab."""
        tab = PDFOperationsTab(config)
        
        # Test initial state
        assert not tab.merge_btn.isEnabled()
        assert not tab.split_btn.isEnabled()
        assert not tab.rotate_btn.isEnabled()
        
        # Test with multiple files selected
        test_files = [Path("test1.pdf"), Path("test2.pdf")]
        tab.set_selected_files(test_files)
        
        assert tab.merge_btn.isEnabled()  # Should be enabled with multiple files
        assert not tab.split_btn.isEnabled()  # Should be disabled (needs single file)
        assert not tab.rotate_btn.isEnabled()  # Should be disabled (needs single file)
        
        # Test with single file selected
        tab.set_selected_files([Path("test.pdf")])
        
        assert not tab.merge_btn.isEnabled()  # Should be disabled (needs multiple files)
        assert tab.split_btn.isEnabled()  # Should be enabled with single file
        assert tab.rotate_btn.isEnabled()  # Should be enabled with single file
        
        tab.close()
        
    def test_progress_dialog_creation(self, progress_dialog):
        """Test progress dialog creation."""
        assert progress_dialog.windowTitle() == "Processing..."
        assert progress_dialog.isModal() is True
        assert progress_dialog.is_cancellable is True
        assert progress_dialog.is_cancelled is False
        
    def test_progress_dialog_set_message(self, progress_dialog):
        """Test setting progress dialog message."""
        test_message = "Test processing message"
        progress_dialog.set_message(test_message)
        assert progress_dialog.message_label.text() == test_message
        
    def test_progress_dialog_set_progress(self, progress_dialog):
        """Test setting progress value."""
        progress_dialog.set_progress(50)
        assert progress_dialog.progress_bar.value() == 50
        
    def test_progress_dialog_indeterminate(self, progress_dialog):
        """Test indeterminate progress mode."""
        progress_dialog.set_indeterminate(True)
        assert progress_dialog.progress_bar.minimum() == 0
        assert progress_dialog.progress_bar.maximum() == 0
        
        progress_dialog.set_indeterminate(False)
        assert progress_dialog.progress_bar.minimum() == 0
        assert progress_dialog.progress_bar.maximum() == 100
        
    def test_progress_dialog_cancellation(self, progress_dialog):
        """Test progress dialog cancellation."""
        # Test cancellable state
        progress_dialog.set_cancellable(True)
        assert progress_dialog.cancel_btn.isEnabled() is True
        
        progress_dialog.set_cancellable(False)
        assert progress_dialog.cancel_btn.isEnabled() is False
        
    def test_main_window_file_operations(self, main_window):
        """Test main window file operations."""
        # Test initial state
        assert len(main_window.current_files) == 0
        
        # Test adding files
        test_files = [Path("test1.pdf"), Path("test2.pdf")]
        main_window.add_files(test_files)
        
        assert len(main_window.current_files) == 2
        assert main_window.current_files == test_files
        
        # Test clearing files
        main_window.clear_files()
        assert len(main_window.current_files) == 0
        
    def test_main_window_status_updates(self, main_window):
        """Test main window status updates."""
        # Test initial status
        assert "No files loaded" in main_window.file_count_label.text()
        
        # Test with files
        test_files = [Path("test1.pdf"), Path("test2.pdf")]
        main_window.add_files(test_files)
        
        assert "2 files loaded" in main_window.file_count_label.text()
        
        # Test with single file
        main_window.clear_files()
        main_window.add_files([Path("test.pdf")])
        
        assert "1 file loaded" in main_window.file_count_label.text()


@pytest.mark.skipif(not PYQT_AVAILABLE, reason="PyQt6 not available")
class TestGUIIntegration:
    """Test GUI component integration."""
    
    @pytest.fixture(scope="class")
    def qapp(self):
        """Create QApplication for testing."""
        if not QApplication.instance():
            app = QApplication([])
        else:
            app = QApplication.instance()
        yield app
        
    @pytest.fixture
    def config(self):
        """Create test configuration."""
        return Config()
        
    def test_file_browser_operation_tabs_integration(self, qapp, config):
        """Test integration between file browser and operation tabs."""
        # Create components
        file_browser = FileBrowser(config)
        operation_tabs = OperationTabs(config)
        
        # Connect signals
        file_browser.files_selected.connect(operation_tabs.set_selected_files)
        
        # Add files to browser
        test_files = [Path("test1.pdf"), Path("test2.pdf")]
        file_browser.add_files(test_files)
        
        # Select files in browser
        file_browser.file_list.selectAll()
        
        # Verify operation tabs received the selection
        # Note: This would require more complex testing with actual signal emission
        
        file_browser.close()
        operation_tabs.close()
        
    def test_main_window_component_integration(self, qapp, config):
        """Test main window component integration."""
        window = MainWindow(config)
        
        # Test that components are properly connected
        assert window.file_browser is not None
        assert window.operation_tabs is not None
        
        # Test file addition through main window
        test_files = [Path("test1.pdf"), Path("test2.pdf")]
        window.add_files(test_files)
        
        # Verify files are in both main window and file browser
        assert len(window.current_files) == 2
        assert len(window.file_browser.files) == 2
        
        window.close()


# Mock tests for when PyQt6 is not available
@pytest.mark.skipif(not PYQT_AVAILABLE, reason="PyQt6 not available")
class TestGUIDialogs:
    """Test GUI dialogs and advanced components."""
    
    @pytest.fixture(scope="class")
    def qapp(self):
        """Create QApplication for testing."""
        if not QApplication.instance():
            app = QApplication([])
        else:
            app = QApplication.instance()
        yield app
        
    @pytest.fixture
    def config(self):
        """Create test configuration."""
        return Config()
        
    def test_settings_dialog_creation(self, qapp, config):
        """Test settings dialog creation."""
        from smart_pdf_toolkit.gui.settings_dialog import SettingsDialog
        
        dialog = SettingsDialog(config)
        assert dialog.windowTitle() == "Settings"
        assert dialog.config is config
        assert dialog.tab_widget.count() >= 3  # General, OCR, AI tabs
        dialog.close()
        
    def test_batch_processing_dialog_creation(self, qapp, config):
        """Test batch processing dialog creation."""
        from smart_pdf_toolkit.gui.batch_processing_dialog import BatchProcessingDialog
        
        dialog = BatchProcessingDialog(config)
        assert dialog.windowTitle() == "Batch Processing"
        assert dialog.config is config
        assert dialog.tab_widget.count() == 2  # Configure and Queue tabs
        dialog.close()
        
    def test_ai_services_tab(self, qapp, config):
        """Test AI services tab functionality."""
        from smart_pdf_toolkit.gui.ai_services_tab import AIServicesTab
        
        tab = AIServicesTab(config)
        
        # Test initial state
        assert not tab.summarize_btn.isEnabled()
        assert not tab.analyze_btn.isEnabled()
        assert not tab.answer_btn.isEnabled()
        assert not tab.translate_btn.isEnabled()
        
        # Test with files selected
        test_files = [Path("test1.pdf"), Path("test2.pdf")]
        tab.set_selected_files(test_files)
        
        assert tab.summarize_btn.isEnabled()
        assert tab.analyze_btn.isEnabled()
        assert tab.answer_btn.isEnabled()
        assert tab.translate_btn.isEnabled()
        
        tab.close()
        
    def test_format_conversion_tab(self, qapp, config):
        """Test format conversion tab functionality."""
        from smart_pdf_toolkit.gui.format_conversion_tab import FormatConversionTab
        
        tab = FormatConversionTab(config)
        
        # Test initial state
        assert not tab.pdf_to_images_btn.isEnabled()
        assert not tab.images_to_pdf_btn.isEnabled()
        assert not tab.pdf_to_office_btn.isEnabled()
        assert not tab.pdf_to_html_btn.isEnabled()
        
        # Test with PDF files selected
        test_files = [Path("test1.pdf"), Path("test2.pdf")]
        tab.set_selected_files(test_files)
        
        assert tab.pdf_to_images_btn.isEnabled()
        assert tab.pdf_to_office_btn.isEnabled()
        assert tab.pdf_to_html_btn.isEnabled()
        # images_to_pdf should still be disabled (needs image files)
        assert not tab.images_to_pdf_btn.isEnabled()
        
        tab.close()
        
    def test_security_optimization_tab(self, qapp, config):
        """Test security and optimization tab functionality."""
        from smart_pdf_toolkit.gui.security_optimization_tab import SecurityOptimizationTab
        
        tab = SecurityOptimizationTab(config)
        
        # Test initial state
        assert not tab.add_password_btn.isEnabled()
        assert not tab.remove_password_btn.isEnabled()
        assert not tab.add_watermark_btn.isEnabled()
        assert not tab.optimize_btn.isEnabled()
        assert not tab.sign_btn.isEnabled()
        
        # Test with files selected
        test_files = [Path("test1.pdf"), Path("test2.pdf")]
        tab.set_selected_files(test_files)
        
        assert tab.add_password_btn.isEnabled()
        assert tab.remove_password_btn.isEnabled()
        assert tab.add_watermark_btn.isEnabled()
        assert tab.optimize_btn.isEnabled()
        assert tab.sign_btn.isEnabled()
        
        tab.close()
        
    def test_batch_job_configuration(self, qapp, config):
        """Test batch job configuration widget."""
        from smart_pdf_toolkit.gui.batch_processing_dialog import BatchJobWidget
        
        widget = BatchJobWidget(config)
        
        # Test initial state
        assert not widget.add_job_btn.isEnabled()
        assert len(widget.selected_files) == 0
        
        # Test adding files
        test_files = [Path("test1.pdf"), Path("test2.pdf")]
        widget.selected_files = test_files
        widget.update_files_list()
        
        assert widget.add_job_btn.isEnabled()
        assert widget.files_list.count() == 2
        
        widget.close()


@pytest.mark.skipif(PYQT_AVAILABLE, reason="PyQt6 is available")
class TestGUIMocks:
    """Test GUI components with mocks when PyQt6 is not available."""
    
    def test_gui_import_fallback(self):
        """Test that GUI imports fail gracefully when PyQt6 is not available."""
        # This test ensures that the GUI module can be imported even without PyQt6
        # The actual GUI functionality would not work, but imports should not fail
        
        with pytest.raises(ImportError):
            from PyQt6.QtWidgets import QApplication
            
    def test_gui_dependency_check(self):
        """Test GUI dependency checking."""
        from smart_pdf_toolkit.gui.app import check_dependencies
        
        deps_ok, deps_msg = check_dependencies()
        assert not deps_ok
        assert "PyQt6" in deps_msg