"""
Update mechanism for Smart PDF Toolkit.
"""

import os
import sys
import json
import requests
import tempfile
import subprocess
import platform
from pathlib import Path
from typing import Dict, Optional, Tuple
import logging
from packaging import version

logger = logging.getLogger(__name__)


class UpdateManager:
    """Manages application updates."""
    
    def __init__(self, current_version: str = "1.0.0"):
        """
        Initialize update manager.
        
        Args:
            current_version: Current application version
        """
        self.current_version = current_version
        self.update_url = "https://api.github.com/repos/siva4it/smart-pdf-toolkit/releases"
        self.download_base_url = "https://github.com/siva4it/smart-pdf-toolkit/releases/download"
        
    def check_for_updates(self) -> Tuple[bool, Optional[Dict]]:
        """
        Check for available updates.
        
        Returns:
            Tuple of (update_available, release_info)
        """
        try:
            response = requests.get(f"{self.update_url}/latest", timeout=10)
            response.raise_for_status()
            
            release_info = response.json()
            latest_version = release_info["tag_name"].lstrip("v")
            
            if version.parse(latest_version) > version.parse(self.current_version):
                logger.info(f"Update available: {latest_version} (current: {self.current_version})")
                return True, release_info
            else:
                logger.info("No updates available")
                return False, None
                
        except Exception as e:
            logger.error(f"Failed to check for updates: {e}")
            return False, None
    
    def get_download_url(self, release_info: Dict) -> Optional[str]:
        """
        Get the appropriate download URL for the current platform.
        
        Args:
            release_info: Release information from GitHub API
            
        Returns:
            Download URL or None if not found
        """
        system = platform.system().lower()
        machine = platform.machine().lower()
        
        # Map platform to expected asset names
        asset_patterns = {
            "windows": ["smart-pdf-toolkit-windows", ".exe", ".msi"],
            "darwin": ["smart-pdf-toolkit-macos", ".dmg", ".pkg"],
            "linux": ["smart-pdf-toolkit-linux", ".AppImage", ".tar.gz"]
        }
        
        if system not in asset_patterns:
            logger.error(f"Unsupported platform: {system}")
            return None
        
        patterns = asset_patterns[system]
        
        for asset in release_info.get("assets", []):
            asset_name = asset["name"].lower()
            
            # Check if asset matches platform patterns
            if any(pattern in asset_name for pattern in patterns):
                # Prefer installer formats over executables
                if system == "windows" and ".msi" in asset_name:
                    return asset["browser_download_url"]
                elif system == "darwin" and ".dmg" in asset_name:
                    return asset["browser_download_url"]
                elif system == "linux" and ".AppImage" in asset_name:
                    return asset["browser_download_url"]
                elif any(ext in asset_name for ext in [".exe", ".tar.gz"]):
                    return asset["browser_download_url"]
        
        logger.warning(f"No suitable download found for {system}")
        return None
    
    def download_update(self, download_url: str, progress_callback=None) -> Optional[str]:
        """
        Download update file.
        
        Args:
            download_url: URL to download from
            progress_callback: Optional callback for progress updates
            
        Returns:
            Path to downloaded file or None if failed
        """
        try:
            response = requests.get(download_url, stream=True, timeout=30)
            response.raise_for_status()
            
            # Get filename from URL or Content-Disposition header
            filename = download_url.split("/")[-1]
            if "Content-Disposition" in response.headers:
                content_disp = response.headers["Content-Disposition"]
                if "filename=" in content_disp:
                    filename = content_disp.split("filename=")[1].strip('"')
            
            # Create temporary file
            temp_dir = tempfile.gettempdir()
            file_path = os.path.join(temp_dir, filename)
            
            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0
            
            with open(file_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        
                        if progress_callback and total_size > 0:
                            progress = (downloaded / total_size) * 100
                            progress_callback(progress)
            
            logger.info(f"Update downloaded to: {file_path}")
            return file_path
            
        except Exception as e:
            logger.error(f"Failed to download update: {e}")
            return None
    
    def install_update(self, update_file: str) -> bool:
        """
        Install the downloaded update.
        
        Args:
            update_file: Path to the update file
            
        Returns:
            True if installation started successfully, False otherwise
        """
        try:
            system = platform.system().lower()
            
            if system == "windows":
                return self._install_windows_update(update_file)
            elif system == "darwin":
                return self._install_macos_update(update_file)
            elif system == "linux":
                return self._install_linux_update(update_file)
            else:
                logger.error(f"Update installation not supported on {system}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to install update: {e}")
            return False
    
    def _install_windows_update(self, update_file: str) -> bool:
        """Install Windows update."""
        if update_file.endswith('.msi'):
            # Run MSI installer
            subprocess.Popen([
                'msiexec', '/i', update_file, '/quiet', '/norestart'
            ], creationflags=subprocess.CREATE_NEW_CONSOLE)
            return True
        elif update_file.endswith('.exe'):
            # Run executable installer
            subprocess.Popen([update_file, '/S'], 
                           creationflags=subprocess.CREATE_NEW_CONSOLE)
            return True
        else:
            logger.error(f"Unsupported Windows update format: {update_file}")
            return False
    
    def _install_macos_update(self, update_file: str) -> bool:
        """Install macOS update."""
        if update_file.endswith('.dmg'):
            # Mount DMG and copy application
            try:
                # Mount the DMG
                mount_result = subprocess.run([
                    'hdiutil', 'attach', update_file, '-nobrowse', '-quiet'
                ], capture_output=True, text=True)
                
                if mount_result.returncode == 0:
                    # Find mounted volume
                    mount_point = None
                    for line in mount_result.stdout.split('\n'):
                        if '/Volumes/' in line:
                            mount_point = line.split('\t')[-1].strip()
                            break
                    
                    if mount_point:
                        # Copy application to Applications folder
                        app_path = os.path.join(mount_point, "Smart PDF Toolkit.app")
                        if os.path.exists(app_path):
                            subprocess.run([
                                'cp', '-R', app_path, '/Applications/'
                            ])
                            
                            # Unmount DMG
                            subprocess.run(['hdiutil', 'detach', mount_point, '-quiet'])
                            return True
                
                return False
                
            except Exception as e:
                logger.error(f"Failed to install macOS update: {e}")
                return False
        else:
            logger.error(f"Unsupported macOS update format: {update_file}")
            return False
    
    def _install_linux_update(self, update_file: str) -> bool:
        """Install Linux update."""
        if update_file.endswith('.AppImage'):
            # Make AppImage executable and replace current installation
            try:
                os.chmod(update_file, 0o755)
                
                # Get current executable path
                current_exe = sys.executable
                if current_exe.endswith('.AppImage'):
                    # Replace current AppImage
                    backup_path = current_exe + '.backup'
                    os.rename(current_exe, backup_path)
                    os.rename(update_file, current_exe)
                    os.remove(backup_path)
                    return True
                else:
                    # Install to /usr/local/bin or ~/.local/bin
                    install_dir = os.path.expanduser('~/.local/bin')
                    os.makedirs(install_dir, exist_ok=True)
                    
                    install_path = os.path.join(install_dir, 'smart-pdf-toolkit')
                    os.rename(update_file, install_path)
                    
                    return True
                    
            except Exception as e:
                logger.error(f"Failed to install Linux update: {e}")
                return False
        else:
            logger.error(f"Unsupported Linux update format: {update_file}")
            return False
    
    def get_update_info(self) -> Dict:
        """
        Get comprehensive update information.
        
        Returns:
            Dictionary with update information
        """
        update_available, release_info = self.check_for_updates()
        
        info = {
            'current_version': self.current_version,
            'update_available': update_available,
            'platform': platform.system(),
            'architecture': platform.machine()
        }
        
        if release_info:
            info.update({
                'latest_version': release_info['tag_name'].lstrip('v'),
                'release_name': release_info['name'],
                'release_notes': release_info['body'],
                'published_at': release_info['published_at'],
                'download_url': self.get_download_url(release_info)
            })
        
        return info
    
    def auto_update(self, progress_callback=None) -> bool:
        """
        Perform automatic update if available.
        
        Args:
            progress_callback: Optional callback for progress updates
            
        Returns:
            True if update was successful, False otherwise
        """
        try:
            # Check for updates
            update_available, release_info = self.check_for_updates()
            if not update_available:
                return False
            
            # Get download URL
            download_url = self.get_download_url(release_info)
            if not download_url:
                return False
            
            # Download update
            update_file = self.download_update(download_url, progress_callback)
            if not update_file:
                return False
            
            # Install update
            return self.install_update(update_file)
            
        except Exception as e:
            logger.error(f"Auto-update failed: {e}")
            return False


def check_for_updates() -> Dict:
    """
    Convenience function to check for updates.
    
    Returns:
        Update information dictionary
    """
    from . import __version__
    updater = UpdateManager(__version__)
    return updater.get_update_info()


def perform_update(progress_callback=None) -> bool:
    """
    Convenience function to perform update.
    
    Args:
        progress_callback: Optional callback for progress updates
        
    Returns:
        True if update was successful, False otherwise
    """
    from . import __version__
    updater = UpdateManager(__version__)
    return updater.auto_update(progress_callback)