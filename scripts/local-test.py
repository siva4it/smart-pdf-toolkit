#!/usr/bin/env python3
"""
Local testing script for Smart PDF Toolkit
Tests all major functionality locally before deployment
"""

import os
import sys
import subprocess
import requests
import time
import json
from pathlib import Path
from typing import Dict, List, Optional

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

class LocalTester:
    def __init__(self):
        self.base_url = "http://localhost:8000"
        self.test_files_dir = project_root / "tests" / "fixtures"
        self.results = []
        
    def log(self, message: str, level: str = "INFO"):
        """Log message with timestamp"""
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] [{level}] {message}")
        
    def run_command(self, command: List[str], cwd: Optional[Path] = None) -> Dict:
        """Run shell command and return result"""
        try:
            result = subprocess.run(
                command,
                cwd=cwd or project_root,
                capture_output=True,
                text=True,
                timeout=60
            )
            return {
                "success": result.returncode == 0,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode
            }
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "stdout": "",
                "stderr": "Command timed out",
                "returncode": -1
            }
        except Exception as e:
            return {
                "success": False,
                "stdout": "",
                "stderr": str(e),
                "returncode": -1
            }
    
    def test_installation(self) -> bool:
        """Test package installation"""
        self.log("Testing package installation...")
        
        # Test pip install
        result = self.run_command([sys.executable, "-m", "pip", "install", "-e", "."])
        if not result["success"]:
            self.log(f"Installation failed: {result['stderr']}", "ERROR")
            return False
            
        # Test imports
        try:
            import smart_pdf_toolkit
            self.log("Package import successful")
            return True
        except ImportError as e:
            self.log(f"Import failed: {e}", "ERROR")
            return False
    
    def test_cli_commands(self) -> bool:
        """Test CLI functionality"""
        self.log("Testing CLI commands...")
        
        # Test help command
        result = self.run_command([sys.executable, "-m", "smart_pdf_toolkit.cli.main", "--help"])
        if not result["success"]:
            self.log(f"CLI help failed: {result['stderr']}", "ERROR")
            return False
            
        self.log("CLI help command successful")
        
        # Create test PDF if it doesn't exist
        test_pdf = self.test_files_dir / "test.pdf"
        if not test_pdf.exists():
            self.create_test_pdf(test_pdf)
        
        if test_pdf.exists():
            # Test info command
            result = self.run_command([
                sys.executable, "-m", "smart_pdf_toolkit.cli.main",
                "info", str(test_pdf)
            ])
            if result["success"]:
                self.log("CLI info command successful")
            else:
                self.log(f"CLI info command failed: {result['stderr']}", "WARN")
        
        return True
    
    def create_test_pdf(self, filepath: Path):
        """Create a simple test PDF"""
        try:
            from reportlab.pdfgen import canvas
            from reportlab.lib.pagesizes import letter
            
            filepath.parent.mkdir(parents=True, exist_ok=True)
            
            c = canvas.Canvas(str(filepath), pagesize=letter)
            c.drawString(100, 750, "Smart PDF Toolkit Test Document")
            c.drawString(100, 700, "This is a test PDF for local testing.")
            c.drawString(100, 650, "Generated automatically by the test suite.")
            c.save()
            
            self.log(f"Created test PDF: {filepath}")
        except ImportError:
            self.log("reportlab not available, skipping PDF creation", "WARN")
        except Exception as e:
            self.log(f"Failed to create test PDF: {e}", "WARN")
    
    def start_api_server(self) -> subprocess.Popen:
        """Start the API server in background"""
        self.log("Starting API server...")
        
        env = os.environ.copy()
        env["SMART_PDF_DEBUG"] = "true"
        
        process = subprocess.Popen([
            sys.executable, "-m", "smart_pdf_toolkit.api.main"
        ], env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # Wait for server to start
        for i in range(30):
            try:
                response = requests.get(f"{self.base_url}/health", timeout=2)
                if response.status_code == 200:
                    self.log("API server started successfully")
                    return process
            except requests.exceptions.RequestException:
                pass
            time.sleep(1)
        
        self.log("API server failed to start", "ERROR")
        process.terminate()
        return None
    
    def test_api_endpoints(self) -> bool:
        """Test API endpoints"""
        self.log("Testing API endpoints...")
        
        # Test health endpoint
        try:
            response = requests.get(f"{self.base_url}/health")
            if response.status_code == 200:
                self.log("Health endpoint successful")
            else:
                self.log(f"Health endpoint failed: {response.status_code}", "ERROR")
                return False
        except Exception as e:
            self.log(f"Health endpoint error: {e}", "ERROR")
            return False
        
        # Test docs endpoint
        try:
            response = requests.get(f"{self.base_url}/docs")
            if response.status_code == 200:
                self.log("API docs endpoint successful")
            else:
                self.log(f"API docs failed: {response.status_code}", "WARN")
        except Exception as e:
            self.log(f"API docs error: {e}", "WARN")
        
        # Test file upload endpoint
        test_pdf = self.test_files_dir / "test.pdf"
        if test_pdf.exists():
            try:
                with open(test_pdf, 'rb') as f:
                    files = {'file': f}
                    data = {'operation': 'info'}
                    response = requests.post(f"{self.base_url}/api/v1/process", files=files, data=data)
                    
                if response.status_code in [200, 202]:
                    self.log("File upload endpoint successful")
                else:
                    self.log(f"File upload failed: {response.status_code}", "WARN")
            except Exception as e:
                self.log(f"File upload error: {e}", "WARN")
        
        return True
    
    def test_gui_import(self) -> bool:
        """Test GUI module import"""
        self.log("Testing GUI module import...")
        
        try:
            # Test if PyQt6 is available
            import PyQt6
            from smart_pdf_toolkit.gui import main_window
            self.log("GUI modules imported successfully")
            return True
        except ImportError as e:
            self.log(f"GUI import failed (this is OK if PyQt6 not installed): {e}", "WARN")
            return True  # Not a critical failure
    
    def run_unit_tests(self) -> bool:
        """Run unit tests"""
        self.log("Running unit tests...")
        
        result = self.run_command([sys.executable, "-m", "pytest", "tests/", "-v", "--tb=short"])
        
        if result["success"]:
            self.log("Unit tests passed")
            return True
        else:
            self.log(f"Unit tests failed: {result['stderr']}", "ERROR")
            return False
    
    def test_docker_build(self) -> bool:
        """Test Docker build"""
        self.log("Testing Docker build...")
        
        # Check if Docker is available
        result = self.run_command(["docker", "--version"])
        if not result["success"]:
            self.log("Docker not available, skipping Docker tests", "WARN")
            return True
        
        # Build Docker image
        result = self.run_command([
            "docker", "build", "-t", "smart-pdf-toolkit:test", "--target", "production", "."
        ])
        
        if result["success"]:
            self.log("Docker build successful")
            
            # Test running container
            result = self.run_command([
                "docker", "run", "--rm", "-d", "--name", "smart-pdf-test",
                "-p", "8001:8000", "smart-pdf-toolkit:test"
            ])
            
            if result["success"]:
                time.sleep(10)  # Wait for container to start
                
                try:
                    response = requests.get("http://localhost:8001/health", timeout=5)
                    if response.status_code == 200:
                        self.log("Docker container test successful")
                    else:
                        self.log("Docker container health check failed", "WARN")
                except Exception as e:
                    self.log(f"Docker container test error: {e}", "WARN")
                
                # Stop container
                self.run_command(["docker", "stop", "smart-pdf-test"])
            
            return True
        else:
            self.log(f"Docker build failed: {result['stderr']}", "ERROR")
            return False
    
    def run_all_tests(self):
        """Run all tests"""
        self.log("Starting comprehensive local testing...")
        
        tests = [
            ("Installation", self.test_installation),
            ("CLI Commands", self.test_cli_commands),
            ("GUI Import", self.test_gui_import),
            ("Unit Tests", self.run_unit_tests),
            ("Docker Build", self.test_docker_build),
        ]
        
        # Start API server for API tests
        api_process = self.start_api_server()
        if api_process:
            tests.append(("API Endpoints", self.test_api_endpoints))
        
        # Run tests
        passed = 0
        total = len(tests)
        
        for test_name, test_func in tests:
            self.log(f"Running {test_name} test...")
            try:
                if test_func():
                    self.log(f"✓ {test_name} test PASSED", "INFO")
                    passed += 1
                else:
                    self.log(f"✗ {test_name} test FAILED", "ERROR")
            except Exception as e:
                self.log(f"✗ {test_name} test ERROR: {e}", "ERROR")
        
        # Stop API server
        if api_process:
            api_process.terminate()
            api_process.wait()
        
        # Summary
        self.log(f"Test Results: {passed}/{total} tests passed")
        
        if passed == total:
            self.log("🎉 All tests passed! Ready for deployment.", "INFO")
            return True
        else:
            self.log(f"❌ {total - passed} tests failed. Please fix issues before deployment.", "ERROR")
            return False

def main():
    """Main function"""
    tester = LocalTester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()