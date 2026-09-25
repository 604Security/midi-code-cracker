#!/usr/bin/env python3
"""
midi_notes.py
Simple Linux MIDI note decoder for piano keyboards.

Features:
- Lists MIDI input ports
- Reads Note On events
- Decodes MIDI note numbers to piano note names
- Optional CSV logging
- Metasploit-style colored status output
"""

import argparse
import csv
import signal
import sys
import time
from typing import Optional

try:
    import mido
except ImportError:
    print("[-] Missing dependency: mido")
    print("[*] Install with: pip install mido python-rtmidi")
    sys.exit(1)

# ANSI colors
RESET = "\033[0m"
BOLD = "\033[1m"
RED = "\033[31m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
BLUE = "\033[34m"
CYAN = "\033[36m"

NOTE_NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]


def status(label: str, msg: str, color: str = BLUE) -> None:
    print(f"{color}[{label}]{RESET} {msg}")


def banner() -> None:
    print(f"""{CYAN}{BOLD}
 __  __ ___ ____ ___   _   _       _            
|  \\/  |_ _|  _ \\_ _| | \\ | | ___ | |_ ___  ___ 
| |\\/| || || | | | |  |  \\| |/ _ \\| __/ _ \\/ __|
| |  | || || |_| | |  | |\\  | (_) | ||  __/\\__ \\
|_|  |_|___|____/___| |_| \\_|\\___/ \\__\\___||___/

{RESET}""")


def midi_note_to_name(note_number: int) -> str:
    note = NOTE_NAMES[note_number % 12]
    octave = (note_number // 12) - 1
    return f"{note}{octave}"


def list_ports() -> None:
    ports = mido.get_input_names()
    if not ports:
        status("-", "No MIDI input ports found.", RED)
        return

    status("*", "Available MIDI input ports:", GREEN)
    for idx, port in enumerate(ports, start=1):
        print(f"  {idx}. {port}")


def find_port(port_hint: Optional[str]) -> Optional[str]:
    ports = mido.get_input_names()
    if not ports:
        return None

    if not port_hint:
        return ports[0]

    hint_lower = port_hint.lower()

    for port in ports:
        if hint_lower == port.lower():
            return port

    for port in ports:
        if hint_lower in port.lower():
            return port

    return None


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Simple MIDI-to-piano-note decoder for Linux."
    )
    parser.add_argument(
        "-l", "--list",
        action="store_true",
        help="List available MIDI input ports and exit."
    )
    parser.add_argument(
        "-p", "--port",
        help="MIDI input port name or partial match."
    )
    parser.add_argument(
        "--csv",
        metavar="FILE",
        help="Write pressed notes to CSV."
    )
    parser.add_argument(
        "--raw",
        action="store_true",
        help="Also show raw MIDI note number."
    )
    args = parser.parse_args()

    banner()

    if args.list:
        list_ports()
        return

    port_name = find_port(args.port)
    if not port_name:
        status("-", "Could not find a MIDI input port.", RED)
        status("*", "Run with --list to see available ports.", YELLOW)
        sys.exit(1)

    csv_file = None
    csv_writer = None

    if args.csv:
        csv_file = open(args.csv, "w", newline="", encoding="utf-8")
        csv_writer = csv.writer(csv_file)
        csv_writer.writerow(["timestamp", "note_number", "note_name", "velocity"])
        status("+", f"CSV logging enabled: {args.csv}", GREEN)

    stop = False

    def handle_sigint(sig, frame):
        nonlocal stop
        stop = True
        status("*", "Stopping...", YELLOW)

    signal.signal(signal.SIGINT, handle_sigint)

    status("+", f"Opening MIDI port: {port_name}", GREEN)
    status("*", "Press piano keys. Only Note On events will be shown.", BLUE)

    try:
        with mido.open_input(port_name) as inport:
            while not stop:
                for msg in inport.iter_pending():
                    # Ignore everything except actual key presses
                    if msg.type == "note_on" and getattr(msg, "velocity", 0) > 0:
                        note_name = midi_note_to_name(msg.note)
                        ts = time.strftime("%Y-%m-%d %H:%M:%S")

                        if args.raw:
                            print(f"{GREEN}[NOTE]{RESET} {note_name}  raw={msg.note}  velocity={msg.velocity}")
                        else:
                            print(f"{GREEN}[NOTE]{RESET} {note_name}")

                        if csv_writer:
                            csv_writer.writerow([ts, msg.note, note_name, msg.velocity])
                            csv_file.flush()

                time.sleep(0.01)

    except KeyboardInterrupt:
        pass
    except Exception as exc:
        status("-", f"Runtime error: {exc}", RED)
        sys.exit(1)
    finally:
        if csv_file:
            csv_file.close()
        status("+", "Done.", GREEN)


if __name__ == "__main__":
    main()
