import os
import random
from pathlib import Path
import string
import PIL.Image
import numpy as np
from datetime import datetime, timedelta

class TestFileGenerator:
    def __init__(self, target_folder: str):
        self.target_folder = Path(target_folder)
        self.file_types = {
            'image': ['.jpg', '.png', '.gif', '.bmp'],
            'document': ['.txt', '.pdf', '.doc', '.docx'],
            'other': ['.zip', '.exe', '.lnk']
        }
        self.words = ['project', 'document', 'report', 'image', 'photo', 'screenshot', 
                     'backup', 'presentation', 'meeting', 'notes', 'draft', 'final']

    def generate_random_name(self) -> str:
        """Generate a random filename using common patterns"""
        patterns = [
            f"{random.choice(self.words)}_{datetime.now().strftime('%Y%m%d')}",
            f"IMG_{random.randint(1000, 9999)}",
            f"doc_{random.choice(self.words)}_{random.randint(1, 100)}",
            ''.join(random.choices(string.ascii_lowercase, k=random.randint(5, 10))),
            f"{datetime.now() - timedelta(days=random.randint(0, 365)):%Y-%m-%d}_{random.choice(self.words)}"
        ]
        return random.choice(patterns)

    def create_random_image(self, path: Path) -> None:
        """Create a random image file"""
        width = random.randint(100, 1000)
        height = random.randint(100, 1000)
        # Create random color array
        array = np.random.rand(height, width, 3) * 255
        image = PIL.Image.fromarray(array.astype('uint8'))
        image.save(path)

    def create_random_document(self, path: Path) -> None:
        """Create a random document file"""
        content_patterns = [
            f"This is a test document created on {datetime.now()}",
            "Lorem ipsum dolor sit amet, consectetur adipiscing elit.",
            f"Project notes for {random.choice(self.words)}",
            f"Meeting minutes from {datetime.now() - timedelta(days=random.randint(0, 30)):%Y-%m-%d}",
            "TODO: Complete this document"
        ]
        
        content = random.choice(content_patterns)
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)

    def generate_files(self, num_files: int = None) -> None:
        """Generate random test files"""
        if num_files is None:
            num_files = random.randint(5, 20)

        # Create target folder if it doesn't exist
        self.target_folder.mkdir(parents=True, exist_ok=True)

        print(f"Generating {num_files} random files in {self.target_folder}")

        for _ in range(num_files):
            # Choose random file type and extension
            file_type = random.choice(list(self.file_types.keys()))
            extension = random.choice(self.file_types[file_type])
            
            # Generate unique filename
            while True:
                filename = self.generate_random_name() + extension
                file_path = self.target_folder / filename
                if not file_path.exists():
                    break

            try:
                if file_type == 'image':
                    self.create_random_image(file_path)
                elif file_type == 'document':
                    self.create_random_document(file_path)
                else:
                    # For other files, just create empty files
                    file_path.touch()
                
                print(f"Created: {filename}")
                
            except Exception as e:
                print(f"Error creating {filename}: {str(e)}")

def main():
    # Get target folder from user
    while True:
        folder = input("Enter target folder path (or press Enter for current directory): ").strip()
        if not folder:
            folder = os.getcwd()
        
        if os.path.exists(folder):
            break
        print("Invalid folder path. Please try again.")

    # Get number of files
    while True:
        try:
            num_input = input("Enter number of files to generate (or press Enter for random): ").strip()
            num_files = int(num_input) if num_input else None
            if num_files is None or num_files > 0:
                break
            print("Please enter a positive number.")
        except ValueError:
            if not num_input:
                break
            print("Please enter a valid number.")

    # Generate files
    generator = TestFileGenerator(folder)
    generator.generate_files(num_files)

if __name__ == "__main__":
    main()
