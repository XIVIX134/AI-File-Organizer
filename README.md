# AI-Powered File Organizer

An intelligent file organization tool that uses AI to automatically suggest and implement logical folder structures for your files. This script analyzes your files and provides smart organization suggestions while maintaining a complete history of changes for easy undoing.

## Features

- AI-powered file organization suggestions
- Interactive command-line interface
- Intelligent file type categorization
- Safe file movement with undo capability
- Customizable organization through user feedback
- Robust error handling and logging
- Fallback mechanisms for reliability

## Prerequisites

- Python 3.6 or higher
- OpenAI API access
- Required Python packages (install via pip):
  ```
  openai
  python-dotenv
  ```

## Installation

1. Clone the repository:
   ```bash
   git clone [repository-url]
   cd [repository-name]
   ```

2. Install required packages:
   ```bash
   pip install -r requirements.txt
   ```

3. Create a `.env` file in the project root with your API credentials:
   ```
   API_KEY=your_openai_api_key
   ENDPOINT=your_api_endpoint
   MODEL_NAME=your_preferred_model
   ```

## Usage

Run the script from the command line:
```bash
python file_organizer.py
```

The script will:
1. Prompt for the directory path you want to organize
2. Display all files and folders in the specified directory
3. Generate an AI-powered organization suggestion
4. Provide options to:
   - Apply the suggested changes
   - Modify the suggestion based on your feedback
   - Undo the last set of changes
   - Cancel the operation

## Error Handling

The script includes comprehensive error handling and logging:
- All operations are logged for debugging
- Failed operations are safely rolled back
- Fallback mechanisms ensure reliability
- Clear error messages for user feedback

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request. For major changes, please open an issue first to discuss what you would like to change.