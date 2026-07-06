# AI Decision Audit Ledger

A small prototype that logs every decision an AI system makes into a
tamper evident record. If someone edits a past decision later, the log
proves it happened and shows exactly which one.

No installs, no internet, no libraries. Just Python.

---

## What's in this folder

| File | What it's for |
|---|---|
| `ledger.py` | The core logic |
| `demo.py` | Run this first: it shows the whole idea in action |
| `verify_chain.py` | A quick checker you run afterward |

---

## Before you start

You just need Python 3 installed. Check by running:

```bash
python3 --version
```

If you see a version number (like `Python 3.11.2`), you're ready.
If that command isn't found, try `python --version` instead.

---

## Testing it — 3 easy steps

**Step 1: Run the demo**

```bash
python demo.py
```

Watch for these things in the output:
- 5 fake AI decisions get logged, one by one
- `verify() -> True` — meaning the log is untouched
- A message that it saved a file called `chain.json`
- A simulated "tampering" attempt on one decision
- `verify() -> False` — now it correctly detects the tampering

That's the whole point of the tool: it can tell when something was changed.

**Step 2: Double-check the saved file**

```bash
python verify_chain.py
```

You should see:
```
✅ VALID — every decision in this ledger is untampered.
```

**Step 3: Try to fool it yourself**

1. Open `chain.json` in any text editor (Notepad, TextEdit, VS Code — anything).
2. Find a line that says `"output": "flagged"` and change it to `"output": "approved"`.
3. Save the file.
4. Run the checker again:

```bash
python verify_chain.py
```

You should now see:
```
❌ TAMPERED — block #N does not match its recorded hash.
```

That's it — you just proved the log catches edits, even a single word changed
by hand in a text editor.

---

## Why this matters

This is the same core idea blockchains use to make records tamper-proof.
Here it's applied to AI: every prediction, flag, or approval an AI system
makes gets a permanent, checkable paper trail — useful for anything where
you need to prove an AI didn't quietly change its story after the fact
(fraud checks, content moderation, loan approvals, etc.).

This is a proof-of-concept, not a production blockchain — there's no
network of nodes or consensus here, just the hashing/chaining core that
those systems are built on top of.

---

## Using it with a real AI model

Instead of the fake decisions in `demo.py`, log your model's real output:

```python
from ledger import AuditLedger

ledger = AuditLedger()

ledger.log_decision(
    model="yourmodelname",
    input_summary="short description of the input (avoid personal data )",
    output=model_output,
    confidence=model_confidence,
    reasoning=explanation_string,
)

ledger.save("production_chain.json")
```

## Ideas for extending this

- Store the chain in a real database instead of a JSON file
- Add a signature per entry, so you know *who* logged each decision
- Anchor the chain to a public blockchain (Ethereum, Polygon, etc.) for outside verification
- Turn `log_decision` into an API endpoint any model can call
