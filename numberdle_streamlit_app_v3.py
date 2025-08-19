# numberdle_app.py
# Minimal, clean Numberdle (00000'9699999), 6 tries
# Run: streamlit run numberdle_app.py

import random
from typing import List, Tuple
import streamlit as st

st.set_page_config(page_title="Numberdle", layout="centered")

# ============================ Utilities ============================

def new_secret() -> str:
    return f"{random.randint(0, 99999):05d}"

def evaluate_guess(secret: str, guess: str):
    """Return ['green'|'yellow'|'gray'] x 5 with duplicate handling."""
    n = 5
    status = ["gray"] * n
    remain = {}
    for i in range(n):
        s, g = secret[i], guess[i]
        if g == s:
            status[i] = "green"
        else:
            remain[s] = remain.get(s, 0) + 1
    for i in range(n):
        if status[i] == "green":
            continue
        g = guess[i]
        if remain.get(g, 0) > 0:
            status[i] = "yellow"
            remain[g] -= 1
    return status

def clamp_range_around_guess(guess: str, secret: str) -> Tuple[int, int]:
    g, s = int(guess), int(secret)
    lo, hi = min(g, s), max(g, s)
    pad = max(50, (hi - lo) // 5)
    return max(0, lo - pad), min(99999, hi + pad)

def gen_clues(secret: str, guess: str, round_idx: int):
    rng = random.Random(hash((secret, round_idx)) & 0xFFFFFFFF)
    s_digits = list(map(int, secret))
    s_val = int(secret)
    clues = []
    lo, hi = clamp_range_around_guess(guess, secret)
    clues.append(f"The number is between {lo:05d} and {hi:05d}.")
    clues.append("It is an even number." if s_val % 2 == 0 else "It is an odd number.")
    clues.append(f"Sum of digits uc0u8801  {sum(s_digits) % 3} (mod 3).")
    i, j = rng.choice([(0,1),(1,2),(2,3),(3,4)])
    rel = "<" if s_digits[i] < s_digits[j] else (">" if s_digits[i] > s_digits[j] else "=")
    clues.append(f"Digit {i+1} {rel} digit {j+1}.")
    clues.append("At least one digit repeats." if len(set(secret)) < 5 else "All digits are distinct.")
    pick = rng.sample(range(len(clues)), k=2)
    return [clues[k] for k in sorted(pick)]

def clean_digits(s: str) -> str:
    return "".join(ch for ch in s if ch.isdigit())[:5]

# ============================ State ============================

def init_state():
    st.session_state.secret = new_secret()
    st.session_state.round = 0
    st.session_state.grid = [["" for _ in range(5)] for _ in range(6)]
    st.session_state.status = [["" for _ in range(5)] for _ in range(6)]
    st.session_state.done = False
    st.session_state.win = False
    st.session_state.hints = [[] for _ in range(6)]
    st.session_state.rowbuf = ""
    st.session_state.error = ""

if "secret" not in st.session_state:
    init_state()

def ensure_row_is_list(r: int):
    row = st.session_state.grid[r]
    if not isinstance(row, list) or len(row) != 5:
        st.session_state.grid[r] = [""] * 5
    else:
        for i in range(5):
            if not isinstance(st.session_state.grid[r][i], str):
                st.session_state.grid[r][i] = str(st.session_state.grid[r][i])

def sync_buf_to_grid(r: int):
    ensure_row_is_list(r)
    buf = st.session_state.rowbuf
    row = st.session_state.grid[r]
    for i in range(5):
        row[i] = buf[i] if i < len(buf) else ""

def submit_guess():
    if st.session_state.done:
        return
    buf = st.session_state.rowbuf
    if len(buf) != 5:
        st.session_state.error = "Enter exactly 5 digits."
        return
    guess = buf
    secret = st.session_state.secret
    st.session_state.status[st.session_state.round] = evaluate_guess(secret, guess)
    if guess == secret:
        st.session_state.done = True
        st.session_state.win = True
        st.session_state.error = ""
    else:
        st.session_state.hints[st.session_state.round] = gen_clues(secret, guess, st.session_state.round)
        st.session_state.round += 1
        st.session_state.rowbuf = ""
        st.session_state.error = ""
        if st.session_state.round >= 6:
            st.session_state.done = True

# ============================ Styles ============================

st.markdown(
    """
    <style>
      .title {text-align:center; font-weight:800; font-size:2rem; margin: 0.2rem 0 0.2rem;}
      .subtle {text-align:center; color:#6b7280; margin-bottom: 0.8rem;}
      .board {display:grid; grid-template-columns: repeat(5, 60px); gap:10px; justify-content:center; margin: 12px 0 14px;}
      .tile {height:60px; width:60px; border-radius:10px; display:flex; align-items:center; justify-content:center;
             font-size:1.4rem; font-weight:800; border:2px solid #e5e7eb; background:#f9fafb; color:#111827;}
      .green {background:#16a34a; color:#fff; border-color:#16a34a;}
      .yellow {background:#f59e0b; color:#fff; border-color:#f59e0b;}
      .gray {background:#9ca3af; color:#fff; border-color:#9ca3af;}
      .neutral {}
      .hint {background:#f3f4f6; border-radius:10px; padding:8px 10px; margin:6px 0;}
      .center {display:flex; align-items:center; justify-content:center; gap:10px;}
      .stTextInput>div>div>input {text-align:center; font-size:1.1rem; font-weight:700;}

      /* NEW: side-by-side hints (single row, 6 columns) */
      .hints-grid {
        display: grid;
        grid-template-columns: repeat(6, 1fr);
        gap: 12px;
        justify-content: center;
        align-items: start;
        margin-top: 8px;
      }
      .hintcard {
        background: #f3f4f6;
        border: 1px solid #e5e7eb;
        border-radius: 10px;
        padding: 10px 12px;
        height: 100%;
      }
      .hinttitle {
        text-align: center;
        font-weight: 700;
        margin-bottom: 6px;
        font-size: 0.9rem;
        color: #374151;
      }
      .hintline {
        font-size: 0.95rem;
        color: #111827;
      }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown('<div class="title">Numberdle</div>', unsafe_allow_html=True)
st.markdown('<div class="subtle">Guess the 5-digit number (00000-99999). 6 tries.</div>', unsafe_allow_html=True)

# ============================ Controls ============================

c1, c2, c3 = st.columns([1,1,1])
if c1.button("New Game", use_container_width=True):
    init_state()
    st.rerun()
if c2.button("Give Up", use_container_width=True):
    st.session_state.done = True
    st.session_state.win = False
if st.session_state.done and not st.session_state.win:
    c3.info(f"Answer: {st.session_state.secret}")

# ============================ Board ============================

current_round = st.session_state.round
if not st.session_state.done:
    sync_buf_to_grid(current_round)  # keep active row tiles in sync

# Build the entire board HTML once (prevents the 30-tiles-in-a-column issue)
tiles_html = []
for r in range(6):
    ensure_row_is_list(r)
    for c in range(5):
        val = st.session_state.grid[r][c]
        status = st.session_state.status[r][c]
        css = status if status in {"green", "yellow", "gray"} else "neutral"
        tiles_html.append(f"<div class='tile {css}'>{val or '&nbsp;'}</div>")
board_html = "<div class='board'>" + "".join(tiles_html) + "</div>"
st.markdown(board_html, unsafe_allow_html=True)

# ===================== Single Input + Submit =====================

with st.form(key=f"row_form_{current_round}"):
    col_inp, col_btn = st.columns([3,1])
    with col_inp:
        typed = st.text_input(
            "Your guess (5 digits)",
            value=st.session_state.rowbuf,
            max_chars=5,
            help="Type here and press Enter.",
        )
    with col_btn:
        submitted = st.form_submit_button("Submit")

# sanitize and update buffer/tiles every render
cleaned = clean_digits(typed)
if cleaned != st.session_state.rowbuf:
    st.session_state.rowbuf = cleaned
    sync_buf_to_grid(current_round)

if submitted and not st.session_state.done:
    submit_guess()
    st.rerun()

# ============================ Feedback ============================

if st.session_state.error:
    st.error(st.session_state.error)

if st.session_state.win:
    st.success(f"Solved in {current_round + 1} tries.")
elif st.session_state.done and not st.session_state.win:
    st.info(f"Answer: {st.session_state.secret}")

# ============================== Hints =============================
# (Changed to fixed single-row, 6-column grid; no expanders, no scrolling)

st.markdown("### Hints")

cards = []
for r in range(6):
    hs = st.session_state.hints[r]
    if hs:
        lines_html = "".join(f"<div class='hintline'>{h}</div>" for h in hs)
        cards.append(
            f"<div class='hintcard'><div class='hinttitle'>After guess #{r+1}</div>{lines_html}</div>"
        )
    else:
        # Empty placeholder to keep the 6-column grid stable
        cards.append(
            "<div class='hintcard'><div class='hinttitle'>&nbsp;</div><div class='hintline'>&nbsp;</div></div>"
        )

st.markdown("<div class='hints-grid'>" + "".join(cards) + "</div>", unsafe_allow_html=True)

# ============================== Sidebar ==========================

with st.sidebar:
    st.header("How to play")
    st.write(
        "- Type a 5-digit number and press Submit (Enter works inside the field).n"
        "- Colors: Green = correct place, Yellow = wrong place, Gray = not in number.n"
        "- 6 total guesses. Leading zeros allowed."
    )
