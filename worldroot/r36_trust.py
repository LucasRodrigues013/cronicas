"""Local custody authentication, not external attestation or author certification."""
import hashlib
import hmac
import json
from .r36_evaluation import HEX

VERSION = "r36-e7-local-auth-v1"
PURPOSES = {"source-authority","run-binding","attempt","review-receipt","human-review","feedback-observation","feedback-proposal","feedback-event","feedback-approval","operational-summary"}
def require(ok,msg):
    if not ok: raise ValueError(msg)
def digest(x):
    return isinstance(x,str) and HEX.fullmatch(x) is not None
def canonical(obj):
    return json.dumps(obj,sort_keys=True,ensure_ascii=False,separators=(",",":"),allow_nan=False).encode("utf-8")
def keycheck(key):
    require(isinstance(key,bytes) and len(key)>=32,"Require at least 32 bytes of locally held key material")
def authenticate(purpose,payload,key):
    keycheck(key)
    require(purpose in PURPOSES and isinstance(payload,dict),"Invalid authentication purpose/payload")
    body={"schema":VERSION,"purpose":purpose,"payload":payload}
    return {**body,"mac":hmac.new(key,canonical(body),hashlib.sha256).hexdigest()}
def verify(envelope,purpose,key,expected=None):
    keycheck(key)
    require(isinstance(envelope,dict) and set(envelope)=={"schema","purpose","payload","mac"} and
            envelope["schema"]==VERSION and envelope["purpose"]==purpose and digest(envelope["mac"]),"Invalid envelope")
    fresh=authenticate(purpose,envelope["payload"],key)
    require(hmac.compare_digest(fresh["mac"],envelope["mac"]),"Authentication failed")
    if expected is not None:require(canonical(envelope["payload"])==canonical(expected),"Stale or wrong binding")
    return envelope["payload"]
def authorize_manifest(manifest,scope,key):
    """Trusted custodian explicitly approves exact manifest and scope off-line."""
    require(isinstance(scope,dict) and set(scope)=={"authority_revision","engine_revision"} and
            all(isinstance(v,str) and bool(v.strip()) for v in scope.values()),"Missing authority/engine pin")
    return authenticate("source-authority",{"scope":scope,"manifest":manifest},key)
