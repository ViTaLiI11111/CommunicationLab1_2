class InputReader:
    def read(self, welcome_message=None, validator=None, error_message=None, process=None):
        while True:
            if welcome_message:
                print(welcome_message)
            user_input = input()

            if validator and not validator(user_input):
                if error_message:
                    print(error_message)
                continue

            if process:
                user_input = process(user_input)

            return user_input