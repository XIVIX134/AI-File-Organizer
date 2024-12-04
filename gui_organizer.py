import tkinter as tk
from ttkbootstrap import Style, ttk
from tkinter import filedialog, messagebox
from pathlib import Path
import json
from file_organizer import FileScanner, AIOrganizer, FileOrganizer
import threading
import queue
import os
import requests
import sys

# Add this at the top of the file to hide terminal
if sys.platform.startswith('win'):
    import ctypes
    ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 0)

class FileOrganizerGUI:
    def __init__(self, root):
        self.style = Style(theme='darkly')  # Use modern dark theme
        self.root = root
        self.root.title("AI File Organizer")
        self.root.geometry("1000x700")  # Larger default size
        
        # Initialize components
        self.base_path = None
        self.files_data = None
        self.current_suggestion = None
        self.file_organizer = None
        self.message_queue = queue.Queue()
        self.apply_button = None
        self.undo_button = None
        self.generate_button = None
        self.file_tree = None
        self.preview_tree = None
        # Change config file location to user's home directory
        self.config_file = Path.home() / '.file_organizer_config.json'
        self.load_config()
        
        self.setup_styles()
        self.create_widgets()
        self.check_messages()

    def setup_styles(self):
        # Configure custom styles
        self.style.configure('Primary.TButton', font=('Segoe UI', 10))
        self.style.configure('Success.TButton', font=('Segoe UI', 10))
        self.style.configure('Warning.TButton', font=('Segoe UI', 10))
        self.style.configure('FileList.TFrame', padding=10)
        self.style.configure('Header.TLabel', font=('Segoe UI', 12, 'bold'))
        self.style.configure(
            'Generate.TButton',
            font=('Segoe UI', 12, 'bold'),
            background='#28a745',
            foreground='white'
        )
        # Add TreeView styles
        self.style.configure('Treeview', 
                           background='#2b2b2b',
                           foreground='white',
                           fieldbackground='#2b2b2b')
        self.style.configure('Treeview.Heading',
                           background='#1e1e1e',
                           foreground='white',
                           relief='flat')
        self.style.map('Treeview',
                      background=[('selected', '#404040')],
                      foreground=[('selected', 'white')])

    def create_widgets(self):
        # Main container with padding
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.grid(row=0, column=0, sticky="nsew")

        # Header
        header_frame = ttk.Frame(main_frame)
        header_frame.grid(row=0, column=0, columnspan=2, pady=(0, 20))
        
        header = ttk.Label(header_frame, text="AI File Organizer", style='Header.TLabel')
        header.pack(side=tk.LEFT, padx=(0, 10))
        
        settings_btn = ttk.Button(
            header_frame,
            text="⚙",
            style='Primary.TButton',
            command=self.show_settings_dialog,
            width=3
        )
        settings_btn.pack(side=tk.RIGHT)

        # Folder selection with improved styling
        folder_frame = ttk.LabelFrame(main_frame, text="Select Directory", padding="10")
        folder_frame.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(0, 20))
        
        self.folder_path = tk.StringVar()
        path_entry = ttk.Entry(folder_frame, textvariable=self.folder_path, width=50)
        path_entry.grid(row=0, column=0, sticky="ew", padx=(0, 10))
        
        browse_btn = ttk.Button(folder_frame, text="Browse", 
                              command=self.browse_folder, style='Primary.TButton')
        browse_btn.grid(row=0, column=1, padx=5)
        
        # Remove or comment out the scan button since it's no longer needed
        # scan_btn = ttk.Button(folder_frame, text="Scan Directory", 
        #                     command=self.scan_directory, style='Success.TButton')
        # scan_btn.grid(row=0, column=2, padx=5)

        # Replace file list with TreeView
        list_frame = ttk.LabelFrame(main_frame, text="Current Files", padding="10")
        list_frame.grid(row=2, column=0, sticky="nsew", pady=(0, 10), padx=(0, 10))
        
        # Create container frame for tree and scrollbar
        tree_container = ttk.Frame(list_frame)
        tree_container.pack(fill=tk.BOTH, expand=True)
        
        # Create scrollbar first
        list_scrollbar = ttk.Scrollbar(tree_container, orient="vertical")
        list_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Create file TreeView
        self.file_tree = ttk.Treeview(
            tree_container, 
            columns=('Type',), 
            height=20,
            yscrollcommand=list_scrollbar.set
        )
        self.file_tree.heading('#0', text='Name')  # Changed from 'File Path'
        self.file_tree.heading('Type', text='Category')
        self.file_tree.column('#0', width=300)  # Made wider for better visibility
        self.file_tree.column('Type', width=100)
        self.file_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Configure scrollbar
        list_scrollbar.config(command=self.file_tree.yview)

        # Replace suggestion display with TreeView
        suggestion_frame = ttk.LabelFrame(main_frame, text="Organization Preview", 
                                        padding="10")
        suggestion_frame.grid(row=2, column=1, sticky="nsew", pady=(0, 10))
        
        # Create container frame for preview tree
        preview_container = ttk.Frame(suggestion_frame)
        preview_container.pack(fill=tk.BOTH, expand=True)
        
        # Create scrollbar first
        preview_scrollbar = ttk.Scrollbar(preview_container, orient="vertical")
        preview_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Create preview TreeView
        self.preview_tree = ttk.Treeview(
            preview_container,
            columns=('Action',),
            height=20,
            yscrollcommand=preview_scrollbar.set
        )
        self.preview_tree.heading('#0', text='Name')  # Changed from 'New Location'
        self.preview_tree.heading('Action', text='Action')
        self.preview_tree.column('#0', width=400)  # Made wider for better visibility
        self.preview_tree.column('Action', width=80)
        self.preview_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Configure scrollbar
        preview_scrollbar.config(command=self.preview_tree.yview)

        # Generate button (large and green)
        generate_frame = ttk.Frame(main_frame)
        generate_frame.grid(row=3, column=0, columnspan=2, sticky="ew", pady=10)
        
        self.generate_button = ttk.Button(
            generate_frame,
            text="🤖 Generate Organization Suggestion",
            style='Generate.TButton',
            command=self.generate_suggestion
        )
        self.generate_button.pack(fill=tk.X, pady=5, ipady=10)  # Make button taller

        # Buttons frame with improved styling
        btn_frame = ttk.Frame(main_frame)
        btn_frame.grid(row=4, column=0, columnspan=2, sticky="ew", pady=10)
        
        self.apply_button = ttk.Button(
            btn_frame,
            text="✓ Apply Changes",
            style='Success.TButton',
            command=self.apply_changes,
            state='disabled'
        )
        self.apply_button.pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            btn_frame,
            text="⚙ Modify Suggestion",
            style='Primary.TButton',
            command=self.show_modify_dialog
        ).pack(side=tk.LEFT, padx=5)
        
        self.undo_button = ttk.Button(
            btn_frame,
            text="↺ Undo Last Change",
            style='Warning.TButton',
            command=self.undo_changes,
            state='disabled'
        )
        self.undo_button.pack(side=tk.LEFT, padx=5)

        # Status bar with progress indication
        status_frame = ttk.Frame(main_frame)
        status_frame.grid(row=5, column=0, columnspan=2, sticky="ew", pady=(10, 0))
        
        self.progress = ttk.Progressbar(status_frame, mode='indeterminate')
        self.progress.pack(fill=tk.X, pady=(0, 5))
        
        self.status_var = tk.StringVar(value="Ready")
        status_bar = ttk.Label(status_frame, textvariable=self.status_var)
        status_bar.pack(fill=tk.X)

        # Configure grid weights
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)
        main_frame.grid_columnconfigure(0, weight=1)
        main_frame.grid_columnconfigure(1, weight=1)
        folder_frame.grid_columnconfigure(0, weight=1)

    def browse_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.folder_path.set(folder)
            self.scan_directory()  # Automatically start scanning the directory

    def scan_directory(self):
        path = self.folder_path.get()
        if not path:
            messagebox.showerror("Error", "Please select a directory first")
            return

        self.base_path = Path(path)
        if not self.base_path.exists():
            messagebox.showerror("Error", "Selected directory does not exist")
            return

        self.status_var.set("Scanning directory...")
        self.root.update()

        def scan_task():
            try:
                scanner = FileScanner(self.base_path)
                self.files_data = scanner.scan()
                self.message_queue.put(("scan_complete", None))
            except Exception as e:
                self.message_queue.put(("error", str(e)))

        self.progress.start()
        self.status_var.set("Scanning directory...")
        threading.Thread(target=scan_task, daemon=True).start()

    def check_messages(self):
        try:
            while True:
                message, data = self.message_queue.get_nowait()
                if message in ["scan_complete", "suggestion_complete"]:
                    self.progress.stop()
                if message == "scan_complete":
                    self.update_file_list()
                    self.generate_button.configure(state='normal')
                elif message == "suggestion_complete":
                    # Ensure UI updates happen in the main thread
                    self.root.after(0, self.update_suggestion_display)
                    self.root.after(0, lambda: self.apply_button.configure(state='normal'))
                    self.root.after(0, lambda: self.generate_button.configure(state='normal'))
                elif message == "success":
                    self.undo_button.configure(state='normal')
                elif message == "error":
                    messagebox.showerror("Error", data)
                    self.generate_button.configure(state='normal')
                self.status_var.set("Ready")
        except queue.Empty:
            pass
        finally:
            self.root.after(100, self.check_messages)

    def update_file_list(self):
        """Update the file TreeView with current files"""
        self.file_tree.delete(*self.file_tree.get_children())
        
        # Group files by category
        categories = {}
        for item in self.files_data:
            category = item['category'].upper()
            if category not in categories:
                categories[category] = []
            categories[category].append(item)
        
        # Add items to tree with just filenames
        for category, items in categories.items():
            category_node = self.file_tree.insert('', 'end', text=category, 
                                                values=('', ), 
                                                tags=('category',))
            for item in items:
                filename = Path(item['path']).name  # Get just the filename
                self.file_tree.insert(category_node, 'end', 
                                    text=filename,
                                    values=(item['type'],),
                                    tags=('file',))
            # Auto expand category
            self.file_tree.item(category_node, open=True)
        
        # Configure tag appearance
        self.file_tree.tag_configure('category', 
                                   font=('Segoe UI', 10, 'bold'),
                                   background='#1e1e1e')
        self.file_tree.tag_configure('file', 
                                   font=('Segoe UI', 9))

    def update_suggestion_display(self):
        """Update the preview TreeView with suggested changes"""
        self.preview_tree.delete(*self.preview_tree.get_children())
        if not self.current_suggestion:
            return
            
        # Group by target folders
        folders = {}
        for category, items in self.current_suggestion.items():
            for item in items:
                folder = str(Path(item['new_path']).parent)
                if folder not in folders:
                    folders[folder] = []
                folders[folder].append({
                    'name': Path(item['new_path']).name  # Store just the filename
                })
        
        # Add items to tree with just filenames
        for folder, items in folders.items():
            folder_node = self.preview_tree.insert('', 'end', text=folder,
                                                 values=('',), 
                                                 tags=('folder',))
            for item in items:
                self.preview_tree.insert(folder_node, 'end',
                                       text=item['name'],
                                       values=('→ Move',),
                                       tags=('move',))
        
        # Configure tag appearance
        self.preview_tree.tag_configure('folder', 
                                      font=('Segoe UI', 10, 'bold'),
                                      background='#1e1e1e')
        self.preview_tree.tag_configure('move',
                                      font=('Segoe UI', 9))
        
        # Expand all folders
        for item in self.preview_tree.get_children():
            self.preview_tree.item(item, open=True)

    def apply_changes(self):
        if not self.current_suggestion or not self.base_path:
            messagebox.showerror("Error", "No organization suggestion available")
            return

        if not self.file_organizer:
            self.file_organizer = FileOrganizer(self.base_path)

        if messagebox.askyesno("Confirm", "Apply the suggested organization?"):
            self.status_var.set("Applying changes...")
            self.root.update()

            def apply_task():
                try:
                    success = self.file_organizer.move_files(self.current_suggestion)
                    self.message_queue.put(
                        ("success", "Files organized successfully!") if success 
                        else ("error", "Failed to organize files")
                    )
                except Exception as e:
                    self.message_queue.put(("error", str(e)))

            threading.Thread(target=apply_task, daemon=True).start()

    def show_modify_dialog(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("Modify Organization")
        dialog.geometry("500x400")
        dialog.transient(self.root)
        dialog.grab_set()
        
        frame = ttk.Frame(dialog, padding="20")
        frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(frame, text="Describe how you'd like to modify the organization:",
                 style='Header.TLabel').pack(pady=(0, 10))
        
        feedback = tk.Text(frame, height=10, font=('Segoe UI', 10),
                          bg='#2b2b2b', fg='white')
        feedback.pack(fill=tk.BOTH, expand=True, pady=(0, 20))
        
        btn_frame = ttk.Frame(frame)
        btn_frame.pack(fill=tk.X)
        
        ttk.Button(btn_frame, text="Submit", style='Success.TButton',
                  command=lambda: self.submit_modification(dialog, feedback)).pack(side=tk.RIGHT, padx=5)
        ttk.Button(btn_frame, text="Cancel", style='Warning.TButton',
                  command=dialog.destroy).pack(side=tk.RIGHT, padx=5)

    def submit_modification(self, dialog, feedback):
        feedback_text = feedback.get(1.0, tk.END).strip()
        if feedback_text:
            self.modify_suggestion(feedback_text)
            dialog.destroy()

    def modify_suggestion(self, feedback):
        """Generate new suggestion based on feedback"""
        self.status_var.set("Generating new suggestion...")
        self.progress.start()
        self.generate_button.configure(state='disabled')
        self.apply_button.configure(state='disabled')
        self.root.update()

        def modify_task():
            try:
                organizer = AIOrganizer()
                # Store the new suggestion in a temporary variable
                new_suggestion = organizer.get_modified_suggestion(
                    self.files_data, 
                    self.current_suggestion, 
                    feedback
                )
                
                # Only update if we got a valid new suggestion
                if new_suggestion and isinstance(new_suggestion, dict):
                    self.current_suggestion = new_suggestion
                    self.message_queue.put(("suggestion_complete", None))
                else:
                    self.message_queue.put(("error", "Failed to generate modified suggestion"))
            except Exception as e:
                self.message_queue.put(("error", str(e)))

        # Run the modification task in a thread
        thread = threading.Thread(target=modify_task, daemon=True)
        thread.start()

    def undo_changes(self):
        if not self.file_organizer:
            messagebox.showerror("Error", "No changes to undo")
            return

        if messagebox.askyesno("Confirm", "Undo the last organization change?"):
            success = self.file_organizer.undo_last_move()
            if success:
                messagebox.showinfo("Success", "Last change undone successfully!")
                self.scan_directory()  # Refresh the display
            else:
                messagebox.showerror("Error", "Failed to undo changes")

    def generate_suggestion(self):
        """Generate organization suggestion for scanned files"""
        if not self.files_data:
            messagebox.showerror("Error", "Please scan a directory first")
            return

        # More thorough API settings check
        if not all([
            os.getenv('API_KEY'),
            os.getenv('ENDPOINT'),
            os.getenv('MODEL_NAME')
        ]):
            messagebox.showerror(
                "Error",
                "API settings are not configured.\nPlease configure them in Settings."
            )
            self.show_settings_dialog()
            return
            
        # Test API connection before proceeding
        success, message = self.test_api_connection(
            os.getenv('API_KEY'),
            os.getenv('ENDPOINT'),
            os.getenv('MODEL_NAME')
        )
        if not success:
            messagebox.showerror("API Error", message)
            self.show_settings_dialog()
            return

        self.status_var.set("Generating suggestion...")
        self.progress.start()
        self.generate_button.configure(state='disabled')

        def generate_task():
            try:
                organizer = AIOrganizer()
                self.current_suggestion = organizer.get_suggestion(self.files_data)
                self.message_queue.put(("suggestion_complete", None))
            except Exception as e:
                self.message_queue.put(("error", str(e)))

        threading.Thread(target=generate_task, daemon=True).start()

    def test_api_connection(self, api_key: str, endpoint: str, model_name: str) -> tuple[bool, str]:
        """Test if the API connection works with given credentials"""
        if not api_key or not endpoint or not model_name:
            return False, "All fields (API Key, Endpoint, Model Name) are required"
            
        try:
            headers = {
                'Authorization': f'Bearer {api_key}',
                'Content-Type': 'application/json'
            }
            
            # Clean and format the endpoint URL
            endpoint = endpoint.rstrip('/')
            url = f"{endpoint}/chat/completions"
            
            test_payload = {
                'messages': [
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": "Say hello"}
                ],
                'model': model_name,
                'max_tokens': 20,
                'temperature': 0.7
            }
            
            # Try an actual API call
            response = requests.post(
                url,
                headers=headers,
                json=test_payload,
                timeout=15
            )
            
            if response.status_code == 200:
                return True, "Connection successful"
            elif response.status_code == 401:
                return False, "Authentication failed: Invalid API key"
            elif response.status_code == 404:
                return False, f"Resource not found: Please verify your endpoint URL\nURL: {url}"
            else:
                try:
                    error_data = response.json()
                    error_msg = error_data.get('error', {}).get('message', 'Unknown error')
                    return False, f"API Error: {error_msg}\nStatus code: {response.status_code}\nEndpoint: {url}"
                except:
                    return False, f"Error {response.status_code}: Could not parse error message"
                
        except requests.exceptions.RequestException as e:
            return False, f"Connection error: {str(e)}\nPlease verify your endpoint URL and internet connection"
        except Exception as e:
            return False, f"Unexpected error: {str(e)}\nPlease check your settings and try again"

    def save_settings(self, dialog, api_key: str, endpoint: str, model_name: str):
        """Save settings after validation"""
        self.status_var.set("Testing API connection...")
        self.root.update()

        success, message = self.test_api_connection(api_key, endpoint, model_name)
        if success:
            try:
                config = {
                    'API_KEY': api_key,
                    'ENDPOINT': endpoint.rstrip('/'),  # Remove trailing slash
                    'MODEL_NAME': model_name
                }
                with open(self.config_file, 'w') as f:
                    json.dump(config, f, indent=4)
                
                # Update environment variables
                os.environ['API_KEY'] = api_key
                os.environ['ENDPOINT'] = endpoint.rstrip('/')
                os.environ['MODEL_NAME'] = model_name
                
                messagebox.showinfo("Success", "Settings saved successfully!")
                dialog.destroy()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save settings: {e}")
        else:
            messagebox.showerror("API Connection Error", message)
        
        self.status_var.set("Ready")

    def load_config(self):
        """Load configuration from file"""
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                    os.environ['API_KEY'] = config.get('API_KEY', '')
                    os.environ['ENDPOINT'] = config.get('ENDPOINT', '')
                    os.environ['MODEL_NAME'] = config.get('MODEL_NAME', '')
            else:
                # Create empty config if it doesn't exist
                self.save_settings('', '', '')
        except Exception as e:
            print(f"Error loading config: {e}")  # Changed from logger to print

    def show_settings_dialog(self):
        """Show settings configuration dialog"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Settings")
        dialog.geometry("500x300")
        dialog.transient(self.root)
        dialog.grab_set()
        
        frame = ttk.Frame(dialog, padding="20")
        frame.pack(fill=tk.BOTH, expand=True)
        
        # API Key
        ttk.Label(frame, text="API Key:", style='Header.TLabel').pack(anchor=tk.W)
        api_key = ttk.Entry(frame, width=50)
        api_key.insert(0, os.getenv('API_KEY', ''))
        api_key.pack(fill=tk.X, pady=(0, 10))
        
        # Endpoint
        ttk.Label(frame, text="Endpoint:", style='Header.TLabel').pack(anchor=tk.W)
        endpoint = ttk.Entry(frame, width=50)
        endpoint.insert(0, os.getenv('ENDPOINT', ''))
        endpoint.pack(fill=tk.X, pady=(0, 10))
        
        # Model Name
        ttk.Label(frame, text="Model Name:", style='Header.TLabel').pack(anchor=tk.W)
        model_name = ttk.Entry(frame, width=50)
        model_name.insert(0, os.getenv('MODEL_NAME', ''))
        model_name.pack(fill=tk.X, pady=(0, 10))
        
        # Buttons
        btn_frame = ttk.Frame(frame)
        btn_frame.pack(fill=tk.X, pady=(20, 0))
        
        ttk.Button(
            btn_frame,
            text="Save",
            style='Success.TButton',
            command=lambda: self.save_settings(dialog, api_key.get(), endpoint.get(), model_name.get())
        ).pack(side=tk.RIGHT, padx=5)
        
        ttk.Button(
            btn_frame,
            text="Cancel",
            style='Warning.TButton',
            command=dialog.destroy
        ).pack(side=tk.RIGHT, padx=5)

def main():
    root = tk.Tk()
    app = FileOrganizerGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()

