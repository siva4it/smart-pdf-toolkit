"""
Desktop GUI application module.
"""

from .main_window import MainWindow, main
from .file_browser import FileBrowser
from .operation_tabs import OperationTabs
from .progress_dialog import ProgressDialog, SimpleProgressDialog
from .ai_services_tab import AIServicesTab
from .format_conversion_tab import FormatConversionTab
from .security_optimization_tab import SecurityOptimizationTab
from .settings_dialog import SettingsDialog
from .batch_processing_dialog import BatchProcessingDialog

__all__ = [
    'MainWindow',
    'main',
    'FileBrowser', 
    'OperationTabs',
    'ProgressDialog',
    'SimpleProgressDialog',
    'AIServicesTab',
    'FormatConversionTab',
    'SecurityOptimizationTab',
    'SettingsDialog',
    'BatchProcessingDialog'
]