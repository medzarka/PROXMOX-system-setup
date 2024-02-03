
import string
import random

class PasswordGenerator:

    @staticmethod
    def generate_password(password_length=50):
        characters = string.ascii_letters + string.digits + '@#$%&'
        password = ''
        for index in range(password_length):
            password = password + random.choice(characters)
        return password