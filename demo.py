"""
demo.py
--------
Simulates an AI system (e.g. a loan/fraud/content-moderation model) logging
every decision it makes to the AuditLedger, then proves the log is
tamper evident.

Run:
    python3 demo.py/python demo.py
"""

import json

from ledger import AuditLedger

# Fixed, not random, so the demo is reproducible and the tamper step always
# targets a decision that actually changes when edited.
FAKE_TRANSACTIONS = [
    (1001, 245.50, 0.12),
    (1002, 5682.75, 0.35),
    (1003, 12800.00, 0.83),   # this one gets flagged
    (1004, 89.20, 0.05),
    (1005, 7634.55, 0.75),    # this one gets flagged too
]


def fake_ai_decision(txn_id: int, amount: float, risk_score: float):
    """
    Stands in for a real model call. In production this would wrap your
    actual model (a fraud classifier, a content moderator, an approval
    engine, etc.) and log its real output instead of this canned one.
    """
    output = "flagged" if risk_score > 0.7 else "approved"
    reasoning = (
        f"risk_score={risk_score} exceeds 0.70 threshold"
        if output == "flagged"
        else f"risk_score={risk_score} within normal range"
    )
    return {
        "model": "fraud-checker-v1",
        "transaction_id": txn_id,
        "input_summary": f"transfer of ${amount}",
        "output": output,
        "confidence": risk_score,
        "reasoning": reasoning,
    }


def find_first_flagged_block(ledger: AuditLedger):
    for block in ledger.chain:
        if block.decision.get("output") == "flagged":
            return block.index
    return None


def print_chain(ledger: AuditLedger):
    for block in ledger.chain:
        print(f"  Block #{block.index}  hash={block.hash[:16]}...")
        print(f"    previous_hash={block.previous_hash[:16]}...")
        print(f"    decision={json.dumps(block.decision)}")
    print()


def main():
    print("=" * 70)
    print("STEP 1 — An AI model makes decisions; each one is logged to the ledger")
    print("=" * 70)

    ledger = AuditLedger()
    for txn_id, amount, risk_score in FAKE_TRANSACTIONS:
        decision = fake_ai_decision(txn_id, amount, risk_score)
        block = ledger.log_decision(**decision)
        print(f"Logged decision for txn {txn_id}: {decision['output']} "
              f"(confidence {decision['confidence']}) -> block #{block.index}")

    print()
    print_chain(ledger)

    print("=" * 70)
    print("STEP 2 — Verify the ledger is intact (nothing was altered)")
    print("=" * 70)
    print("verify() ->", ledger.verify())
    print()

    ledger.save("chain.json")
    print("Saved chain to chain.json\n")

    print("=" * 70)
    print("STEP 3 — Simulate someone tampering with a past decision")
    print("=" * 70)
    target_index = find_first_flagged_block(ledger)
    print(f"Editing block #{target_index}'s recorded output from 'flagged' to"
          " 'approved' directly in memory (as if someone hand-edited a database"
          " row after the fact)...\n")

    ledger.chain[target_index].decision["output"] = "approved"
    # NOTE: we deliberately do NOT recompute the hash here — that's the point.
    # A real tamperer editing a database row wouldn't know to recompute a
    # cryptographic hash chain either.

    print("verify() ->", ledger.verify())
    tampered_index = ledger.find_tampered_block()
    print(f"find_tampered_block() -> Block #{tampered_index} fails verification")
    print()
    print("This is the core guarantee: once a decision is logged, editing it")
    print("invalidates its hash, which breaks the chain from that point forward.")
    print("Anyone auditing the ledger can immediately see something was changed")
    print("and exactly which record it was.")


if __name__ == "__main__":
    main()
