from typing import Any

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization

from app.core.config.environment_config import settings


class JWKSService:
    """Service for handling JWKS operations."""

    def __init__(self):
        self._private_key_pem = settings.PRIVATE_KEY
        self._public_key_pem = settings.PUBLIC_KEY

    def getPrivateKey(self) -> str:
        """Get the private key in PEM format."""
        return self._private_key_pem

    def getPublicKey(self) -> str:
        """Get the public key in PEM format."""
        return self._public_key_pem

    def getJWK(self) -> dict[str, Any]:
        """Get the public key in JWK (JSON Web Key) format."""

        # Extract RSA public key numbers
        encoded_public_key = serialization.load_pem_public_key(
            self._public_key_pem.encode(), backend=default_backend()
        )
        public_numbers = encoded_public_key.public_numbers()

        # Convert to JWK format
        return {
            'kty': 'RSA',
            'use': 'sig',
            'alg': 'RS256',
            'kid': '1',  # Key ID - can be made configurable
            'n': self._base64url_encode(public_numbers.n),
            'e': self._base64url_encode(public_numbers.e),
        }

    def getJWKS(self) -> dict[str, Any]:
        """Get the JWKS (JSON Web Key Set) containing the public key."""
        return {'keys': [self.getJWK()]}

    def _base64url_encode(self, number: int) -> str:
        """Encode a large integer as base64url without padding."""
        import base64

        # Convert the integer to bytes (big-endian)
        byte_length = (number.bit_length() + 7) // 8
        if byte_length == 0:
            byte_length = 1
        number_bytes = number.to_bytes(byte_length, 'big')

        # Encode to base64url without padding
        encoded = base64.urlsafe_b64encode(number_bytes).decode('ascii')
        return encoded.rstrip('=')


# Global instance
jwks_service = JWKSService()
