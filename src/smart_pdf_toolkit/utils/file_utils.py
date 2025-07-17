"""
File operation utilities.
"""

import os
import shutil
import tempfile
from typing import List, Optional, Union
from pathlib import Path
from ..core.exceptions import FileOperationError


class FileManager:
    """Manages file operations and temporary file handling."""
    
    def __init__(self, temp_dir: Optional[str] = None):
        """Initialize file manager.
        
        Args:
            temp_dir: Directory for temporary files
        """
        self.temp_dir = temp_dir or tempfile.gettempdir()
        self._temp_files: List[str] = []
    
    def create_temp_file(self, suffix: str = ".pdf", prefix: str = "smart_pdf_") -> str:
        """Create a temporary file.
        
        Args:
            suffix: File extension
            prefix: File name prefix
            
        Returns:
            Path to temporary file
        """
        try:
            fd, temp_path = tempfile.mkstemp(suffix=suffix, prefix=prefix, dir=self.temp_dir)
            os.close(fd)
            self._temp_files.append(temp_path)
            return temp_path
        except Exception as e:
            raise FileOperationError(f"Failed to create temporary file: {str(e)}")
    
    def create_temp_dir(self, prefix: str = "smart_pdf_") -> str:
        """Create a temporary directory.
        
        Args:
            prefix: Directory name prefix
            
        Returns:
            Path to temporary directory
        """
        try:
            temp_dir = tempfile.mkdtemp(prefix=prefix, dir=self.temp_dir)
            self._temp_files.append(temp_dir)
            return temp_dir
        except Exception as e:
            raise FileOperationError(f"Failed to create temporary directory: {str(e)}")
    
    def cleanup_temp_files(self) -> None:
        """Clean up all temporary files and directories."""
        for temp_path in self._temp_files:
            try:
                if os.path.isfile(temp_path):
                    os.unlink(temp_path)
                elif os.path.isdir(temp_path):
                    shutil.rmtree(temp_path)
            except Exception:
                # Ignore cleanup errors
                pass
        self._temp_files.clear()
    
    def ensure_directory(self, directory: Union[str, Path]) -> None:
        """Ensure a directory exists, create if necessary.
        
        Args:
            directory: Directory path
        """
        try:
            Path(directory).mkdir(parents=True, exist_ok=True)
        except Exception as e:
            raise FileOperationError(f"Failed to create directory {directory}: {str(e)}")
    
    def copy_file(self, source: Union[str, Path], destination: Union[str, Path]) -> None:
        """Copy a file from source to destination.
        
        Args:
            source: Source file path
            destination: Destination file path
        """
        try:
            shutil.copy2(source, destination)
        except Exception as e:
            raise FileOperationError(f"Failed to copy file from {source} to {destination}: {str(e)}")
    
    def move_file(self, source: Union[str, Path], destination: Union[str, Path]) -> None:
        """Move a file from source to destination.
        
        Args:
            source: Source file path
            destination: Destination file path
        """
        try:
            shutil.move(source, destination)
        except Exception as e:
            raise FileOperationError(f"Failed to move file from {source} to {destination}: {str(e)}")
    
    def delete_file(self, file_path: Union[str, Path]) -> None:
        """Delete a file.
        
        Args:
            file_path: Path to file to delete
        """
        try:
            os.unlink(file_path)
        except Exception as e:
            raise FileOperationError(f"Failed to delete file {file_path}: {str(e)}")
    
    def get_file_size(self, file_path: Union[str, Path]) -> int:
        """Get file size in bytes.
        
        Args:
            file_path: Path to file
            
        Returns:
            File size in bytes
        """
        try:
            return os.path.getsize(file_path)
        except Exception as e:
            raise FileOperationError(f"Failed to get file size for {file_path}: {str(e)}")
    
    def validate_pdf_file(self, file_path: Union[str, Path]) -> bool:
        """Basic validation that file exists and has PDF extension.
        
        Args:
            file_path: Path to PDF file
            
        Returns:
            True if file appears to be a valid PDF
        """
        path = Path(file_path)
        return (path.exists() and 
                path.is_file() and 
                path.suffix.lower() == '.pdf' and 
                path.stat().st_size > 0)
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - cleanup temporary files."""
        self.cleanup_temp_files()


# Convenience functions for common file operations
def ensure_directory_exists(directory: Union[str, Path]) -> None:
    """Ensure a directory exists, create if necessary."""
    file_manager = FileManager()
    file_manager.ensure_directory(directory)


def get_unique_filename(file_path: Union[str, Path]) -> str:
    """Get a unique filename by appending a number if file exists.
    
    Args:
        file_path: Desired file path
        
    Returns:
        Unique file path
    """
    path = Path(file_path)
    if not path.exists():
        return str(file_path)
    
    base = path.stem
    suffix = path.suffix
    parent = path.parent
    counter = 1
    
    while True:
        new_name = f"{base}_{counter}{suffix}"
        new_path = parent / new_name
        if not new_path.exists():
            return str(new_path)
        counter += 1


def copy_file(source: Union[str, Path], destination: Union[str, Path]) -> None:
    """Copy a file from source to destination."""
    file_manager = FileManager()
    file_manager.copy_file(source, destination)


def move_file(source: Union[str, Path], destination: Union[str, Path]) -> None:
    """Move a file from source to destination."""
    file_manager = FileManager()
    file_manager.move_file(source, destination)


def delete_file(file_path: Union[str, Path]) -> None:
    """Delete a file."""
    file_manager = FileManager()
    file_manager.delete_file(file_path)


def get_file_size(file_path: Union[str, Path]) -> int:
    """Get file size in bytes."""
    file_manager = FileManager()
    return file_manager.get_file_size(file_path)


def validate_pdf_file(file_path: Union[str, Path]) -> bool:
    """Basic validation that file exists and has PDF extension."""
    file_manager = FileManager()
    return file_manager.validate_pdf_file(file_path)