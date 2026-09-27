import hashlib
import json
from ..models import Idempotency
from ..errors import fail


def begin(db, user_id, scope, key, payload):
    if not key or not 8 <= len(key) <= 120:
        fail('IDEMPOTENCY_KEY_REQUIRED', 'Supply an Idempotency-Key of 8–120 characters.', 400)
    digest = hashlib.sha256(json.dumps(payload, sort_keys=True, default=str).encode()).hexdigest()
    row = db.get(Idempotency, (user_id, scope, key))
    if row:
        if row.request_hash != digest:
            fail('IDEMPOTENCY_CONFLICT', 'This key was already used for a different request.', 409)
        return row, True
    row = Idempotency(user_id=user_id, scope=scope, key=key, request_hash=digest)
    db.add(row)
    db.flush()
    return row, False
