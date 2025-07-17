# Smart PDF Toolkit - Debug Guide

Guide for debugging issues and viewing logs in the Smart PDF Toolkit.

## 📁 **Log File Locations**

### Default Log Locations
```
# Windows
logs/smart_pdf_toolkit.log
temp/smart_pdf_toolkit.log

# Linux/Mac
./logs/smart_pdf_toolkit.log
/tmp/smart_pdf_toolkit.log
```

### Environment-Specific Logs
```
# Development
config/development/.env.development -> LOG_FILE_PATH=./logs/development.log

# Production
/var/log/smart_pdf_toolkit.log (Linux)
C:\ProgramData\SmartPDFToolkit\logs\ (Windows)
```

## 🔧 **Enable Debug Logging**

### Method 1: Environment Variables
```bash
# Set debug level
export SMART_PDF_DEBUG=true
export SMART_PDF_LOG_LEVEL=DEBUG

# Run GUI with debug logging
smart-pdf-gui
```

### Method 2: Configuration File
Create/edit `.env` in project root:
```bash
# Debug Configuration
SMART_PDF_DEBUG=true
SMART_PDF_LOG_LEVEL=DEBUG
LOG_TO_FILE=true
LOG_FILE_PATH=./logs/debug.log
```

### Method 3: Direct Python Logging
Add this to your code for immediate debugging:
```python
import logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('debug.log'),
        logging.StreamHandler()
    ]
)
```

## 🐛 **Debug Merge Functionality**

### Check Merge Operation Logs
```bash
# Create logs directory
mkdir -p logs

# Run with debug logging
SMART_PDF_DEBUG=true SMART_PDF_LOG_LEVEL=DEBUG smart-pdf-gui

# Or run directly with logging
python -c "
import logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
import sys
sys.path.insert(0, 'src')
from smart_pdf_toolkit.gui.app import main
main()
"
```

### Common Merge Issues & Solutions

**1. File Path Issues**
```python
# Check if files exist and are readable
for file_path in selected_files:
    if not file_path.exists():
        print(f"File not found: {file_path}")
    if not file_path.is_file():
        print(f"Not a file: {file_path}")
    try:
        with open(file_path, 'rb') as f:
            f.read(1024)  # Test read
    except Exception as e:
        print(f"Cannot read file {file_path}: {e}")
```

**2. PDF Corruption Issues**
```python
# Test PDF validity
import PyMuPDF as fitz
for file_path in selected_files:
    try:
        doc = fitz.open(file_path)
        print(f"PDF {file_path}: {doc.page_count} pages")
        doc.close()
    except Exception as e:
        print(f"Invalid PDF {file_path}: {e}")
```

**3. Output Directory Issues**
```python
# Check output directory permissions
import os
output_dir = Path("output")
output_dir.mkdir(exist_ok=True)
if not os.access(output_dir, os.W_OK):
    print(f"Cannot write to {output_dir}")
```

## 🔍 **Real-time Debugging**

### Console Output
Run the GUI from terminal to see real-time output:
```bash
# Windows Command Prompt
python src/smart_pdf_toolkit/gui/app.py

# PowerShell
python src\smart_pdf_toolkit\gui\app.py

# Add debug prints
PYTHONPATH=src python -c "
import sys
sys.path.insert(0, 'src')
from smart_pdf_toolkit.gui.app import main
print('Starting GUI application...')
main()
"
```

### Add Debug Prints to GUI
Temporarily add debug prints to the merge function:

```python
# In src/smart_pdf_toolkit/gui/operation_tabs.py
def on_merge_clicked(self):
    """Handle merge button click."""
    print(f"DEBUG: Merge clicked with {len(self.selected_files)} files")
    print(f"DEBUG: Selected files: {[str(f) for f in self.selected_files]}")
    
    if len(self.selected_files) < 2:
        print("DEBUG: Not enough files selected")
        QMessageBox.warning(self, "Warning", "Please select at least 2 files to merge.")
        return
        
    output_file = self.merge_output_edit.text().strip()
    if not output_file:
        output_file = "merged_output.pdf"
    
    print(f"DEBUG: Output file: {output_file}")
    
    params = {
        'files': self.selected_files,
        'output_file': output_file
    }
    
    print(f"DEBUG: Emitting operation_requested with params: {params}")
    self.operation_requested.emit('merge', params)
```

## 📊 **Log Analysis**

### View Recent Logs
```bash
# View last 50 lines of log
tail -50 logs/smart_pdf_toolkit.log

# Follow log in real-time
tail -f logs/smart_pdf_toolkit.log

# Search for errors
grep -i error logs/smart_pdf_toolkit.log
grep -i merge logs/smart_pdf_toolkit.log
```

### Windows Log Viewing
```powershell
# View log file
Get-Content logs\smart_pdf_toolkit.log -Tail 50

# Follow log in real-time
Get-Content logs\smart_pdf_toolkit.log -Wait

# Search for errors
Select-String -Path logs\smart_pdf_toolkit.log -Pattern "error|merge" -CaseSensitive:$false
```

## 🚨 **Quick Debug Steps for Merge Issue**

1. **Enable Debug Mode**:
   ```bash
   export SMART_PDF_DEBUG=true
   export SMART_PDF_LOG_LEVEL=DEBUG
   ```

2. **Run GUI from Terminal**:
   ```bash
   python src/smart_pdf_toolkit/gui/app.py
   ```

3. **Try Merge Operation** and watch terminal output

4. **Check Log Files**:
   ```bash
   ls -la logs/
   cat logs/smart_pdf_toolkit.log
   ```

5. **Test Core Merge Function**:
   ```python
   # Test merge directly
   python -c "
   import sys
   sys.path.insert(0, 'src')
   from smart_pdf_toolkit.core.pdf_operations import PDFOperations
   from pathlib import Path
   
   ops = PDFOperations()
   files = [Path('file1.pdf'), Path('file2.pdf')]  # Replace with your files
   result = ops.merge_pdfs(files, 'test_merge.pdf')
   print(f'Merge result: {result}')
   "
   ```

## 📝 **Create Debug Log Script**

Create `debug_merge.py`:
```python
#!/usr/bin/env python3
import sys
import logging
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('merge_debug.log'),
        logging.StreamHandler()
    ]
)

# Add src to path
sys.path.insert(0, 'src')

try:
    from smart_pdf_toolkit.core.pdf_operations import PDFOperations
    
    # Test merge functionality
    ops = PDFOperations()
    
    # Replace with your actual file paths
    files = [
        Path('path/to/file1.pdf'),
        Path('path/to/file2.pdf')
    ]
    
    print(f"Testing merge with files: {files}")
    
    # Check files exist
    for file_path in files:
        if not file_path.exists():
            print(f"ERROR: File not found: {file_path}")
            sys.exit(1)
    
    # Attempt merge
    result = ops.merge_pdfs(files, 'debug_merge_output.pdf')
    print(f"Merge result: {result}")
    
except Exception as e:
    logging.exception("Error during merge test")
    print(f"ERROR: {e}")
```

Run with: `python debug_merge.py`

## 🎯 **Next Steps**

1. **Run GUI from terminal** to see real-time output
2. **Check logs directory** for error messages
3. **Test merge with simple PDFs** first
4. **Share the error output** for specific debugging help

The logs will show exactly what's happening during the merge operation! 🔍