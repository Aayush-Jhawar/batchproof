# BatchProof

A buying checklist for the person on a student motorsport team who orders raw material.

**Live app:** https://aayush-jhawar.github.io/batchproof/

## Why this exists

Last month our Formula Bharat team (IIT Kanpur) needed aluminium sheet urgently. We found sellers on IndiaMART and JustDial, told them the dimensions, thickness and "quality", and paid. The first batch failed our 3-point bend test. Getting a replacement took a week, there was no refund, and the replacement came from the same kind of listing, so there was no guarantee it would be any better.

The listings have star ratings, but a rating tells you a seller shipped something. It doesn't tell you whether the metal passed. On top of that, half the numbers we called were dead or never replied, so whatever we learned about sellers was lost by the next order.

BatchProof doesn't sell anything or list sellers. It makes the buyer do the few things we skipped under time pressure, and it remembers how each seller actually did.

## What it does

1. **Spec.** You write the exact spec: material, grade, temper, thickness and tolerance, size, quantity, need-by date, payment terms, and whether the mill test certificate (MTC) is required. It warns you if the temper is missing, the MTC is off, or you're paying full advance.
2. **Ask sellers.** It turns the spec into one message, and every seller gets the same words on WhatsApp. You tick who replied, who confirmed the grade and temper in writing, and who sent the MTC. A comparison card says which quote is safest and why the cheapest one might not be.
3. **Delivery check.** When the batch arrives, you enter thickness at 5 points (checked against the tolerance), grade marking, MTC match, a visual check and the test result, then accept or reject.
4. **Seller record.** Pass/fail results and reply rates are built from your own purchases. Sellers who failed before are flagged when you pick them again, and numbers that stopped replying are marked.

It opens with sample data based on our sheet order. The seller names and numbers in it are made up.

## Run it

It's one HTML file with no build step and no backend. Open `index.html` in a browser, or use the live link above. Data is saved in your browser's local storage.

## Evals

`evals/run_evals.py` drives the app in headless Chrome at phone size: 11 core scenarios from the real order and 17 edge cases (bad input, empty data, reload, 300 sellers, blocked storage, values on the tolerance limit, and more).

```
pip install playwright && playwright install chromium
python evals/run_evals.py
```

The current version passes 28/28. The first version passed my first 22. After I reviewed screenshots and added harder cases, 4 failed (no quote comparison, sellers list cut off on phones, no way to type a grade not in the list, closed specs still editable), and those were fixed. Results are in `evals/results.json`.

## Not in scope (yet)

- **Sharing across phones / teams.** Data lives in one browser. A shared record needs a backend and a second team to test with.
- **Ordering or paying in the app.** The problem is trust in what arrives, not placing the order.
- **Buyers other than student teams.** Workshops, electricians and service centres might have the same problem, but I haven't talked to any of them.

## Who did what

Problem, user research and product decisions: Aayush Jhawar. Built and tested with Claude (Anthropic), working from my problem statement, interview notes and review. The full prompt log is part of the case-study submission.

## License

MIT
