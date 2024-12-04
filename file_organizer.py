import json
import os
import shutil
from pathlib import Path
from typing import Dict, List
import logging
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FileScanner:
    def __init__(self, base_path: Path):
        self.base_path = base_path
        self.file_types = {
            'image': ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp'],
            'video': ['.mp4', '.avi', '.mov', '.wmv', '.flv', '.mkv', '.webm'],
            'document': ['.pdf', '.doc', '.docx', '.txt', '.rtf', '.odt', '.xlsx', '.pptx'],
            'shortcut': ['.lnk', '.url'],
            'audio': ['.mp3', '.wav', '.ogg', '.m4a', '.flac'],
            'archive': ['.zip', '.rar', '.7z', '.tar', '.gz'],
            'application': ['.exe', '.msi', '.app', '.dmg', '.pkg']  # Added application types
        }

    def get_file_category(self, file_path: Path) -> str:
        if not file_path.suffix:
            return "unknown"
        
        suffix = file_path.suffix.lower()
        for category, extensions in self.file_types.items():
            if suffix in extensions:
                return category
        return "other"

    def scan(self) -> List[Dict]:
        """Scan directory and return file information (only parent directory)"""
        files_data = []
        try:
            for item in self.base_path.iterdir():
                if item.is_file():
                    files_data.append({
                        "path": str(item.relative_to(self.base_path)),
                        "type": item.suffix[1:] if item.suffix else "unknown",
                        "category": self.get_file_category(item),
                        "is_folder": False
                    })
                else:
                    files_data.append({
                        "path": str(item.relative_to(self.base_path)),
                        "type": "folder",
                        "category": "folder",
                        "is_folder": True
                    })
        except Exception as e:
            logger.error(f"Scanning error: {str(e)}")
            raise
        return files_data

class AIOrganizer:
    def __init__(self, model: str = None):
        self.client = OpenAI(
            api_key=os.getenv('API_KEY'),
            base_url=os.getenv('ENDPOINT')
        )
        self.model = model or os.getenv('MODEL_NAME')
        self.max_chunk_size = 1000000  # 1MB chunks for processing

    def clean_response(self, response: str) -> str:
        """Clean and validate the AI response"""
        try:
            # Remove any markdown formatting
            cleaned = response.replace('```json', '').replace('```', '').strip()
            cleaned = cleaned.strip('" \n\t')
            
            # Process in chunks if response is too large
            if len(cleaned) > self.max_chunk_size:
                logger.warning(f"Large response detected ({len(cleaned)} bytes), processing in chunks")
                return self.process_large_response(cleaned)
            
            # Find the last complete JSON object
            depth = 0
            last_complete = 0
            for i, char in enumerate(cleaned):
                if char == '{':
                    depth += 1
                elif char == '}':
                    depth -= 1
                    if depth == 0:
                        last_complete = i + 1
            
            if last_complete > 0:
                cleaned = cleaned[:last_complete]
            
            return cleaned
        except Exception as e:
            logger.error(f"Error cleaning response: {str(e)}")
            return "{}"

    def process_large_response(self, response: str) -> str:
        """Process large JSON responses in chunks"""
        try:
            # Find the outermost JSON object
            start_idx = response.find('{')
            if start_idx == -1:
                return "{}"
            
            depth = 0
            for i, char in enumerate(response[start_idx:], start_idx):
                if char == '{':
                    depth += 1
                elif char == '}':
                    depth -= 1
                    if depth == 0:
                        return response[start_idx:i + 1]
            
            return "{}"
        except Exception as e:
            logger.error(f"Error processing large response: {str(e)}")
            return "{}"

    def create_fallback_suggestion(self, files_data: List[Dict]) -> Dict:
        """Create a basic organization suggestion based on file types"""
        suggestion = {}
        for file in files_data:
            if file['is_folder']:
                continue
                
            category = file['category'].lower()
            if category not in suggestion:
                suggestion[category] = []
                
            suggestion[category].append({
                'original_path': file['path'],
                'new_path': f"{category}/{file['path']}"
            })
        
        return suggestion

    def process_suggestion(self, response_text: str, files_data: List[Dict]) -> Dict:
        """Process and validate the AI suggestion with fallback"""
        try:
            cleaned_result = self.clean_response(response_text)
            try:
                parsed_result = json.loads(cleaned_result)
            except json.JSONDecodeError:
                logger.warning("Failed to parse AI response, using fallback organization")
                return self.create_fallback_suggestion(files_data)
            
            # Validate the structure
            if not isinstance(parsed_result, dict):
                return self.create_fallback_suggestion(files_data)
                
            # Ensure all entries have required fields
            validated_result = {}
            for category, items in parsed_result.items():
                if isinstance(items, list):
                    valid_items = []
                    for item in items:
                        if isinstance(item, dict) and 'original_path' in item and 'new_path' in item:
                            valid_items.append(item)
                    if valid_items:
                        validated_result[category] = valid_items
            
            return validated_result if validated_result else self.create_fallback_suggestion(files_data)
            
        except Exception as e:
            logger.error(f"Processing error: {str(e)}")
            return self.create_fallback_suggestion(files_data)

    def get_suggestion(self, files_data: List[Dict]) -> Dict:
        try:
            prompt = """Analyze these files and create an organized folder structure.
            Files: {files}
            
            Return a JSON object with categories as keys and arrays of file movements as values.
            Each file movement should include 'original_path' and 'new_path'.
            IMPORTANT: Always include both the folder and filename in the new_path.
            
            Example format:
            {{
                "documents": [
                    {{"original_path": "file1.txt", "new_path": "documents/file1.txt"}},
                    {{"original_path": "file2.txt", "new_path": "documents/subfolder/file2.txt"}}
                ],
                "images": [
                    {{"original_path": "pic.jpg", "new_path": "images/pic.jpg"}}
                ]
            }}""".format(files=json.dumps([f['path'] for f in files_data], indent=2))

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system", 
                        "content": "You are a file organization assistant. Respond with clean JSON only."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.2
            )

            result = response.choices[0].message.content
            return self.process_suggestion(result, files_data)

        except Exception as e:
            logger.error(f"AI API error: {str(e)}")
            return self.create_fallback_suggestion(files_data)

    def get_modified_suggestion(self, files_data: List[Dict], previous_suggestion: Dict, user_feedback: str) -> Dict:
        try:
            prompt = f"""I need you to reorganize these files differently based on user feedback.

Previous organization that needs modification:
{json.dumps(previous_suggestion, indent=2)}

Files to organize:
{json.dumps([f['path'] for f in files_data], indent=2)}

User requested changes:
{user_feedback}

Important instructions:
1. Create a NEW organization scheme that incorporates the user's feedback
2. Do NOT just return the previous suggestion
3. Ensure all new paths include both folder and filename
4. Return ONLY valid JSON in this format:
{{
    "category1": [
        {{"original_path": "file1.txt", "new_path": "category1/file1.txt"}}
    ],
    "category2": [
        {{"original_path": "file2.jpg", "new_path": "category2/file2.jpg"}}
    ]
}}"""

            logger.info("Sending modified suggestion request to AI")
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a file organization assistant. You must create a new organization scheme based on user feedback. Never return the same suggestion twice."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.7  # Increased temperature for more variation
            )

            result = response.choices[0].message.content
            logger.info(f"Received modified suggestion from AI: {result[:200]}...")  # Log first 200 chars
            
            processed_result = self.process_suggestion(result, files_data)
            
            # Verify the suggestion is different from the previous one
            if processed_result == previous_suggestion:
                logger.warning("AI returned same suggestion, generating alternative")
                return self.create_fallback_suggestion(files_data)
                
            return processed_result

        except Exception as e:
            logger.error(f"AI API error in modified suggestion: {str(e)}")
            return self.create_fallback_suggestion(files_data)

class FileOrganizer:
    def __init__(self, base_path: Path):
        self.base_path = base_path
        self.move_history = []  # Store move operations for undo

    def normalize_path(self, path_str: str) -> str:
        """Ensure path includes both folder and filename"""
        path = Path(path_str)
        if not path.suffix:  # If no file extension, assume it's missing filename
            return str(path / path.parts[-1])  # Append original filename
        return path_str

    def move_files(self, organization: Dict) -> bool:
        """Execute file movement based on suggestion"""
        try:
            moved_files = []
            current_batch = []  # Track current batch of moves
            
            for category, items in organization.items():
                for item in items:
                    if not isinstance(item, dict) or 'original_path' not in item or 'new_path' not in item:
                        logger.error(f"Invalid item format: {item}")
                        continue

                    old_path = self.base_path / item['original_path']
                    new_path = self.base_path / self.normalize_path(item['new_path'])
                    
                    if str(old_path) in moved_files:
                        logger.warning(f"File already moved: {old_path}")
                        continue

                    # Create parent directories if they don't exist
                    new_path.parent.mkdir(exist_ok=True, parents=True)
                    
                    if old_path.exists():
                        shutil.move(str(old_path), str(new_path))
                        moved_files.append(str(old_path))
                        current_batch.append({
                            'from': str(old_path),
                            'to': str(new_path)
                        })
                        logger.info(f"Moved {old_path} to {new_path}")
                    else:
                        logger.warning(f"File not found: {old_path}")
            
            if current_batch:
                self.move_history.append(current_batch)
            return True
            
        except Exception as e:
            logger.error(f"File movement error: {str(e)}")
            return False

    def remove_empty_folders(self, path: Path) -> None:
        """Recursively remove empty folders from deepest level up"""
        try:
            # Get all subfolders
            folders = [x for x in Path(path).glob('**/*') if x.is_dir()]
            
            # Sort by depth (deepest first)
            folders.sort(key=lambda x: len(x.parts), reverse=True)
            
            # Try to remove each folder
            for folder in folders:
                try:
                    if folder.exists() and not any(folder.iterdir()):
                        folder.rmdir()
                        logger.info(f"Removed empty folder: {folder}")
                except Exception as e:
                    logger.warning(f"Could not remove folder {folder}: {e}")
            
            # Finally try to remove the root folder if it's empty
            try:
                if path.exists() and not any(path.iterdir()):
                    path.rmdir()
                    logger.info(f"Removed empty root folder: {path}")
            except Exception as e:
                logger.warning(f"Could not remove root folder {path}: {e}")
                
        except Exception as e:
            logger.error(f"Error in remove_empty_folders: {str(e)}")

    def get_created_folders(self, moves: list) -> set:
        """Get all folders that were created during the moves"""
        folders = set()
        for move in moves:
            path = Path(move['to'])
            while path != self.base_path:
                folders.add(path.parent)
                path = path.parent
        return folders

    def undo_last_move(self) -> bool:
        """Undo the last batch of file movements and clean up empty folders"""
        try:
            if not self.move_history:
                logger.info("No moves to undo")
                return False

            last_moves = self.move_history.pop()
            
            # Get all folders that were created
            created_folders = self.get_created_folders(last_moves)
            
            # First move all files back
            for move in reversed(last_moves):
                old_path = Path(move['to'])
                new_path = Path(move['from'])
                
                if old_path.exists():
                    # Ensure parent directory exists
                    new_path.parent.mkdir(parents=True, exist_ok=True)
                    shutil.move(str(old_path), str(new_path))
                    logger.info(f"Undid move: {old_path} back to {new_path}")
                else:
                    logger.error(f"Cannot undo - file not found: {old_path}")
                    return False
            
            # Clean up each created folder
            for folder in sorted(created_folders, key=lambda x: len(str(x)), reverse=True):
                self.remove_empty_folders(folder)

            return True
            
        except Exception as e:
            logger.error(f"Undo error: {str(e)}")
            return False

def get_user_confirmation(prompt: str) -> bool:
    """Get user confirmation with Y/N prompt"""
    while True:
        response = input(f"{prompt} (Y/N): ").lower()
        if response in ['y', 'n']:
            return response == 'y'
        print("Please enter Y or N")

def organize():
    """Interactive file organization script"""
    try:
        # Get path from user
        folder_path = input("Enter the folder path to organize: ").strip()
        base_path = Path(folder_path)
        
        if not base_path.exists() or not base_path.is_dir():
            print("Invalid directory path!")
            return

        # Scan directory
        scanner = FileScanner(base_path)
        files_data = scanner.scan()
        
        if not files_data:
            print("No files found in the specified directory.")
            return

        # Show files and get confirmation
        print("\nFiles and folders in the directory:")
        for item in files_data:
            type_str = f"[{item['category'].upper()}]"
            print(f"{type_str:12} {item['path']}")
        
        if not get_user_confirmation("\nDo you want to organize these files?"):
            print("Operation cancelled.")
            return

        # Get AI suggestion
        print("\nGenerating organization suggestion...")
        organizer = AIOrganizer()
        suggestion = organizer.get_suggestion(files_data)
        
        file_organizer = FileOrganizer(base_path)
        while True:
            # Show suggestion
            print("\nSuggested organization:")
            print(json.dumps(suggestion, indent=2))
            
            print("\nOptions:")
            print("1. Apply changes")
            print("2. Modify suggestion")
            print("3. Undo last change")
            print("4. Cancel")
            
            choice = input("\nEnter your choice (1-4): ").strip()
            
            if choice == '1':
                if file_organizer.move_files(suggestion):
                    print("Files organized successfully!")
                    break
            elif choice == '2':
                feedback = input("\nPlease describe how you'd like to modify the organization:\n")
                print("\nGenerating new suggestion based on your feedback...")
                suggestion = organizer.get_modified_suggestion(files_data, suggestion, feedback)
            elif choice == '3':
                if file_organizer.undo_last_move():
                    print("Last change undone successfully!")
                    # Refresh files_data after undo
                    files_data = scanner.scan()
                    suggestion = organizer.get_suggestion(files_data)
                else:
                    print("No changes to undo or undo failed")
            elif choice == '4':
                print("Operation cancelled.")
                break
            else:
                print("Invalid choice, please try again")

    except Exception as e:
        logger.error(f"Error: {str(e)}")
        print(f"An error occurred: {str(e)}")

if __name__ == '__main__':
    organize()