"""
Sign In With Apple authentication backend.

Docs:
    * https://developer.apple.com/documentation/signinwithapplerestapi
    * https://developer.apple.com/documentation/signinwithapplerestapi/tokenresponse

Settings:
    * `TEAM` - your team id;
    * `KEY` - your key id;
    * `CLIENT` - your client id;
    * `SECRET` - your secret key;
    * `SCOPE` (optional) - e.g. `['name', 'email']`;
    * `EMAIL_AS_USERNAME` - use Apple email is username is set, use Apple ID otherwise.
    * `AppleIdAuth.TOKEN_TTL_SEC` - time before JWT token expiration, seconds.
"""

import jwt
from jwt.algorithms import RSAAlgorithm
from social_core.backends.apple import AppleIdAuth

from social_core.exceptions import AuthCanceled


class AppleIdAppAuth(AppleIdAuth):
    def decode_app_token(self, id_token):
        """Decode and validate JWT token from apple and return payload including user data."""

        if not id_token:
            raise AuthCanceled("Missing id_token parameter")

        kid = jwt.get_unverified_header(id_token).get('kid')
        public_key = RSAAlgorithm.from_jwk(self.get_apple_jwk(kid))

        decoded = jwt.decode(id_token, key=public_key,
                             audience=self.setting("CLIENT_APP"), algorithm="RS256", )
        return decoded
