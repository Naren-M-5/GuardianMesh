import hashlib
import hmac
import time


class SignatureError(ValueError):
    pass


def sign(body: bytes, secret: str, timestamp: str) -> str:
    payload = timestamp.encode() + b"." + body
    return hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()


def verify(body: bytes, secret: str, timestamp: str | None, signature: str | None,
           tolerance_seconds: int = 300) -> None:
    if not timestamp or not signature:
        raise SignatureError("Missing webhook signature headers")
    try:
        sent_at = int(timestamp)
    except ValueError as exc:
        raise SignatureError("Invalid webhook timestamp") from exc
    if abs(int(time.time()) - sent_at) > tolerance_seconds:
        raise SignatureError("Webhook timestamp is outside the replay window")
    expected = sign(body, secret, timestamp)
    supplied = signature.removeprefix("sha256=")
    if not hmac.compare_digest(expected, supplied):
        raise SignatureError("Invalid webhook signature")
