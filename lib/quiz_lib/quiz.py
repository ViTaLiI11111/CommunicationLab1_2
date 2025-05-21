# lib/quiz_lib/quiz.py
import threading
import os
from pathlib import Path

# Використовуємо патерн Singleton для конфігурації
class QuizSingleton:
    _instance = None
    _lock = threading.Lock() # Для потокобезпеки, хоча конфігурація, як правило, відбувається в одному потоці

    def new(cls):
        if cls._instance is None:
            with cls._lock:
                # Перевіряємо ще раз після отримання блокування
                if cls._instance is None:
                    cls._instance = super(QuizSingleton, cls).new(cls)
                    # Ініціалізуємо з дефолтними значеннями
                    cls._instance.yaml_dir = 'config/questions'
                    cls._instance.answers_dir = 'quiz_answers'
                    cls._instance.in_ext = 'yml'
                    cls._instance.log_dir = 'log'
                    cls._instance._initialized = True # Внутрішній прапорець ініціалізації
        return cls._instance

    @classmethod
    def config(cls, configure_func):
        """Метод для конфігурування Singleton."""
        instance = cls()
        if instance._initialized:
             # Викликаємо функцію, яка налаштовує екземпляр
             configure_func(instance)
             instance._initialized = False # Позначаємо як сконфігурований (або можна прапорець "сконфігуровано")
             # logger.info("QuizSingleton configured.") # Використовуйте логер, якщо він доступний тут
        else:
             # Це може статися, якщо config викликається повторно
             pass # Або логуйте попередження

    # Можна додати метод для отримання шляхів відносно кореня проекту
    def get_project_path(self, relative_path):
        """Повертає абсолютний шлях відносно кореня проекту."""
        # Припускаємо, що цей файл знаходиться в lib/quiz_lib/
        project_root = Path(file).parent.parent.parent
        return project_root / relative_path

# Дефолтна конфігурація (може бути перевизначена в main.py)
# Не викликайте config() тут, це має робити main.py або BotEngine після додавання config_paths
# QuizSingleton.config(lambda cfg: ...)