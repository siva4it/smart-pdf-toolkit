"""
Shell completion support for the CLI.
"""

import click
import os
from pathlib import Path
from typing import List, Tuple


def complete_pdf_files(ctx, param, incomplete):
    """Complete PDF file paths."""
    return [
        click.shell_complete.CompletionItem(str(path))
        for path in Path('.').glob(f'{incomplete}*.pdf')
    ]


def complete_output_formats(ctx, param, incomplete):
    """Complete output format options."""
    formats = ['PDF', 'PNG', 'JPEG', 'TIFF', 'CSV', 'Excel', 'JSON', 'TXT']
    return [
        click.shell_complete.CompletionItem(fmt)
        for fmt in formats
        if fmt.lower().startswith(incomplete.lower())
    ]


def complete_languages(ctx, param, incomplete):
    """Complete OCR language codes."""
    languages = [
        'eng', 'fra', 'deu', 'spa', 'ita', 'por', 'rus', 'chi_sim', 'chi_tra',
        'jpn', 'kor', 'ara', 'hin', 'tha', 'vie', 'nld', 'swe', 'nor', 'dan'
    ]
    return [
        click.shell_complete.CompletionItem(lang)
        for lang in languages
        if lang.startswith(incomplete.lower())
    ]


def complete_operations(ctx, param, incomplete):
    """Complete batch operation types."""
    operations = [
        'merge', 'split', 'extract-text', 'extract-images', 'extract-tables',
        'ocr', 'summarize', 'analyze', 'translate', 'optimize', 'secure'
    ]
    return [
        click.shell_complete.CompletionItem(op)
        for op in operations
        if op.startswith(incomplete.lower())
    ]


def complete_config_files(ctx, param, incomplete):
    """Complete configuration file paths."""
    extensions = ['.yaml', '.yml', '.json']
    matches = []
    
    for ext in extensions:
        matches.extend(Path('.').glob(f'{incomplete}*{ext}'))
    
    return [
        click.shell_complete.CompletionItem(str(path))
        for path in matches
    ]


def install_shell_completion(shell: str = None) -> str:
    """
    Install shell completion for the current shell.
    
    Args:
        shell: Shell type (bash, zsh, fish, powershell)
        
    Returns:
        Installation instructions or completion script
    """
    if shell is None:
        shell = os.environ.get('SHELL', '').split('/')[-1]
    
    app_name = 'smart-pdf'
    
    if shell == 'bash':
        return f"""
# Add this to your ~/.bashrc or ~/.bash_profile:
eval "$(_SMART_PDF_COMPLETE=bash_source {app_name})"

# Or save the completion script:
_{app_name.upper()}_COMPLETE=bash_source {app_name} > ~/.{app_name}-complete.bash
echo 'source ~/.{app_name}-complete.bash' >> ~/.bashrc
"""
    
    elif shell == 'zsh':
        return f"""
# Add this to your ~/.zshrc:
eval "$(_SMART_PDF_COMPLETE=zsh_source {app_name})"

# Or save the completion script:
_{app_name.upper()}_COMPLETE=zsh_source {app_name} > ~/.{app_name}-complete.zsh
echo 'source ~/.{app_name}-complete.zsh' >> ~/.zshrc
"""
    
    elif shell == 'fish':
        return f"""
# Add this to your ~/.config/fish/config.fish:
eval (env _SMART_PDF_COMPLETE=fish_source {app_name})

# Or save the completion script:
_{app_name.upper()}_COMPLETE=fish_source {app_name} > ~/.config/fish/completions/{app_name}.fish
"""
    
    elif shell in ['powershell', 'pwsh']:
        return f"""
# Add this to your PowerShell profile:
Register-ArgumentCompleter -Native -CommandName {app_name} -ScriptBlock {{
    param($wordToComplete, $commandAst, $cursorPosition)
    $env:_SMART_PDF_COMPLETE = "powershell_complete"
    $env:_SMART_PDF_COMPLETE_WORD_TO_COMPLETE = $wordToComplete
    & {app_name} | ForEach-Object {{
        [System.Management.Automation.CompletionResult]::new($_, $_, 'ParameterValue', $_)
    }}
}}
"""
    
    else:
        return f"""
Shell completion is available for: bash, zsh, fish, powershell

To enable completion, run:
  {app_name} completion install

Or set the appropriate environment variable:
  _{app_name.upper()}_COMPLETE=<shell>_source {app_name}

Supported shells: bash, zsh, fish, powershell
"""


def get_completion_script(shell: str) -> str:
    """
    Get the completion script for a specific shell.
    
    Args:
        shell: Shell type
        
    Returns:
        Completion script content
    """
    import subprocess
    import sys
    
    app_name = 'smart-pdf'
    env_var = f'_{app_name.upper()}_COMPLETE'
    
    try:
        env = os.environ.copy()
        env[env_var] = f'{shell}_source'
        
        result = subprocess.run(
            [sys.executable, '-m', 'smart_pdf_toolkit'],
            env=env,
            capture_output=True,
            text=True
        )
        
        return result.stdout
    except Exception as e:
        return f"Error generating completion script: {e}"


class CompletionManager:
    """Manages shell completion installation and configuration."""
    
    def __init__(self):
        self.supported_shells = ['bash', 'zsh', 'fish', 'powershell']
    
    def detect_shell(self) -> str:
        """Detect the current shell."""
        shell = os.environ.get('SHELL', '').split('/')[-1]
        
        if not shell:
            # Try to detect PowerShell on Windows
            if os.name == 'nt':
                return 'powershell'
        
        return shell if shell in self.supported_shells else 'bash'
    
    def install_completion(self, shell: str = None, force: bool = False) -> Tuple[bool, str]:
        """
        Install shell completion.
        
        Args:
            shell: Target shell (auto-detect if None)
            force: Force installation even if already exists
            
        Returns:
            Tuple of (success, message)
        """
        if shell is None:
            shell = self.detect_shell()
        
        if shell not in self.supported_shells:
            return False, f"Unsupported shell: {shell}"
        
        try:
            instructions = install_shell_completion(shell)
            return True, instructions
        except Exception as e:
            return False, f"Failed to install completion: {e}"
    
    def generate_script(self, shell: str) -> Tuple[bool, str]:
        """
        Generate completion script for a shell.
        
        Args:
            shell: Target shell
            
        Returns:
            Tuple of (success, script_content)
        """
        if shell not in self.supported_shells:
            return False, f"Unsupported shell: {shell}"
        
        try:
            script = get_completion_script(shell)
            return True, script
        except Exception as e:
            return False, f"Failed to generate script: {e}"
    
    def get_completion_status(self) -> dict:
        """
        Get completion installation status.
        
        Returns:
            Dictionary with completion status information
        """
        shell = self.detect_shell()
        
        status = {
            'current_shell': shell,
            'supported_shells': self.supported_shells,
            'completion_available': shell in self.supported_shells,
            'installation_instructions': install_shell_completion(shell)
        }
        
        return status