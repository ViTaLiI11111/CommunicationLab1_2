import json
import yaml
import random

class Question:
    def __init__(self, raw_text, raw_answers):
        self.question_body = raw_text
        self.question_answers = {}
        self.question_correct_answer = None
        self.load_answers(raw_answers)

    def load_answers(self, raw_answers):
        answers_list = list(raw_answers)
        random.shuffle(answers_list)
        chars = [chr(i) for i in range(ord('A'), ord('A') + len(answers_list))]
        self.question_answers = {char: answer for char, answer in zip(chars, answers_list)}
        original_correct_answer = raw_answers[0]
        for char, answer in self.question_answers.items():
            if answer == original_correct_answer:
                self.question_correct_answer = char
                break

    def display_answers(self):
        return [f"{char}. {answer}" for char, answer in self.question_answers.items()]

    def __str__(self):
        return self.question_body

    def to_h(self):
        return {
            "question_body": self.question_body,
            "question_correct_answer": self.question_correct_answer,
            "question_answers": self.question_answers
        }

    def to_json(self):
        return json.dumps(self.to_h())

    def to_yaml(self):
        return yaml.dump(self.to_h())

    def find_answer_by_char(self, char):
        return self.question_answers.get(char)