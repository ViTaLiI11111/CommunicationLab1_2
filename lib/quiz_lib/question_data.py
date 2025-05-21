# lib/quiz_lib/question_data.py

import yaml
import json
import os
import sys
import glob
import threading
from pathlib import Path
from .question import Question
from .quiz import QuizSingleton
import logging # Імпортуємо логування

logger = logging.getLogger(name) # Отримуємо об'єкт логера

class QuestionData:
    def init(self):
        self.collection = []
        config = QuizSingleton()
        self.yaml_dir = config.yaml_dir
        self.in_ext = config.in_ext
        self.log_dir = config.log_dir # Отримуємо log_dir з Singleton
        self.answers_dir = config.answers_dir # Отримуємо answers_dir (хоча тут не використовується)
        # Коректно визначаємо корінь проекту. Path(file) - шлях до поточного файлу.
        # .parent.parent.parent - піднімаємося на три рівні вгору (з lib/quiz_lib/question_data.py до кореня)
        self._project_root = Path(file).parent.parent.parent
        self.threads = []
        self.load_data() # Завантажуємо дані при створенні об'єкта QuestionData

    def to_yaml(self):
        # Використовуємо allow_unicode=True та default_flow_style=False для читабельного YAML з кирилицею
        return yaml.dump([q.to_h() for q in self.collection], allow_unicode=True, default_flow_style=False)

    def save_to_yaml(self, filename="testing.yml"): # Дефолтна назва файлу testing.yml
        # Формуємо повний шлях: корінь_проекту / log_dir / filename
        save_path = self._project_root / self.log_dir / filename
        try:
            save_path.parent.mkdir(parents=True, exist_ok=True) # Перестрахуємося, що директорія існує
            with open(save_path, "w", encoding="utf-8") as f:
                f.write(self.to_yaml())
            logger.info(f"Questions data saved to {save_path}") # Логуємо успіх
        except Exception as e:
            logger.error(f"Error saving questions data to {save_path}: {e}", exc_info=True) # Логуємо помилку


    def to_json(self):
        # Використовуємо ensure_ascii=False та indent=2 для читабельного JSON з кирилицею
        return json.dumps([q.to_h() for q in self.collection], ensure_ascii=False, indent=2)

    def save_to_json(self, filename="testing.json"): # Дефолтна назва файлу testing.json
        # Формуємо повний шлях: корінь_проекту / log_dir / filename
        save_path = self._project_root / self.log_dir / filename
        try:
            save_path.parent.mkdir(parents=True, exist_ok=True) # Перестрахуємося
            with open(save_path, "w", encoding="utf-8") as f:
                f.write(self.to_json())
            logger.info(f"Questions data saved to {save_path}") # Логуємо успіх
        except Exception as e:
            logger.error(f"Error saving questions data to {save_path}: {e}", exc_info=True) # Логуємо помилку


    # prepare_filename більше не потрібен, оскільки ми використовуємо Path і self._project_root напряму

    def each_file(self, block):
        # Формуємо повний шлях до директорії питань
        path = self._project_root / self.yaml_dir
        # Перевіряємо, чи шлях існує
        if not path.exists():
            logger.warning(f"Question directory not found: {path}") # Логуємо попередження
            return
        # Перетворюємо Path об'єкт на рядок для glob (glob часто вимагає рядок)
        files = glob.glob(str(path / f"*.{self.in_ext}"))
        if not files:
             logger.warning(f"No question files found in {path} with extension .{self.in_ext}") # Логуємо, якщо файли не знайдені
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
                # Логуємо помилку завантаження конкретного файлу
                logger.error(f"Error loading questions from {filename}: {e}", exc_info=True)

        self.each_file(lambda filename: self.in_thread(lambda: load(filename)))

        # Чекаємо завершення всіх потоків завантаження
        for thread in self.threads:
            thread.join()

        self.threads = []  # Очищаємо список потоків
        logger.info(f"Finished loading questions. Total loaded: {len(self.collection)}")

    def load_from(self, filename):
        try:
            with open(filename, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
                if isinstance(data, list):  # Перевіряємо, чи кореневий елемент - список
                    for item in data:
                        # Перевіряємо, чи кожен елемент списку - словник з потрібними ключами
                        if isinstance(item, dict) and "question" in item and "answers" in item:
                            # Створюємо об'єкт Question. Передаємо текст питання (item["question"])
                            # та список відповідей (item["answers"]).
                            question = Question(item["question"], item["answers"])
                            self.collection.append(question)
                        else:
                            logger.warning(
                                f"Invalid data format for an item in {filename}. Expected dict with 'question' and 'answers'. Skipping entry: {item}")  # Логуємо попередження
                else:
                    logger.warning(
                        f"Invalid root data format in {filename}. Expected a list of questions. Skipping file.")  # Логуємо попередження


        except FileNotFoundError:
            logger.error(f"File not found: {filename}")  # Логуємо помилку
        except yaml.YAMLError as e:
            logger.error(f"YAML error in {filename}: {e}", exc_info=True)  # Логуємо помилку парсингу YAML
        except Exception as e:
            # Загальний виняток при обробці файлу
            logger.error(f"An unexpected error occurred while loading {filename}: {e}", exc_info=True)