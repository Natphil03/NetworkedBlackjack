import random


class diffie_hellman:
    """ Diffie-Hellman key generation
        (g^a mod p)^b mod p = g^(ab) mod p = (g^b mod p)^a mod p
    """
    def __init__(self, modulus, base, private_key = None):
        self.p = modulus
        self.g = base
        self.symmetric_key = 0
        self.partial_key = 0

        if not private_key:
            self.private_key = random.randint(1000, 5000)
        else:
            self.private_key = int(private_key)

    def calculate_partial_key(self):
        self.partial_key = (self.g ** self.private_key) % self.p
        return self.partial_key

    def calculate_full_key(self, partial_key):
        self.symmetric_key = (partial_key ** self.private_key) % self.p
        return self.symmetric_key
