class Statistics:
    def __init__(self, writer):
        self.correct_answers = 0
        self.incorrect_answers = 0
        self.writer = writer

    def correct_answer(self):
        self.correct_answers += 1

    def incorrect_answer(self):
        self.incorrect_answers += 1

    def print_report(self, total_questions):
        correct_percentage = (self.correct_answers / total_questions) * 100 if total_questions > 0 else 0
        report = (
            f"--- Test Results ---\n"
            f"Correct Answers: {self.correct_answers}\n"
            f"Incorrect Answers: {self.incorrect_answers}\n"
            f"Correct Percentage: {correct_percentage:.2f}%\n"
        )
        print(report)
        self.writer.write(report)