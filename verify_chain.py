"""
verify_chain.py
----------------
Independently loads a saved chain.json and checks its integrity.
This simulates an auditor (or a client) checking the ledger later,
in a completely separate process from whatever logged the decisions.

Usage:
    python3 verify_chain.py                 # verifies chain.json
    python3 verify_chain.py path/to/file.json
"""

import sys

from ledger import AuditLedger


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else "chain.json"

    try:
        ledger = AuditLedger.load(path)
    except FileNotFoundError:
        print(f"No such file: {path}")
        print("Run 'python3 demo.py' first to generate one.")
        sys.exit(1)

    print(f"Loaded {len(ledger.chain)} blocks from {path}\n")

    if ledger.verify():
        print("✅ VALID — every decision in this ledger is untampered.")
    else:
        bad_index = ledger.find_tampered_block()
        print(f"❌ TAMPERED — block #{bad_index} does not match its recorded hash.")
        print("   Someone edited a decision (or the chain link) after it was logged.")


if __name__ == "__main__":
    main()
