import PyInstaller.__main__
import sys
from pathlib import Path
import ttkbootstrap
import PIL
import warnings

# Suppress warnings
warnings.filterwarnings("ignore", category=SyntaxWarning)
warnings.filterwarnings("ignore", category=DeprecationWarning)

def build_exe():
    # Get package locations
    ttkbootstrap_path = Path(ttkbootstrap.__file__).parent
    pil_path = Path(PIL.__file__).parent
    
    PyInstaller.__main__.run([
        'gui_organizer.py',
        '--name=AI_File_Organizer',
        '--onefile',
        '--noconsole',
        '--clean',
        '--windowed',
        # Exclude unnecessary modules
        '--exclude-module=matplotlib',
        '--exclude-module=numpy',
        '--exclude-module=pandas',
        '--exclude-module=scipy',
        '--exclude-module=PyQt5',
        '--exclude-module=pyqt5',
        '--exclude-module=cv2',
        '--exclude-module=unittest',
        '--exclude-module=test',
        '--exclude-module=setuptools',
        '--exclude-module=pkg_resources',
        # Add required data files
        f'--add-data={ttkbootstrap_path};ttkbootstrap',
        f'--add-data={pil_path};PIL',
        # Required imports
        '--hidden-import=PIL._tkinter_finder',
        '--hidden-import=PIL',
        '--hidden-import=tkinter',
        '--hidden-import=tkinter.ttk',
        '--collect-submodules=ttkbootstrap',
        '--collect-submodules=PIL',
        # Build options
        '--noupx',
        '--log-level=ERROR',  # Changed from WARN to ERROR
        # Additional options to suppress warnings
        '--disable-windowed-traceback',
        # Add runtime hooks to suppress warnings
        '--runtime-hook=runtime_hook.py'
    ])

if __name__ == "__main__":
    build_exe()
