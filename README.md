# MIDI Code Cracker

**MegaSpy's Piano Code Cracking**: a kid-friendly, Mastermind-style game played on a MIDI piano keyboard.

The game picks a secret 4-note code from the white keys (C D E F G A B, no repeats). Play 4 notes to guess it and get spy clues back:

- 🟢 correct note, right spot
- 🟡 note is in the code, and which position it belongs in
- 🔴 note is not in the code

Crack the code and the victory screen appears, the computer speaks a message, and a clue picture opens. That picture can lead to the next step of a treasure hunt.

## Requirements

- Linux with a USB/MIDI piano keyboard (tested with a P-Series keyboard)
- Python 3.8+
- Optional: `espeak-ng` (spoken message), `xdg-open`/`feh` (show the clue picture)

## Install

```bash
git clone https://github.com/604Security/midi-code-cracker.git
cd midi-code-cracker
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
sudo apt install espeak-ng   # optional
```

## Play

```bash
./megaspy.py                 # auto-picks a P-Series port, else the first MIDI input
./megaspy.py --port "Piano"  # choose a port by name or partial match
```

To quit, type `Q` then Enter.

### Operator (parent) controls

| While playing | Effect |
|---|---|
| `H` + Enter | Show the secret code |
| `W` + Enter | Force a win |

| Flag | Effect |
|---|---|
| `--debug` / `--cheat-on-start` | Print the code at startup |
| `--auto-win-after N` | Win automatically after N failed guesses |
| `--force-win` | Skip straight to the victory + clue (handy for testing) |

## Setting up your clue

When the game is won it runs `clue.sh`, which opens `clue.jpg` from the repo folder. Clue images are git-ignored so personal pictures stay local.

```bash
cp ~/Pictures/next-clue.jpg clue.jpg
# or point at any image:
CLUE_IMAGE=~/Pictures/next-clue.jpg ./megaspy.py
```

Edit `clue.sh` to change the spoken message or do something else on a win.

## Checking your keyboard

`midi_notes.py` lists MIDI ports and prints each key you press. Use it to confirm the piano is detected:

```bash
./midi_notes.py --list
./midi_notes.py --port "Piano" --raw
./midi_notes.py --csv notes.csv
```

## License

MIT

