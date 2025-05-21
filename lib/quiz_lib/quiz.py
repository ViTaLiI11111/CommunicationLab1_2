
import threading
import os
from pathlib import Path


class QuizSingleton:
    _instance = None
    _lock = threading.Lock()

    def new(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(QuizSingleton, cls).new(cls)
                    cls._instance.yaml_dir = 'config/questions'
                    cls._instance.answers_dir = 'quiz_answers'
                    cls._instance.in_ext = 'yml'
                    cls._instance.log_dir = 'log'
                    cls._instance._initialized = True
        return cls._instance

    @classmethod
    def config(cls, configure_func):
        instance = cls()
        if instance._initialized:
             configure_func(instance)
             instance._initialized = False
        else:
             pass

    def get_project_path(self, relative_path):
        project_root = Path(__file__).parent.parent.parent
        return project_root / relative_path
