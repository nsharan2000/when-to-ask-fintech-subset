#!/bin/bash
# askbc.sh — fixed-path wrapper for the Critical API Understanding for AI Agents research SIMULATION CLI. No real backend, money, data or infrastructure is involved.
# Runs from any working directory; relative --scenarios / --run paths resolve against the caller's cwd.
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHONPATH="$DIR${PYTHONPATH:+:$PYTHONPATH}" ASKBC_CLI="$DIR/askbc.sh" exec python3 -m askbc.cli "$@"
