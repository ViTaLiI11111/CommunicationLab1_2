from pathlib import Path
from .quiz import QuizSingleton

class FileWriter:
    def __init__(self, mode, filename):
        config = QuizSingleton()
        self.answers_dir = config.answers_dir
        Path(self.answers_dir).mkdir(parents=True, exist_ok=True)
        self.filename = filename
        self.mode = mode
        self.filepath = self.prepare_filename(filename)

    def write(self, message):
        try:
            with open(self.filepath, self.mode, encoding="utf-8") as f:
                f.write(message + "\n")
        except Exception as e:
            print(f"Error writing to file {self.filename}: {e}")

    def prepare_filename(self, filename):
        project_root = Path(__file__).parent.parent.parent
        return project_root / self.answers_dir / filename