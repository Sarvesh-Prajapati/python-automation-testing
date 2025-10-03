# ------------- UNIT TESTING A REGISTRATION PAGE ----------------

# Run file in terminal : pytest test_fileName.py

%%writefile test_registration.py           # saves this code snippet as a file in Colab
import pytest

def register_user(username, email, password):
    if not username or not email or not password: return False
    if "@" not in email: return False
    return True

def test_registration():
    # Test with valid inputs
    assert register_user("testuser", "test@example.com", "password123") == True

    # Test with invalid inputs
    assert register_user("", "test@example.com", "password123") == False  # Missing username
    assert register_user("testuser", "", "password123") == False  # Missing email
    assert register_user("testuser", "test@example.com", "") == False  # Missing password
    assert register_user("testuser", "testexample.com", "password123") == False  # Invalid email format

# ------------- UNIT TESTING A CALCULATOR ----------------

%%writefile test_calculator.py             # saves this code snippet as a file in Colab

import pytest

def add(num1, num2): return num1 + num2
def subtract(num1, num2): return abs(num1 - num2)
def multiply(num1, num2): return num1 * num2
def divide(num1, num2):
  try:
    return num1 / num2
  except ZeroDivisionError:
    return "Cannot divide by zero"

def test_calculator():
  assert add(2, 3) == 5
  assert subtract(5, 3) == 2
  assert multiply(2, 3) == 6
  assert divide(6, 4) == 1.5

  assert add(2, 3) != -1
  assert subtract(5, -3) != -8
  assert multiply(2, -3) != 6
  assert divide(6, 2) != "Cannot divide by zero"

# --------------------- UNIT TESTING PASSWORD STRENGTH ----------------------------

%%writefile test_password_strength.py           # saves this code snippet as a file in Colab

import pytest
import re        # regular expressions package

def validate_password(password):

    if len(password) < 8 or len(password) > 16: return False             # Password length
    if " " in password or "-" in password: return False                  # No space or hyphen in PW
    if not re.search(r'\d', password): return False                      # at least 1 number
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password): return False  # at least 1 special char
    if not re.search(r'[A-Z]', password): return False                   # at least 1 uppercase letter
    if not re.search(r'[a-z]', password): return False                   # at least 1 lower case letter

    return True

def test_password_strength():
    # Test with valid password
    assert validate_password("Password123!") == True
    assert validate_password("aB1@cDeFghIjK") == True

    # Test with invalid passwords
    assert validate_password("short") == False  # Too short
    assert validate_password("toolongpasswordtoolong") == False  # Too long
    assert validate_password("Password 123!") == False           # Contains space
    assert validate_password("Password-123!") == False           # Contains hyphen
    assert validate_password("Password!!!") == False             # Missing number
    assert validate_password("Password123") == False             # Missing special character
    assert validate_password("password123!") == False            # Missing uppercase letter
    assert validate_password("PASSWORD123!") == False            # Missing lowercase letter
    assert validate_password("12345678!") == False               # Missing upper and lower case
    assert validate_password("ABCDEFG@") == False                # Missing number and lower case


# -------------- UNIT TESTING PASSWORD STRENGTH USING PARAMETRIZATION --------------------
%%writefile test_password_strength.py

import pytest
import re

def validate_password(password):
    if len(password) < 8 or len(password) > 16: return False             # Password length
    if " " in password or "-" in password: return False                  # No space or hyphen in PW
    if not re.search(r'\d', password): return False                      # at least 1 number
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password): return False  # at least 1 special char
    if not re.search(r'[A-Z]', password): return False                   # at least 1 uppercase letter
    if not re.search(r'[a-z]', password): return False                   # at least 1 lower case letter
    return True

pw_list = ["Password123!", "aB1@cDeFghIjK", "short", "toolongpasswordtoolong"]

@pytest.mark.parametrize("password", pw_list)
def test_password(password):
  assert validate_password(password) == True
  # print(f'Found password {password} as :', validate_password(password))
