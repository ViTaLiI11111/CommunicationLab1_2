import threading
from pathlib import Path

class QuizSingleton:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance.yaml_dir = None
                    cls._instance.answers_dir = None
                    cls._instance.in_ext = None
                    cls._instance.log_dir = None
        return cls._instance

    def get_project_path(self, relative_path):
        project_root = Path(__file__).parent.parent.parent
        return project_root / relative_path

    def is_configured(self):
        return self.yaml_dir is not None and \
               self.answers_dir is not None and \
               self.in_ext is not None and \
               self.log_dir is not None

    def __repr__(self):
        return f"QuizSingleton(yaml_dir='{self.yaml_dir}', answers_dir='{self.answers_dir}', in_ext='{self.in_ext}', log_dir='{self.log_dir}')"