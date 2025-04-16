import hashlib

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# Example
plain_password = "pass123"
hashed = hash_password(plain_password)
print(hashed)
