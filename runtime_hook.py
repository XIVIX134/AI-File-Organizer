import warnings
import os
import sys

def suppress_startup_messages():
    # Suppress all warnings
    warnings.filterwarnings('ignore')
    
    # Disable pygame welcome message
    os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
    
    # Disable debug messages
    os.environ['PYDEVD_DISABLE_FILE_VALIDATION'] = "1"
    
    # Suppress specific ttkbootstrap warnings
    warnings.filterwarnings('ignore', category=SyntaxWarning)
    warnings.filterwarnings('ignore', category=DeprecationWarning)
    
    # Hide console in Windows
    if sys.platform.startswith('win'):
        import ctypes
        ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 0)
    
    # Disable frozen modules warning
    sys.frozen = True

# Run when the hook is loaded
suppress_startup_messages()
