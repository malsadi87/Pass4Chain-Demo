from sawtooth_signing import create_context
from sawtooth_signing import CryptoFactory


context = create_context('secp256k1')


def get_new_signer(private_key=None):
    if private_key is None:
        private_key = context.new_random_private_key()
    return CryptoFactory(context).new_signer(private_key)


# To get public key for transaction:
# pub_key = signer.get_public_key().as_hex()
