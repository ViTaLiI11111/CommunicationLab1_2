
import yaml
import json
import os
import sys
import glob
import threading
from pathlib import Path
from .question import Question
from .quiz import QuizSingleton
import logging

logger = logging.getLogger(__name__)

class QuestionData:
    def __init__(self):
        self.collection = []
        config = QuizSingleton()
        self.yaml_dir = config.yaml_dir
        self.in_ext = config.in_ext
        self.log_dir = config.log_dir
        self.answers_dir = config.answers_dir
        self._project_root = Path(__file__).parent.parent.parent
        self.threads = []
        self.load_data()

    def to_yaml(self):
        return yaml.dump([q.to_h() for q in self.collection], allow_unicode=True, default_flow_style=False)

    def save_to_yaml(self, filename="testing.yml"):
        save_path = self._project_root / self.log_dir / filename
        try:
            save_path.parent.mkdir(parents=True, exist_ok=True)
            with open(save_path, "w", encoding="utf-8") as f:
                f.write(self.to_yaml())
            logger.info(f"Questions data saved to {save_path}")
        except Exception as e:
            logger.error(f"Error saving questions data to {save_path}: {e}", exc_info=True)


    def to_json(self):
        return json.dumps([q.to_h() for q in self.collection], ensure_ascii=False, indent=2)

    def save_to_json(self, filename="testing.json"):
        save_path = self._project_root / self.log_dir / filename
        try:
            save_path.parent.mkdir(parents=True, exist_ok=True)
            with open(save_path, "w", encoding="utf-8") as f:
                f.write(self.to_json())
            logger.info(f"Questions data saved to {save_path}")
        except Exception as e:
            logger.error(f"Error saving questions data to {save_path}: {e}", exc_info=True)



    def each_file(self, block):
        path = self._project_root / self.yaml_dir
        if not path.exists():
            logger.warning(f"Question directory not found: {path}")
            return
        files = glob.glob(str(path / f"*.{self.in_ext}"))
        if not files:
             logger.warning(f"No question files found in {path} with extension .{self.in_ext}")
        for filename in files:
            block(filename)

    def in_thread(self, block):
        import threading
        thread = threading.Thread(target=block)
        self.threads.append(thread)
        thread.start()

    def load_data(self):
        logger.info(f"Loading questions from {self._project_root / self.yaml_dir} with extension .{self.in_ext}")
        def load(filename):
            try:
                self.load_from(filename)
            except Exception as e:
                logger.error(f"Error loading questions from {filename}: {e}", exc_info=True)

        self.each_file(lambda filename: self.in_thread(lambda: load(filename)))

        for thread in self.threads:
            thread.join()

        self.threads = []
        logger.info(f"Finished loading questions. Total loaded: {len(self.collection)}")


    def load_from(self, filename):
        try:
            with open(filename, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
                if isinstance(data, list):
                    for item in data:
                        if isinstance(item, dict) and "question" in item and "answers" in item:
                            question = Question(item["question"], item["answers"])
                            self.collection.append(question)
                        else:
                            logger.warning(f"Invalid data format for an item in {filename}. Expected dict with 'question' and 'answers'. Skipping entry: {item}")
                else:
                    logger.warning(f"Invalid root data format in {filename}. Expected a list of questions. Skipping file.")


        except FileNotFoundError:
            logger.error(f"File not found: {filename}")
        except yaml.YAMLError as e:
            logger.error(f"YAML error in {filename}: {e}", exc_info=True)
        except Exception as e:
            logger.error(f"An unexpected error occurred while loading {filename}: {e}", exc_info=True)