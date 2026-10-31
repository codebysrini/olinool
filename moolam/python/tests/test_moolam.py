"""moolam base-package tests: seal press round-trip + tamper + downgrade."""
import json

import pytest

from moolam import KeyResolver, Signer, jws_decode, jws_sign, sha256_b64u
from moolam.core import b64u_decode, b64u_encode, canonical_json


def test_sign_verify_roundtrip():
    s = Signer.generate("did:web:a.example")
    r = KeyResolver()
    r.register_signer(s)
    jws = jws_sign(s, "test+jws", {"hello": "world", "n": 1})
    _, payload, signing_input, sig = jws_decode(jws)
    assert payload == {"hello": "world", "n": 1}
    assert r.verify(s.agent_id, signing_input, sig)


def test_tamper_breaks_signature():
    s = Signer.generate("did:web:a.example")
    r = KeyResolver()
    r.register_signer(s)
    h_b, p_b, s_b = jws_sign(s, "test+jws", {"amount": 10}).split(".")
    payload = json.loads(b64u_decode(p_b))
    payload["amount"] = 9999
    forged = f"{h_b}.{b64u_encode(canonical_json(payload))}.{s_b}"
    _, _, signing_input, sig = jws_decode(forged)
    assert not r.verify(s.agent_id, signing_input, sig)


def test_wrong_key_rejected():
    s = Signer.generate("did:web:a.example")
    other = Signer.generate("did:web:b.example")
    r = KeyResolver()
    r.register_signer(other)  # register the WRONG key for a
    _, _, signing_input, sig = jws_decode(jws_sign(s, "test+jws", {"x": 1}))
    assert not r.verify("did:web:a.example", signing_input, sig)  # unresolved -> False


def test_canonical_json_is_stable():
    assert canonical_json({"b": 1, "a": 2}) == canonical_json({"a": 2, "b": 1})
    assert sha256_b64u(b"abc") == sha256_b64u(b"abc")


def test_malformed_jws_raises():
    with pytest.raises(ValueError):
        jws_decode("not.a.valid.jws.string")
    with pytest.raises(ValueError):
        jws_decode("onlyonesegment")


# Tricky characters below are built with chr() so no editor/tooling layer can
# silently normalize or re-escape them; BS/Q keep backslash counts readable.
_BS, _Q = chr(92), chr(34)  # backslash, double-quote


def test_canonical_json_rfc8785_known_answers():
    """RFC 8785 known-answer vectors: sect 3.2.3 sample + key-sorting sample."""
    # Sample 1 (sect 3.2.3): number formatting, string escaping, literals.
    # Input string chars: euro $ U+000F LF A ' B " backslash backslash " /
    tricky = "€$" + chr(0x0F) + chr(0x0A) + "A'B" + _Q + _BS + _BS + _Q + "/"
    obj = {
        "numbers": [333333333.33333329, 1e30, 4.50, 2e-3, 0.000000000000000000000000001],
        "string": tricky,
        "literals": [None, True, False],
    }
    expected = (
        '{{"literals":[null,true,false],'
        '"numbers":[333333333.3333333,1e+30,4.5,0.002,1e-27],'
        '"string":"€${bs}u000f{bs}nA\'B{bs}"{bs}{bs}{bs}{bs}{bs}"/"}}'
    ).format(bs=_BS).encode("utf-8")
    assert canonical_json(obj) == expected

    # Sample 2: property sorting is by UTF-16 code units, output is raw UTF-8
    # (only C0 controls escaped). U+1F600 sorts before U+FB33 via surrogates.
    obj2 = {
        "€": "Euro Sign",
        chr(0x0D): "Carriage Return",
        chr(0xFB33): "Hebrew Letter Dalet With Dagesh",
        "1": "One",
        "😀": "Emoji: Grinning Face",
        chr(0x80): "Control",
        "ö": "Latin Small Letter O With Diaeresis",
    }
    expected2 = (
        '{{"{bs}r":"Carriage Return","1":"One","{c80}":"Control",'
        '"ö":"Latin Small Letter O With Diaeresis","€":"Euro Sign",'
        '"😀":"Emoji: Grinning Face","{fb33}":"Hebrew Letter Dalet With Dagesh"}}'
    ).format(bs=_BS, c80=chr(0x80), fb33=chr(0xFB33)).encode("utf-8")
    assert canonical_json(obj2) == expected2


def test_canonical_json_v01_byte_parity():
    """v0.1 wire compatibility: for the all-ASCII payload shapes this stack
    mints (receipt/invocation claims, JWS headers, ints and simple floats),
    JCS output MUST equal the v0.1 prototype encoder byte-for-byte."""
    fixtures = [
        {  # receipt claims (muthirai shape)
            "v": "0.1",
            "rid": "0d6cba9f-6dd5-4c88-8c48-6f30c1a3a44e",
            "prh": None,
            "pri": "did:web:principal.example",
            "iss": "did:web:principal.example",
            "sub": "did:web:agent-a.example",
            "aud": ["did:web:tool.*"],
            "scope": [{"act": "call", "res": "tool/*", "limits": {"amount": 250, "rate": 2.5}}],
            "cst": {"iat": 1751500000, "exp": 1751503600, "max_depth": 4, "epoch": 0},
            "asr": {"level": 0, "evidence": None},
        },
        {  # invocation claims
            "typ": "olinool-invocation",
            "rcp": "qFyMdiDGYHiWKevXInterb64uPayloadHashStub",
            "sub": "did:web:agent-a.example",
            "aud": "did:web:tool.example",
            "req": "47DEQpj8HBSaTImW9-5Wg_hashStub",
            "iat": 1751500042,
            "nnc": "vY9x_1-abcDEF",
        },
        {"alg": "EdDSA", "typ": "olinool-receipt+jws", "kid": "did:web:principal.example"},
        {"limits": {"simple_float": 4.5, "milli": 0.002, "zero": 0, "int": 10}},
    ]
    for obj in fixtures:
        legacy = json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("ascii")
        assert canonical_json(obj) == legacy
