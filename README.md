# BatchProof

A buying checklist for whoever on a student motorsport team orders the raw material.

Live app: https://aayush-jhawar.github.io/batchproof/

## Why I made this

Last year, our Formula Student EV team at IIT Kanpur needed aluminum sheet in a hurry. We picked sellers from IndiaMART and JustDial, told them the size and thickness, said we wanted good quality, and paid. The sheet failed our 3-point bend test. The replacement took a week, nobody refunded us, and it came from the same kind of listing, so it was just as much of a gamble.

Looking back, the sites' star ratings told us whether a seller replied and shipped, not whether the metal was any good. And half the numbers we called were dead or never picked up, so whatever we figured out about sellers was gone by the next order.

BatchProof doesn't sell anything or list sellers. It just makes you do the few things we skipped when we were rushing, and it remembers how each seller actually did.

## How it works

1. **Spec.** Write down exactly what you need: material, grade, temper, thickness and tolerance, size, quantity, deadline, payment terms, and whether you want the mill test certificate (MTC). If you leave out the temper, skip the MTC, or pay everything upfront, it tells you.
2. **Ask sellers.** You get one message with the full spec to send every seller on WhatsApp. Tick off who replied, who confirmed the grade and temper in writing, and who sent the MTC. It shows which quote is the safest bet, and why the cheapest one might not be.
3. **Check the delivery.** When the sheet arrives, measure the thickness at 5 points (it compares against your tolerance), check the grade marking and the MTC, look it over, add the test result, and accept or reject it.
4. **Seller record.** Every order adds to a running record of who passed, who failed, and who stopped replying. If you pick a seller who failed you before, you'll see it.

It opens with sample data from our sheet order. The seller names and numbers in it are made up.

## Running it

It's a single HTML file. Open `index.html` in a browser or use the link above. There's no build step and no server, and data stays in your browser.

## Tests

`evals/run_evals.py` clicks through the app in headless Chrome at phone size. It runs 11 scenarios based on our real order and 17 edge cases: junk input, empty data, reloading halfway, 300 sellers, blocked storage, readings sitting exactly on the tolerance limit, and so on.

```
pip install playwright && playwright install chromium
python evals/run_evals.py
```

It's at 28/28 now. The first version passed the first 22 easily, which told me the tests were too soft. The harder ones caught four real problems: no way to compare quotes side by side, the seller list cut off on phones, no way to type a grade that wasn't in the list, and closed orders that could still be edited. All four are fixed. Results are in `evals/results.json`.

## What it doesn't do (yet)

- **Sync between phones or teams.** Everything lives in one browser for now. Sharing needs a server, and I'd want a second team to try it first.
- **Ordering or payments.** Ordering was never the hard part. Knowing what would show up was.
- **Other kinds of buyers.** Workshops or electricians might have the same problem, but I haven't asked any of them.

## Credits

The problem is from my own team's order. I worked out what went wrong, decided what the app should and shouldn't do, and reviewed each version. Claude wrote the code and the test script from that. The prompts I used are in my case-study submission.

## License

MIT. Use it however you like.
