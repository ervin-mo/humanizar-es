# How to measure

## Grammarly

[grammarly.com/ai-detector](https://www.grammarly.com/ai-detector). This is the detector
the recipe was measured and tuned for.

- **Limit:** on a free account, about 3 scans a day. After that, the button stops starting
  a scan without showing any error. It resets after 24 hours.
- **Clear the box before pasting.** If older text is left below, Grammarly only analyzes
  the first 1,400 words and mixes both versions.
- **Read the big number:** "X% of this text appears to be AI-generated".
- The detector built into Grammarly's document editor, on a free account, always shows
  20%: it can't be used to measure.

- **Texts over ~1,400 words: measure them in two halves.** Otherwise Grammarly only reads
  the beginning.

## GPTZero

[gptzero.me](https://gptzero.me). The free scan reads the first 10,000 characters, and a
free account has a few scans a day ("0 scans left" when they run out).

- **Read "AI X%"**, not the mixed one. "AI 0% · Mixed 1% · Human 99%" means "entirely
  human"; the three always add up to 100%.
- Text past 10,000 characters is not read: scan the rest separately.

## ZeroGPT

[zerogpt.com](https://www.zerogpt.com). No account, 15,000 characters. Reads "X% AI GPT".
The recipe does not pass it yet.

## Always with two controls

In every session, before comparing versions:

1. **A human control:** a text you wrote without AI, of the same kind and similar length.
   It must come out human.
2. **The AI original:** it must come out as AI.

If either fails, the detector isn't measuring that kind of text (QuillBot scored our AI
original 100% human) or it is throttling you (GPTZero, after many scans from one browser,
scored a 1914 text 100% AI). Then its number for your version means nothing. And measure
the reference version again in the same session: don't compare with a number from hours
before.

## Other detectors

They don't agree with each other: a version that passes one may not pass another. If you
care about a detector, measure in that one.
