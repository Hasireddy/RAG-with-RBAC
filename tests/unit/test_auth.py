from app.auth.hash_password import hash_password, verify_password


# Test for password hashing that returns different password after hashing
def test_hash_password_returns_different_value():
    password = "MySecretPassword123"
    hashed_password = hash_password(password)

    assert hashed_password != password # The stored hash must not simply be palin-text password
    assert hashed_password # hash should not be empty



# Test the password and hashed password
# Correct password verification
def test_verify_password_with_correct_password():
    password = "MySecretPassword123"
    hashed_password = hash_password(password)

    result = verify_password(password, hashed_password)

    assert result is True



# Test the wrong password
def test_verify_password_with_wrong_password():

    password = "MySecretPassword123"

    hashed_password = hash_password(password)

    result = verify_password(
        "WrongPassword123",
        hashed_password
    )

    assert result is False



# Test empty password
def test_verify_password_with_empty_password():

    hashed_password = hash_password("MySecretPassword123")

    result = verify_password("", hashed_password)

    assert result is False



# Test empty hash
def test_verify_password_with_empty_hash():
    password =  "MySecretPassword123"

    result = verify_password(
        password, ""
    )

    assert result is False





