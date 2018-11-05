import uuid

class AuthKeyGenerator:

    def generate_auth_key(self):
        return uuid.uuid4().hex
