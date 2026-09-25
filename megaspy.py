#!/usr/bin/env python3

import argparse
import os
import random
import select
import signal
import subprocess
import sys
import time

import mido

# ============================================================
# CONFIG
# ============================================================

WHITE_NOTES = {
    0: "C",
    2: "D",
    4: "E",
    5: "F",
    7: "G",
    9: "A",
    11: "B",
}

ALLOWED_NOTES = ["C", "D", "E", "F", "G", "A", "B"]
CLUE_SCRIPT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "clue.sh")

# ============================================================
# ANSI COLORS / STATUS
# ============================================================

RESET = "\033[0m"
BOLD = "\033[1m"
RED = "\033[31m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
CYAN = "\033[36m"

def info(msg):
    print(f"{CYAN}[*]{RESET} {msg}")

def good(msg):
    print(f"{GREEN}[+]{RESET} {msg}")

def warn(msg):
    print(f"{YELLOW}[!]{RESET} {msg}")

def bad(msg):
    print(f"{RED}[-]{RESET} {msg}")

# ============================================================
# ASCII ART
# ============================================================

def banner():
    print(f"""{CYAN}{BOLD}
 __  __                        ____             
|  \\/  | ___  __ _  __ _  __ _/ ___| _ __  _   _ 
| |\\/| |/ _ \\/ _` |/ _` |/ _` \\___ \\| '_ \\| | | |
| |  | |  __/ (_| | (_| | (_| |___) | |_) | |_| |
|_|  |_|\\___|\\__, |_|\\__,_|\\__,_|____/| .__/ \\__, |
             |___/                    |_|    |___/

   ____          _        ____                _    _             
  / ___|___   __| | ___  / ___|_ __ __ _  ___| | _(_)_ __   __ _ 
 | |   / _ \\ / _` |/ _ \\| |   | '__/ _` |/ __| |/ / | '_ \\ / _` |
 | |__| (_) | (_| |  __/| |___| | | (_| | (__|   <| | | | | (_| |
  \\____\\___/ \\__,_|\\___| \\____|_|  \\__,_|\\___|_|\\_\\_|_| |_|\\__, |
                                                           |___/

=========================================================
             MEGASPY'S PIANO CODE CRACKING
=========================================================
Crack the 4-note secret code using the piano.
Allowed notes: C D E F G A B
Black keys are ignored.
Press Q then Enter to quit.
=========================================================
{RESET}""")

def victory_banner():
    print(f"""{GREEN}{BOLD}
 __     ___ _____ _____ ___  ______   __
 \\ \\   / (_) ____|_   _/ _ \\|  _ \\ \\ / /
  \\ \\ / /| |  _|   | || | | | |_) \\ V / 
   \\ V / | | |___  | || |_| |  _ < | |  
    \\_/  |_|_____| |_| \\___/|_| \\_\\|_|  

    _    ____ ____ _____ ____ ____    ____ ____      _    _   _ _____ _____ ____
   / \\  / ___/ ___| ____/ ___/ ___|  / ___|  _ \\    / \\  | \\ | |_   _| ____|  _ \\
  / _ \\| |  | |   |  _| \\___ \\___ \\ | |  _| |_) |  / _ \\ |  \\| | | | |  _| | | | |
 / ___ \\ |__| |___| |___ ___) |__) || |_| |  _ <  / ___ \\| |\\  | | | | |___| |_| |
/_/   \\_\\____\\____|_____|____/____/  \\____|_| \\_\\/_/   \\_\\_| \\_| |_| |_____|____/

=========================================================
              ACCESS GRANTED, AGENT MEGASPY
=========================================================
{RESET}""")

# ============================================================
# GLOBAL STATE
# ============================================================

RUNNING = True

def handle_sigint(signum, frame):
    global RUNNING
    RUNNING = False
    print()
    warn("Caught Ctrl+C. Exiting MegaSpy cleanly...")

signal.signal(signal.SIGINT, handle_sigint)

# ============================================================
# MIDI / GAME LOGIC
# ============================================================

def midi_note_to_letter(note_number):
    return WHITE_NOTES.get(note_number % 12)

def generate_code():
    return random.sample(ALLOWED_NOTES, 4)

def choose_port(port_hint=None):
    ports = mido.get_input_names()

    if not ports:
        raise RuntimeError("No MIDI input ports found.")

    if port_hint:
        hint = port_hint.lower()
        for port in ports:
            if hint == port.lower():
                return port
        for port in ports:
            if hint in port.lower():
                return port
        raise RuntimeError(f"Requested port not found: {port_hint}")

    for port in ports:
        if "P-Series" in port:
            return port

    return ports[0]

def flush_pending(inport):
    for _ in inport.iter_pending():
        pass

def read_stdin_line_nonblocking():
    if select.select([sys.stdin], [], [], 0)[0]:
        return sys.stdin.readline().strip().upper()
    return None

def run_clue_script():
    try:
        good(f"Executing clue script: {CLUE_SCRIPT}")
        result = subprocess.run([CLUE_SCRIPT], check=True)
        good(f"clue.sh exited with status {result.returncode}")
    except FileNotFoundError:
        bad(f"clue script not found: {CLUE_SCRIPT}")
    except PermissionError:
        bad(f"clue script is not executable: {CLUE_SCRIPT}")
        warn(f"Try: chmod +x {CLUE_SCRIPT}")
    except subprocess.CalledProcessError as exc:
        bad(f"clue.sh exited with non-zero status: {exc.returncode}")

def handle_win(code, attempts, forced=False):
    victory_banner()

    if forced:
        warn("Victory path triggered via operator override.")

    good(f"Solved in {attempts} attempt(s)")
    good(f"Secret code: {' '.join(code)}")

    run_clue_script()
    return 0

def read_sequence(inport, code):
    global RUNNING

    print()
    info("Play 4 piano notes for your guess")
    info("Waiting for notes...")

    flush_pending(inport)
    sequence = []

    while len(sequence) < 4 and RUNNING:
        user_input = read_stdin_line_nonblocking()

        if user_input:
            if user_input == "Q":
                RUNNING = False
                warn("Quit requested by operator.")
                return None

            elif user_input == "H":
                warn(f"CHEAT CODE: {' '.join(code)}")
                continue

            elif user_input == "W":
                warn("FORCE WIN TRIGGERED")
                return "__FORCE_WIN__"

        for msg in inport.iter_pending():
            if msg.type == "note_on" and msg.velocity > 0:
                note = midi_note_to_letter(msg.note)

                if note is None:
                    warn("Ignored black key")
                    continue

                position = len(sequence) + 1
                good(f"Position {position}: {note}")
                sequence.append(note)

                if len(sequence) == 4:
                    break

        time.sleep(0.01)

    if not RUNNING:
        return None

    return sequence

def evaluate_guess(code, guess):
    feedback = [None] * 4
    remaining_code = []
    remaining_guess = []

    for i in range(4):
        if guess[i] == code[i]:
            feedback[i] = ("correct", guess[i], i)
        else:
            remaining_code.append((i, code[i]))
            remaining_guess.append((i, guess[i]))

    used_code_indexes = set()

    for guess_index, guess_note in remaining_guess:
        found = None

        for code_index, code_note in remaining_code:
            if code_index in used_code_indexes:
                continue
            if guess_note == code_note:
                found = code_index
                break

        if found is not None:
            feedback[guess_index] = ("wrong_place", guess_note, found)
            used_code_indexes.add(found)
        else:
            feedback[guess_index] = ("wrong", guess_note, None)

    return feedback

def print_feedback(feedback):
    print()
    info("Spy clues:")

    for idx, item in enumerate(feedback, start=1):
        status, note, target_pos = item

        if status == "correct":
            good(f"[{idx}] {note} = correct and in the right spot")
        elif status == "wrong_place":
            warn(f"[{idx}] {note} = in the code, but belongs in position {target_pos + 1}")
        else:
            bad(f"[{idx}] {note} = not in the code")

# ============================================================
# MAIN
# ============================================================

def build_arg_parser():
    parser = argparse.ArgumentParser(
        description="MegaSpy Piano Code Cracking - kid-friendly MIDI note guessing game"
    )
    parser.add_argument(
        "--port",
        help="MIDI input port name or partial match"
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Show the secret code at startup"
    )
    parser.add_argument(
        "--force-win",
        action="store_true",
        help="Immediately trigger the victory path and execute clue.sh"
    )
    parser.add_argument(
        "--cheat-on-start",
        action="store_true",
        help="Print the secret code once at startup"
    )
    parser.add_argument(
        "--auto-win-after",
        type=int,
        metavar="N",
        help="Automatically trigger the victory path after N failed guesses"
    )
    return parser

def main():
    global RUNNING

    parser = build_arg_parser()
    args = parser.parse_args()

    if args.auto_win_after is not None and args.auto_win_after < 0:
        bad("--auto-win-after must be 0 or greater")
        return 1

    banner()

    code = generate_code()
    attempts = 0
    failed_attempts = 0

    if args.debug:
        warn(f"DEBUG CODE: {' '.join(code)}")

    if args.cheat_on_start:
        warn(f"CHEAT CODE: {' '.join(code)}")

    if args.force_win:
        return handle_win(code, attempts, forced=True)

    try:
        port = choose_port(args.port)
    except Exception as exc:
        bad(str(exc))
        return 1

    good(f"Using MIDI port: {port}")

    try:
        with mido.open_input(port) as inport:
            while RUNNING:
                guess = read_sequence(inport, code)

                if not RUNNING or guess is None:
                    break

                if guess == "__FORCE_WIN__":
                    return handle_win(code, attempts, forced=True)

                attempts += 1
                info(f"Guess: {' '.join(guess)}")

                if guess == code:
                    return handle_win(code, attempts)

                failed_attempts += 1
                print_feedback(evaluate_guess(code, guess))
                info("Try again, MegaSpy.")

                if (
                    args.auto_win_after is not None
                    and failed_attempts >= args.auto_win_after
                ):
                    warn(
                        f"Auto-win threshold reached after "
                        f"{failed_attempts} failed attempt(s)."
                    )
                    return handle_win(code, attempts, forced=True)

    except KeyboardInterrupt:
        warn("Keyboard interrupt received. Exiting...")
    except Exception as exc:
        bad(f"Runtime error: {exc}")
        return 1

    info("MegaSpy session ended.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
