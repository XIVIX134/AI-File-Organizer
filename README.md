
# AI File Organizer

A powerful desktop application that uses AI to intelligently organize your files with a modern, user-friendly interface.

## Features

- 🤖 AI-powered file organization suggestions
- 🎨 Modern dark-themed GUI interface
- 📁 Smart file type detection and categorization
- ↩️ Undo functionality for safe file operations
- 🔄 Real-time modification of suggestions
- ⚙️ Persistent settings storage
- 🌐 Support for multiple AI providers

## Installation

### Option 1: Download Executable
1. Download the latest release from the Releases page
2. Run the `AI_File_Organizer.exe` directly - no installation needed

### Option 2: Run from Source
1. Clone the repository
2. Install requirements:
   ```bash
   pip install -r requirements.txt
   ```
3. Run the application:
   ```bash
   python gui_organizer.py
   ```

## Configuration

1. Click the ⚙️ settings button
2. Enter your API credentials:
   - API Key: Your authentication key
   - Endpoint: Your API endpoint URL
   - Model Name: Your preferred model
3. Settings are automatically saved in your user directory

## Usage

1. Launch the application
2. Click "Browse" to select a directory
3. Click "Generate Organization Suggestion" to get AI recommendations
4. Review the suggested changes in the preview
5. Use "Modify Suggestion" to refine the organization
6. Click "Apply Changes" to execute the organization

![AI_File_Organizer_p6RsbKNmQe](https://github.com/user-attachments/assets/3f2bfa65-4214-4d89-8ca8-6eddec1ff54c)

## Requirements

- Windows/Linux/MacOS
- Python 3.6+ (for source)
- OpenAI-compatible API access
- Required packages:
  ```
  ttkbootstrap
  requests
  openai
  pillow
  ```

## Notes

- Settings are stored in `~/.file_organizer_config.json`
- All operations can be undone
- Supports any OpenAI-compatible API endpoint

## Contributing

Pull requests are welcome! For major changes, please open an issue first.
