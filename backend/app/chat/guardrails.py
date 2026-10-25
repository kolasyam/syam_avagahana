"""
Chat Guardrails — defense-in-depth (Layers L0..L3)
==================================================
Deterministic RULE ENGINE evaluated BEFORE the pipeline reacts at every stage.
No LLM tokens, no model dependency: regex classification, sub-millisecond.

  L0  INPUT GUARD     stream_chat(): sensitive / out-of-scope user messages are
                      refused BEFORE any LLM call or tool fires (classify_input).
  L1  ROUTER SCOPE    SYSTEM_PROMPT hard rules (onion-only platform scope).
  L2  TOOL GUARDS     web_lookup topic gate (agriculture/market/weather ONLY);
                      forecast horizon clamp (1..90); scenario factor value
                      sanity bounds; geography fuzzy-resolved against the DB.
  L3  OUTPUT GUARD    scans the composed/streamed answer for sensitive data,
                      fabricated ingestion claims, commodity drift, or
                      injection echoes before it reaches the user
                      (guard_output / StreamingGuard).

Every trip emits an SSE `guardrail` frame and a GUARDRAIL_* audit row —
governance is visible in the demo trace, never silent.
"""

import re
from typing import Any, Dict, List, Optional, Tuple

# --------------------------------------------------------------------------- #
# Categories + refusal texts (stock, honest, platform-framed)
# --------------------------------------------------------------------------- #

CAT_OK = "OK"
CAT_INJECTION = "PROMPT_INJECTION"
CAT_PII = "PII_OR_IDENTITY"
CAT_POLITICAL = "POLITICAL_OR_RELIGIOUS"
CAT_MEDICAL = "MEDICAL_OR_HEALTH"
CAT_LEGAL = "LEGAL_ADVICE"
CAT_FINANCE = "PERSONAL_FINANCE"
CAT_HARMFUL = "HARMFUL_OR_ILLEGAL"
CAT_OTHER_COMMODITY = "OTHER_COMMODITY"
CAT_OFF_TOPIC = "OFF_TOPIC"
# output-filter only:
CAT_FABRICATION = "FABRICATED_INGESTION_CLAIM"
CAT_DRIFT = "COMMODITY_SCOPE_DRIFT"
CAT_ECHO = "INJECTION_ECHO"

REFUSALS: Dict[str, str] = {
    CAT_INJECTION: (
        "🚫 Guardrail: that request tries to change or reveal my operating "
        "instructions, which I don't do. I answer onion market questions — "
        "prices, forecasts, risk levels and what-if factors — using only the "
        "platform's governed tools."
    ),
    CAT_PII: (
        "🚫 Guardrail: I can't process personal identity data (Aadhaar, PAN, "
        "OTP, passwords or credentials) — this platform handles onion market "
        "intelligence, not personal records."
    ),
    CAT_POLITICAL: (
        "🚫 Guardrail: I stay strictly neutral on political parties, elections "
        "and religion. I'm built for onion price intelligence — ask me about "
        "prices, forecasts, breach risk, or scenario factors."
    ),
    CAT_MEDICAL: (
        "🚫 Guardrail: I don't give medical or health advice. My scope is the "
        "onion market — prices, forecasts and factors like weather and fuel."
    ),
    CAT_LEGAL: (
        "🚫 Guardrail: I can't provide legal advice. For onion market "
        "questions — prices, forecasts, risk, scenarios — I'm ready."
    ),
    CAT_FINANCE: (
        "🚫 Guardrail: I can't advise on personal investments (shares, crypto, "
        "savings, gold). My scope is onion market intelligence for the Civil "
        "Supplies department."
    ),
    CAT_HARMFUL: (
        "🚫 Guardrail: I can't help with that. This platform is for safe, "
        "lawful onion market intelligence only."
    ),
    CAT_OTHER_COMMODITY: (
        "🚫 Guardrail: this platform manages ONION only — no rice, wheat, "
        "tomato or other-commodity data is ingested, so I don't answer for "
        "them. Ask me anything about onion prices, forecasts or factors."
    ),
    CAT_OFF_TOPIC: (
        "🚫 Guardrail: that's outside my scope. I'm the AP Onion platform "
        "assistant — try today's price, averages, a 30-day forecast, a "
        "what-if factor, or weather impact on onion prices."
    ),
    # Output-filter replacements (answer was composed by the model, then caught)
    CAT_FABRICATION: (
        "🚫 Guardrail (output filter): the drafted answer wrongly claimed web "
        "data was ingested into the model — replaced. Web results are "
        "citations only and are never ingested; the model runs purely on the "
        "ingested AGMARKNET-derived series and Chronos-2."
    ),
    CAT_DRIFT: (
        "🚫 Guardrail (output filter): the drafted answer drifted outside the "
        "onion-only commodity scope — replaced. This platform manages onion "
        "only."
    ),
    CAT_ECHO: (
        "🚫 Guardrail (output filter): the drafted answer echoed an "
        "instruction-bypass attempt — replaced. My instructions cannot be "
        "changed through chat."
    ),
    CAT_PII + "_OUT": (
        "🚫 Guardrail (output filter): the drafted answer contained "
        "personal-data patterns — replaced. Please rephrase without personal "
        "identifiers."
    ),
}

# --------------------------------------------------------------------------- #
# L0 — INPUT GUARD
# --------------------------------------------------------------------------- #

# (category, patterns). Ordered by severity; first match wins.
_INPUT_RULES: List[Tuple[str, List[str]]] = [
    (CAT_INJECTION, [
        r"ignore\s+(?:all\s+|any\s+|your\s+|previous\s+|prior\s+|the\s+|my\s+|their\s+)*(?:instructions?|rules?|prompts?|settings?|guidelines?|guardrails?|above)",
        r"disregard\s+(?:all\s+|any\s+|your\s+|previous\s+|prior\s+|the\s+|my\s+)*(?:instructions?|rules?|prompts?|guidelines?|guardrails?)",
        r"forget\s+(?:all\s+|any\s+|your\s+|previous\s+|prior\s+|the\s+|my\s+)*(?:instructions?|rules?|prompts?|above)",
        r"\byou\s+are\s+now\b",
        r"\bact\s+as\s+(?:if|a|an|my|your)\b",
        r"\bpretend\s+(?:to\s+be|you\s+are)\b",
        r"\broleplay\b",
        r"\bsystem\s+prompt\b",
        r"\b(?:reveal|print|show|repeat|spell)\b.{0,24}\b(?:prompt|instructions?|rules?|config(?:uration)?)\b",
        r"\bjailbreak\b", r"\bdan\s+mode\b", r"\bdeveloper\s+mode\b",
        r"\bno\s+restrictions\b", r"\bunrestricted\s+mode\b",
        r"\boverride\b.{0,18}\b(?:instructions?|rules?|settings?|safety|guardrails?|filters?)\b",
        r"\bbypass\b.{0,14}\b(?:rules?|safety|guardrails?|filters?|restrictions?)\b",
        r"<\|",
        r"\binjected?\s+(?:instruction|prompt|command)s?\b",
    ]),
    (CAT_HARMFUL, [
        r"\bbombs?\b", r"\bexplosive", r"\bweapon", r"\bnarcotic",
        r"\bcocaine\b|\bheroin\b|\bmdma\b|\bmethamphetamine\b",
        r"\bkill(?:ing)?\s+(?:someone|a\s+person|him|her|them|my)",
        r"\bmurder\b", r"\bterror(?:is|st|iz)", r"\bkidnap", r"\bblackmail\b",
        r"\bhack(?:ing)?\s+(?:into|someone|accounts?|servers?|phones?)\b",
        r"\bsteal(?:ing)?\s+(?:data|money|passwords|personal)\b",
        r"\bcounterfeit\b", r"\bsmuggl", r"\bextort",
    ]),
    (CAT_PII, [
        r"\baadhaa?r\b", r"\bpan\s+card\b", r"\bpan\s+number\b",
        r"\botp\b", r"\bpassword\b", r"\bpassphrase\b", r"\bkyc\b",
        r"\bcredit\s+card\b", r"\bdebit\s+card\b", r"\bcvv\b",
        r"\b(?:phone|mobile|whatsapp)\s+number\b",
        r"\bmy\s+(?:address|bank|salary|account|location|details|data)\b",
        r"\bsomeone'?s\s+(?:address|phone|mobile|bank|details)\b",
        r"\bpersonal\s+(?:data|information|details|records?)\b",
        r"\bcustomer\s+(?:data|records?|details)\b",
        r"\bidentity\s+(?:card|number|theft)\b",
        r"\bbank\s+account\b", r"\bifsc\b", r"\bpin\s*number\b",
        r"\blogin\s+(?:id|credentials)\b",
    ]),
    (CAT_MEDICAL, [
        r"\b(?:medicine|medications?|dosage|dosing|medical\s+advice|health\s+advice)\b",
        r"\b(?:symptoms?|diagnos|prescription|self\s*-?\s*medicat)\w*\b",
        r"\b(?:cure|treats?|treatment|remed(?:y|ies))\b",
        r"\b(?:disease|cancer|diabet\w*|covid|infection|fever|headache|migraine)\b",
        r"\bvaccin\w*\b", r"\bdoctor\b", r"\bhospital\b",
        r"\b(?:lose|gain)\s+weight\b", r"\bnutrition\b|\bdiet\b",
    ]),
    (CAT_POLITICAL, [
        r"\belection", r"\bvote\b|\bvoting\b|\bvoters?\b",
        r"\bopinion\s+on\b",
        r"\b(?:your|the)\s+(?:opinion|view|stance|take)\b",
        r"\b(?:politic|political|politics)\w*\b",
        r"\bbjp\b|\bcongress\b|\btdp\b|\bycp\b|\bjsp\b|\bcpi\b|\bcpi\(m\)\b|\bcommunist\b",
        r"\breligio\w*\b",
        r"\bhindu\w*\b|\bmuslim\w*\b|\bchristian\w*\b|\bcaste\b|\bcommunal\b",
        r"\btemple\b|\bmosque\b|\bchurch\b",
        r"\briots?\b",
        r"\bwho\s+(?:should|will)\s+(?:i\s+)?(?:vote|win)\b",
    ]),
    (CAT_LEGAL, [
        r"\blegal\s+advice\b", r"\bsue\b|\blawsuit\b|\blitigation\b",
        r"\bfir\b", r"\bpolice\s+complaint\b", r"\bcourt\s+case\b",
        r"\badvocate\b|\blawyer\b|\bnotary\b|\baffidavit\b",
        r"\bpassport\b|\bvisa\s+(?:apply|rules?)\b",
    ]),
    (CAT_FINANCE, [
        r"\binvest(?:ing|ment)?\s+(?:my|our)\b",
        r"\bshould\s+(?:i|we)\s+invest\b",
        r"\binvest\s+in\s+(?:stocks?|shares?|crypto|gold|mutual)\b",
        r"\b(?:crypto|cryptocurrency|bitcoin|ethereum|nft)s?\b",
        r"\bmutual\s+fund", r"\bstock\s+market\b|\bshare\s+market\b",
        r"\b(?:my|our)\s+(?:savings|portfolio)\b",
        r"\btrading\s+(?:tips?|advice|calls?)\b",
        r"\bgold\s+(?:rate|price)\b", r"\bloan\s+against\s+(?:property|gold)\b",
        r"\bfixed\s+deposit\b|\bfd\s+rates?\b",
    ]),
    (CAT_OFF_TOPIC, [
        r"\bcricket\b|\bfootball\b|\bbadminton\b|\bhockey\b|\bipl\b|\bmatch\s+(?:score|yesterday|today)\b",
        r"\b(?:movie|film|bollywood|tollywood|netflix|ott\s+platform)\b",
        r"\bsong\b|\balbum\b|\bconcert\b|\bsinger\b",
        r"\bjoke\b|\bmeme\b|\bpoem\b|\bessay\b|\bnovel\b|\bstory\s+(?:about|for)\b",
        r"\b(?:game|games|gaming|pubg|free\s+fire)\b",
        r"\brecipe\b|\bcooking\b|\bbiryani\b",
        r"\biphone\b|\bsmartphone\b|\blaptop\b|\bair\s+conditioner\b|\brefrigerator\b",
        r"\b(?:write|draft|compose)\b.{0,22}\b(?:python|code|email|letter|song|poem|essay)\b",
        r"\bcat\b|\bpuppy|\bpets?\b",
    ]),
]

_OTHER_COMMODITY_RE = re.compile(
    r"\b(?:tomato(?:es)?|potato(?:es)?|rice|wheat|pulses?|dals?|tur\s*dal|chana|gram|"
    r"garlic|ginger|chill(?:y|ies)|turmeric|sugar|jaggery|maize|corn|"
    r"soybean|groundnut|cotton|oilseeds?)\b"
)
_ONION_RE = re.compile(r"\bonions?\b|\bpyaaz\b|\bvellul?i\b")

_COMPILED_INPUT: List[Tuple[str, List[re.Pattern]]] = [
    (cat, [re.compile(p, re.IGNORECASE) for p in pats])
    for cat, pats in _INPUT_RULES
]


def classify_input(message: str) -> Dict[str, Any]:
    """
    L0 input guard. Returns:
      {"allowed": True,  "category": "OK"}
      {"allowed": False, "category": <CAT_*, "refusal": str, "detail": str}
    """
    msg = (message or "").strip()
    for cat, patterns in _COMPILED_INPUT:
        for pat in patterns:
            m = pat.search(msg)
            if m:
                return {
                    "allowed": False,
                    "category": cat,
                    "refusal": REFUSALS[cat],
                    "detail": f"matched /{m.group(0)[:40]}/",
                }
    # Onion-only commodity scope: block other commodities unless onion is
    # explicitly mentioned (comparisons mentioning onion stay platform-side).
    if not _ONION_RE.search(msg) and _OTHER_COMMODITY_RE.search(msg):
        return {
            "allowed": False,
            "category": CAT_OTHER_COMMODITY,
            "refusal": REFUSALS[CAT_OTHER_COMMODITY],
            "detail": "non-onion commodity, no onion mention",
        }
    return {"allowed": True, "category": CAT_OK}


# --------------------------------------------------------------------------- #
# L2 — WEB TOPIC GUARD (the web tool escapes its lane for nothing else)
# --------------------------------------------------------------------------- #

_WEB_ALLOWED_RE = re.compile(
    r"(?:onion|pyaaz|mandi|market|price|prices|priced|wholesale|retail|modal|"
    r"arrival|commodit|agri|farm|crop|kharif|rabi|harvest|sow|storage|"
    r"godown|warehouse|buffer|msp|nafed|inflation|supply|demand|hoarding|"
    r"import|export|rain|rainfall|monsoon|drought|flood|cyclone|weather|"
    r"climate|temperature|humidity|heat\s*wave|diesel|fuel|petrol|freight|"
    r"transport|logistic)",
    re.IGNORECASE,
)


def web_topic_guard(query: str) -> Dict[str, Any]:
    """
    L2 web-tool gate: Tavily may be used ONLY for agriculture / market /
    weather topics tied to this platform's work. Refuses politics, sports,
    health, entertainment, personal data and general knowledge queries.
    """
    q = (query or "").strip()
    if not q:
        return {"allowed": False, "reason": "empty web query."}
    if _WEB_ALLOWED_RE.search(q):
        # double-check the query itself doesn't carry sensitive payloads
        verdict = classify_input(q)
        if not verdict["allowed"]:
            return {"allowed": False, "reason": f"sensitive content in query ({verdict['category']})."}
        return {"allowed": True, "reason": "on-platform topic"}
    return {
        "allowed": False,
        "reason": "query is outside the agriculture/market/weather scope.",
        "allowed_topics": "onion prices, mandis, commodities context, farming, weather, fuel, logistics",
    }


# --------------------------------------------------------------------------- #
# L2 — numeric param bounds for Forecast Agent tools
# --------------------------------------------------------------------------- #

FORECAST_HORIZON_MAX = 90


def sanitize_horizon(value: Any, default: int = 30) -> int:
    """Clamp LLM-supplied horizons into the supported 1..90 band."""
    try:
        h = int(float(value))
    except (TypeError, ValueError):
        return default
    return max(1, min(FORECAST_HORIZON_MAX, h))


FACTOR_VALUE_BOUNDS: Dict[str, Tuple[float, float]] = {
    "precipitation_mm": (0.0, 600.0),        # seasonal extremes are within this
    "temperature_c": (-5.0, 60.0),
    "fuel_price_inr_l": (40.0, 300.0),
    "diesel_price_inr_l": (40.0, 300.0),
    "petrol_price_inr_l": (60.0, 350.0),
}
_GENERIC_FACTOR_BOUNDS: Tuple[float, float] = (0.0, 100000.0)


def check_factor_value(variable: str, value: Any) -> Dict[str, Any]:
    """Sanity bounds for scenario inputs (no absurd/negative factors)."""
    try:
        v = float(value)
    except (TypeError, ValueError):
        return {"ok": False, "reason": f"value '{value}' is not a number."}
    if v != v:  # NaN
        return {"ok": False, "reason": "value is NaN."}
    lo, hi = FACTOR_VALUE_BOUNDS.get(variable, _GENERIC_FACTOR_BOUNDS)
    if not (lo <= v <= hi):
        return {
            "ok": False,
            "reason": f"value {v} outside the supported range for {variable} "
                      f"(supported: {lo} to {hi}).",
        }
    return {"ok": True}


# --------------------------------------------------------------------------- #
# L3 — OUTPUT GUARD
# --------------------------------------------------------------------------- #

_OUTPUT_RULES: List[Tuple[str, List[str]]] = [
    (CAT_PII, [
        r"\b\d{4}\s?\d{4}\s?\d{4}\b",                 # Aadhaar 12-digit
        r"\b[A-Z]{5}\d{4}[A-Z]\b",                    # PAN format
        r"\b(?:\+91[-\s]?)?[6-9]\d{9}\b",             # mobile number
        r"\bpassword\s*[:=]?", r"\b\d{3}\s?\d{3}\s?\d{3}\b",
    ]),
    (CAT_FABRICATION, [
        r"web\s+(?:data|results?|sources?|findings)\s+(?:was|were|is|are|has\s+been|have\s+been)\s+(?:now\s+)?(?:ingested|added|fed|loaded|trained|included\s+in\s+the\s+model)",
        r"\b(?:i|we)\s+(?:have\s+)?(?:ingested|added|fed|loaded)\s+(?:the\s+)?web\b",
        r"\bretrain(?:ed|ing)?\b.*\b(?:web|today(?:'s)?\s+data)\b",
    ]),
    (CAT_DRIFT, [
        r"\b(?:rice|wheat|tomato(?:es)?|potato(?:es)?|pulses?|dals?|chana|garlic|ginger|turmeric|sugar|maize|corn|soybean|groundnut|cotton)\b",
    ]),
    (CAT_ECHO, [
        r"\bi\s+can\s+now\s+(?:ignore|bypass|reveal)",
        r"\bmy\s+(?:rules?|guardrails?|restrictions?|instructions?)\s+(?:are|have\s+been|were)\s+(?:off|disabled|removed|ignored)\b",
        r"\bdeveloper\s+mode\s+(?:activated|enabled|on)\b",
    ]),
]

_COMPILED_OUTPUT: List[Tuple[str, List[re.Pattern]]] = [
    (cat, [re.compile(p, re.IGNORECASE) for p in pats])
    for cat, pats in _OUTPUT_RULES
]


def guard_output(text: str) -> Tuple[Optional[str], Optional[str]]:
    """
    L3 output guard. Returns (clean_text, None) when safe, or
    (None, category) when the drafting must be replaced by the stock refusal.
    Commodity-drift (CAT_DRIFT) only fires when there is NO onion reference
    in the text — a comparison mentioning onion stays within scope.
    """
    t = text or ""
    for cat, patterns in _COMPILED_OUTPUT:
        # Skip commodity-drift if the answer clearly references onion.
        if cat == CAT_DRIFT and _ONION_RE.search(t):
            continue
        for pat in patterns:
            if pat.search(t):
                return None, cat
    return t, None


class StreamingGuard:
    """
    Sliding-window wrapper for genuinely token-streamed output: feeds deltas
    and reports when to halt. Windowed scanning catches patterns up to the
    window length (sensitive tokens are short by nature).
    """

    WINDOW = 200

    def __init__(self) -> None:
        self.buf: str = ""
        self.violation: Optional[str] = None

    def feed(self, delta: str) -> bool:
        """True → keep streaming; False → halt, violation recorded."""
        self.buf += delta or ""
        window = self.buf[-self.WINDOW:]
        _, cat = guard_output(window)
        if cat:
            self.violation = cat
            return False
        return True

    @property
    def refusal(self) -> str:
        cat = self.violation or CAT_ECHO
        key = cat if cat != CAT_PII else CAT_PII + "_OUT"
        return REFUSALS.get(key, REFUSALS[CAT_ECHO])
