"""
ledger.py
----------
A minimal, dependency-free blockchain for logging AI model decisions.

Why this exists:
Ethical/regulated AI systems need to prove *why* they made a decision, and
prove that record hasn't been altered after the fact. This gives every AI
decision (input, output, confidence, reasoning) a permanent, tamper-evident
record by chaining each entry to the one before it with a SHA-256 hash --
the same core idea blockchains use for immutability.

Pure Python standard library. No external dependencies.
"""

import hashlib
import json
import time
from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional


@dataclass
class Block:
    index: int
    timestamp: float
    decision: Dict[str, Any]   # the AI decision being logged
    previous_hash: str
    nonce: int = 0
    hash: str = field(default="", init=False)

    def compute_hash(self) -> str:
        """Hash everything except the hash field itself."""
        payload = {
            "index": self.index,
            "timestamp": self.timestamp,
            "decision": self.decision,
            "previous_hash": self.previous_hash,
            "nonce": self.nonce,
        }
        block_string = json.dumps(payload, sort_keys=True).encode()
        return hashlib.sha256(block_string).hexdigest()

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["hash"] = self.hash
        return d


GENESIS_DECISION = {
    "type": "genesis",
    "note": "Ledger initialized. No AI decision recorded in this block.",
}


class AuditLedger:
    """
    An append-only, hash-chained log of AI decisions.

    Usage:
        ledger = AuditLedger()
        ledger.log_decision(model="fraud-checker-v1",
                             input_summary="txn #4471, $12,400 transfer",
                             output="flagged",
                             confidence=0.91,
                             reasoning="amount + velocity exceed threshold")
        ledger.verify()          # -> True
        ledger.save("chain.json")
    """

    def __init__(self):
        genesis = Block(index=0, timestamp=time.time(),
                         decision=GENESIS_DECISION, previous_hash="0")
        genesis.hash = genesis.compute_hash()
        self.chain: List[Block] = [genesis]

    @property
    def last_block(self) -> Block:
        return self.chain[-1]

    def log_decision(self, **decision_fields: Any) -> Block:
        """
        Append a new AI decision to the ledger. Accepts any keyword fields
        describing the decision, e.g.:
            model, input_summary, output, confidence, reasoning
        """
        decision_fields.setdefault("logged_at", time.time())
        new_block = Block(
            index=self.last_block.index + 1,
            timestamp=time.time(),
            decision=decision_fields,
            previous_hash=self.last_block.hash,
        )
        new_block.hash = new_block.compute_hash()
        self.chain.append(new_block)
        return new_block

    def verify(self) -> bool:
        """
        Walk the whole chain and confirm:
          1. each block's stored hash matches a fresh recomputation
             (nobody edited the decision data after the fact)
          2. each block's previous_hash matches the prior block's hash
             (nobody deleted, reordered, or inserted a block)
        Returns True if the ledger is intact, False if tampering is detected.
        """
        for i in range(1, len(self.chain)):
            current = self.chain[i]
            previous = self.chain[i - 1]

            if current.hash != current.compute_hash():
                return False
            if current.previous_hash != previous.hash:
                return False
        return True

    def find_tampered_block(self) -> Optional[int]:
        """Returns the index of the first block that fails verification, or None."""
        for i in range(1, len(self.chain)):
            current = self.chain[i]
            previous = self.chain[i - 1]
            if current.hash != current.compute_hash() or current.previous_hash != previous.hash:
                return current.index
        return None

    def to_list(self) -> List[Dict[str, Any]]:
        return [b.to_dict() for b in self.chain]

    def save(self, path: str) -> None:
        with open(path, "w") as f:
            json.dump(self.to_list(), f, indent=2)

    @classmethod
    def load(cls, path: str) -> "AuditLedger":
        """Load a chain from disk. Restores blocks exactly as stored --
        including their original hash -- so verify() can detect if the
        JSON file itself was hand-edited."""
        with open(path) as f:
            raw = json.load(f)

        ledger = cls.__new__(cls)  # bypass __init__ (don't want a fresh genesis)
        ledger.chain = []
        for item in raw:
            block = Block(
                index=item["index"],
                timestamp=item["timestamp"],
                decision=item["decision"],
                previous_hash=item["previous_hash"],
                nonce=item.get("nonce", 0),
            )
            block.hash = item["hash"]  # trust-but-verify: keep stored hash as-is
            ledger.chain.append(block)
        return ledger
