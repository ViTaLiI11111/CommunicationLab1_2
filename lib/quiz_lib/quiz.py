class QuizSingleton:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.yaml_dir = None
            cls._instance.in_ext = None
            cls._instance.answers_dir = None
            cls._instance.log_dir = None
        return cls._instance

    @classmethod
    def config(cls, block):
        instance = cls()
        block(instance)

    @property
    def yaml_dir(self):
        return self._yaml_dir

    @yaml_dir.setter
    def yaml_dir(self, value):
        self._yaml_dir = value

    @property
    def in_ext(self):
        return self._in_ext

    @in_ext.setter
    def in_ext(self, value):
        self._in_ext = value

    @property
    def answers_dir(self):
        return self._answers_dir

    @answers_dir.setter
    def answers_dir(self, value):
        self._answers_dir = value

    @property
    def log_dir(self):
        return self._log_dir

    @log_dir.setter
    def log_dir(self, value):
        self._log_dir = value