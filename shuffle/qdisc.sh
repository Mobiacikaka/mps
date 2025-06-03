#!/bin/bash

if [[ $EUID -ne 0 ]]; then
  echo "This script requires root privileges. Please run with sudo."
  exit 1
fi



# Delete any existing qdisc on lo
tc qdisc del dev lo root 2> /dev/null || true



# 2.1) Add root HTB handle “1:” on loopback
tc qdisc add dev lo root handle 1: htb

# 2.2) Create Class 1:1 → “no extra delay” (this is the default fallback)
tc class add dev lo parent 1: classid 1:1 htb rate 1000mbit



# ─── Class for u1 → u2 (100 ms) ──────────────────────────────────────────────────────
#  Class 1:2 can send at full speed, but we attach `netem`→100 ms delay.
tc class add dev lo parent 1: classid 1:2 htb rate 1000mbit
tc qdisc add dev lo parent 1:2 handle 2: netem delay 100ms

# ─── Class for u2 → u1 (100 ms) ──────────────────────────────────────────────────────
tc class add dev lo parent 1: classid 1:3 htb rate 1000mbit
tc qdisc add dev lo parent 1:3 handle 3: netem delay 100ms

# ─── Class for u1 → u3 (120 ms) ──────────────────────────────────────────────────────
tc class add dev lo parent 1: classid 1:4 htb rate 1000mbit
tc qdisc add dev lo parent 1:4 handle 4: netem delay 120ms

# ─── Class for u3 → u1 (120 ms) ──────────────────────────────────────────────────────
tc class add dev lo parent 1: classid 1:5 htb rate 1000mbit
tc qdisc add dev lo parent 1:5 handle 5: netem delay 120ms

# ─── Class for u2 → u3 (140 ms) ──────────────────────────────────────────────────────
tc class add dev lo parent 1: classid 1:6 htb rate 1000mbit
tc qdisc add dev lo parent 1:6 handle 6: netem delay 140ms

# ─── Class for u3 → u2 (140 ms) ──────────────────────────────────────────────────────
tc class add dev lo parent 1: classid 1:7 htb rate 1000mbit
tc qdisc add dev lo parent 1:7 handle 7: netem delay 140ms



# ─── u1 (port 5001) → u2 (port 5002)  : class 1:2 ─────────────────────────────────
tc filter add dev lo protocol ip parent 1: prio 1 u32 \
    match ip src   127.0.0.1/32 \
    match ip dst   127.0.0.1/32 \
    match ip sport 5001 0xffff \
    match ip dport 5002 0xffff \
    flowid 1:2

# ─── u2 (port 5002) → u1 (port 5001)  : class 1:3 ─────────────────────────────────
tc filter add dev lo protocol ip parent 1: prio 1 u32 \
    match ip src   127.0.0.1/32 \
    match ip dst   127.0.0.1/32 \
    match ip sport 5002 0xffff \
    match ip dport 5001 0xffff \
    flowid 1:3

# ─── u1 (port 5001) → u3 (port 5003)  : class 1:4 ─────────────────────────────────
tc filter add dev lo protocol ip parent 1: prio 1 u32 \
    match ip src   127.0.0.1/32 \
    match ip dst   127.0.0.1/32 \
    match ip sport 5001 0xffff \
    match ip dport 5003 0xffff \
    flowid 1:4

# ─── u3 (port 5003) → u1 (port 5001)  : class 1:5 ─────────────────────────────────
tc filter add dev lo protocol ip parent 1: prio 1 u32 \
    match ip src   127.0.0.1/32 \
    match ip dst   127.0.0.1/32 \
    match ip sport 5003 0xffff \
    match ip dport 5001 0xffff \
    flowid 1:5

# ─── u2 (port 5002) → u3 (port 5003)  : class 1:6 ─────────────────────────────────
tc filter add dev lo protocol ip parent 1: prio 1 u32 \
    match ip src   127.0.0.1/32 \
    match ip dst   127.0.0.1/32 \
    match ip sport 5002 0xffff \
    match ip dport 5003 0xffff \
    flowid 1:6

# ─── u3 (port 5003) → u2 (port 5002)  : class 1:7 ─────────────────────────────────
tc filter add dev lo protocol ip parent 1: prio 1 u32 \
    match ip src   127.0.0.1/32 \
    match ip dst   127.0.0.1/32 \
    match ip sport 5003 0xffff \
    match ip dport 5002 0xffff \
    flowid 1:7
