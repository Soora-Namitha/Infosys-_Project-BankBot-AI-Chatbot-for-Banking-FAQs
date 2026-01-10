"""
Rule-based entity extractor for BANKBOT.
Extracts: amount, currency, account_number, transaction_id, location keywords.
"""


import re
from typing import Dict, Any, List, Tuple



class EntityExtractor:
    def __init__(self):
        # Transaction id patterns like: TXN 12345, txn id: 12-34-ABC, UTR: ABC123456
        self.txn_patterns = [
            re.compile(
                r'\b(?:txn|transaction|utr|ref(?:erence)?)[\s#:]*([A-Z0-9\-]{4,20})',
                flags=re.IGNORECASE,
            ),
        ]


        # Account number when context words appear near digits
        self.account_patterns = [
            re.compile(
                r'\b(?:account|acct|a/c|a\.c\.|acc)\b[^0-9]{0,10}(\d{6,18})',
                flags=re.IGNORECASE,
            ),
            re.compile(
                r'(\d{6,18})[^0-9]{0,10}\b(?:account|acct|a/c|a\.c\.|acc)\b',
                flags=re.IGNORECASE,
            ),
        ]


        # Currency + amount (₹, Rs, INR, $, dollars, rupees, etc.)
        self.amount_patterns = [
            re.compile(
                r'\b(?:₹|rs\.?|inr|\$|usd|dollars?|rupees?)\s*([0-9][0-9,]*(?:\.[0-9]{1,2})?)',
                flags=re.IGNORECASE,
            ),
            re.compile(
                r'([0-9][0-9,]*(?:\.[0-9]{1,2})?)\s*(?:₹|rs\.?|inr|\$|usd|dollars?|rupees?)\b',
                flags=re.IGNORECASE,
            ),
        ]


        # Fallback: plain numeric amount without explicit currency
        self.plain_amount_pattern = re.compile(
            r'\b[0-9][0-9,]*(?:\.[0-9]{1,2})?\b'
        )


        # Simple location keywords used in banking examples
        self.location_keywords = [
            "near me",
            "nearby",
            "bangalore",
            "whitefield",
            "mg road",
            "airport",
        ]


        # Generic number pattern (only used with context, not labelled alone)
        self.number_pattern = re.compile(r'\b[0-9]{2,20}\b')


    # ---------- internal helpers ----------


    def _reserve_span(self, reserved: List[Tuple[int, int]], start: int, end: int) -> bool:
        """Return True and record span if it does not overlap existing ones."""
        for s, e in reserved:
            if not (end <= s or start >= e): 

                return False 
        reserved.append((start, end))
        return True


    def _normalize_amount(self, raw: str) -> float:
        """Convert raw numeric text with commas to float."""
        cleaned = raw.replace(",", "")
        try:
            return float(cleaned)
        except ValueError:
            return 0.0


    # ---------- main API ----------


    def extract(self, text: str) -> Dict[str, Any]:
        entities: Dict[str, Any] = {}
        reserved: List[Tuple[int, int]] = []


        # Transaction IDs
        for pattern in self.txn_patterns:
            for m in pattern.finditer(text):
                if self._reserve_span(reserved, m.start(1), m.end(1)):
                    entities.setdefault("transaction_id", []).append(m.group(1))


        # Account numbers
        for pattern in self.account_patterns:
            for m in pattern.finditer(text):
                if self._reserve_span(reserved, m.start(1), m.end(1)):
                    entities.setdefault("account_number", []).append(m.group(1))


        # Amount + currency
        for pattern in self.amount_patterns:
            for m in pattern.finditer(text):
                if self._reserve_span(reserved, m.start(1), m.end(1)):
                    amount_val = self._normalize_amount(m.group(1))
                    entities.setdefault("amount", []).append(amount_val)


        # Fallback: bare numeric amount if no currency+amount found
        if "amount" not in entities:
            for m in self.plain_amount_pattern.finditer(text):
                if self._reserve_span(reserved, m.start(), m.end()):
                    amount_val = self._normalize_amount(m.group(0))
                    entities.setdefault("amount", []).append(amount_val)
                    break  # use first bare number as amount


        # Location keywords (very simple, can later be replaced with spaCy NER)
        lowered = text.lower()
        for loc in self.location_keywords:
            idx = lowered.find(loc)
            if idx != -1 and self._reserve_span(reserved, idx, idx + len(loc)):
                entities.setdefault("location", []).append(loc)


        return entities



# Simple wrapper so other modules can do: from nlu_engine.entity_extractor import extract
def extract(text: str) -> Dict[str, Any]:
    ex = EntityExtractor()
    return ex.extract(text)