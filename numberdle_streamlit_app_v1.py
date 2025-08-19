# numberdle_app.py
# Streamlit "Numberdle" — guess a 5-digit number in 6 tries (00000–99999 allowed)
# Run:  streamlit run numberdle_app.py

import random
import time
from typing import List, Tuple
import streamlit as st

st.set_page_config(
    page_title="Numberdle",
    page_icon="🔢",
    layout="centered",
)

# ----------------------------- Utility Functions -----------------------------

def new_secret() -> str:
    """Return a 5-character string between '00000' and '99999'."""
    return f"{random.randint(0, 99999):05d}"


def evaluate_guess(secret: str, guess: str) -> List[str]:
    """Wordle-style evaluation with duplicate handling.
    Returns list of statuses for each position: 'green' | 'yellow' | 'gray'.
    """
    n = 5
    status = ["gray"] * n
    secret_counts = {}

    # First pass: mark greens and count remaining secret digits
    for i in range(n):
        s, g = secret[i], guess[i]
        if g == s:
            status[i] = "green"
        else:
            secret_counts[s] = secret_counts.get(s, 0) + 1

    # Second pass: mark yellows respecting counts
    for i in range(n):
        if status[i] == "green":
            continue
        g = guess[i]
        if secret_counts.get(g, 0) > 0:
            status[i] = "yellow"
            secret_counts[g] -= 1
    return status


def clamp_range_around_guess(guess: str, secret: str) -> Tuple[int, int]:
    """Produce a sensible numeric range hint around guess & secret."""
    g = int(guess)
    s = int(secret)
    lo = min(g, s)
    hi = max(g, s)
    # widen a little so range feels helpful
    pad = max(50, (hi - lo) // 5)
    lo = max(0, lo - pad)
    hi = min(99999, hi + pad)
    return lo, hi


def gen_clues(secret: str, guess: str, round_idx: int) -> List[str]:
    """Generate 1–2 adaptive hints after a miss. Deterministic per round."""
    rng = random.Random(hash((secret, round_idx)) & 0xFFFFFFFF)

    s_digits = list(map(int, secret))
    s_val = int(secret)

    clues = []

    # 1) Range hint
    lo, hi = clamp_range_around_guess(guess, secret)
    clues.append(f"The number is between {lo:05d} and {hi:05d}.")

    # 2) Parity / divisibility
    clues.append("It is an even number." if s_val % 2 == 0 else "It is an odd number.")
    mod3 = sum(s_digits) % 3
    clues.append(f"Sum of digits ≡ {mod3} (mod 3).")

    # 3) Positional relations (pick safe ones)
    pairs = [(0,1),(1,2),(2,3),(3,4)]
    i, j = rng.choice(pairs)
    relation = "<" if s_digits[i] < s_digits[j] else (">" if s_digits[i] > s_digits[j] else "=")
    clues.append(f"Digit {i+1} {relation} digit {j+1}.")

    # 4) Repetition fact
    clues.append("At least one digit repeats." if len(set(secret)) < 5 else "All digits are distinct.")

    # Pick 2 interesting & non-redundant clues deterministically
    pick = rng.sample(range(len(clues)), k=2)
    return [clues[k] for k in sorted(pick)]


# ----------------------------- Session State -----------------------------

if "secret" not in st.session_state:
    st.session_state.secret = new_secret()
    st.session_state.round = 0  # 0..5
    st.session_state.grid = [["" for _ in range(5)] for _ in range(6)]
    st.session_state.status = [["" for _ in range(5)] for _ in range(6)]
    st.session_state.done = False
    st.session_state.win = False
    st.session_state.hints = [[] for _ in range(6)]

# ----------------------------- Styles -----------------------------

st.markdown(
    """
    <style>
    .title {text-align:center; font-weight:800; font-size:2.2rem; margin-bottom:0.2rem}
    .subtitle {text-align:center; color:#666; margin-bottom:0.6rem}

    .cell-fixed {height:64px; width:64px; border-radius:14px; display:flex; align-items:center; justify-content:center;
           font-size:1.6rem; font-weight:800; border:2px solid #E5E7EB;}
    .green {background:#16a34a; color:white; border-color:#16a34a}
    .yellow {background:#f59e0b; color:white; border-color:#f59e0b}
    .gray {background:#9CA3AF; color:white; border-color:#9CA3AF}
    .neutral {background:#F9FAFB; color:#111827}

    .hint {background:#F3F4F6; border-radius:12px; padding:10px 12px; margin:6px 0;}

    /* Make Streamlit text_inputs compact and borderless to fit 64px cells */
    div[data-baseweb="input"] input {text-align:center; font-weight:800; font-size:1.6rem}
    div[data-baseweb="input"] {border:none !important; box-shadow:none !important}
    label[for^="cell_"] {display:none}
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown('<div class="title">🔢 Numberdle</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Guess the 5-digit number (00000–99999). You have 6 tries.</div>', unsafe_allow_html=True)

# ----------------------------- Controls -----------------------------
colA, colB, colC = st.columns([1,1,1])
if colA.button("🆕 New Game", use_container_width=True):
    st.session_state.secret = new_secret()
    st.session_state.round = 0
    st.session_state.grid = [["" for _ in range(5)] for _ in range(6)]
    st.session_state.status = [["" for _ in range(5)] for _ in range(6)]
    st.session_state.done = False
    st.session_state.win = False
    st.session_state.hints = [[] for _ in range(6)]
    st.rerun()

if colB.button("🙋 Give Up", use_container_width=True):
    st.session_state.done = True
    st.session_state.win = False

if st.session_state.done and not st.session_state.win:
    colC.info(f"Answer: **{st.session_state.secret}**")

# ----------------------------- Grid + Input Logic -----------------------------

current_round = st.session_state.round

# Helper: add digit into the first empty cell of current row
def add_digit(d: str):
    if st.session_state.done:
        return
    row = st.session_state.grid[current_round]
    for i in range(5):
        if row[i] == "":
            row[i] = d
            break

# Helper: remove last filled digit in current row
def backspace():
    if st.session_state.done:
        return
    row = st.session_state.grid[current_round]
    for i in reversed(range(5)):
        if row[i] != "":
            row[i] = ""
            break

# Submit guess
def submit_guess():
    if st.session_state.done:
        return
    row_vals = st.session_state.grid[current_round]
    if any(v == "" for v in row_vals):
        st.session_state._error = "Please fill all 5 digits."
        return
    guess = "".join(row_vals)
    secret = st.session_state.secret
    statuses = evaluate_guess(secret, guess)
    st.session_state.status[current_round] = statuses

    if guess == secret:
        st.session_state.done = True
        st.session_state.win = True
        st.session_state._error = ""
    else:
        st.session_state.hints[current_round] = gen_clues(secret, guess, current_round)
        st.session_state.round += 1
        if st.session_state.round >= 6:
            st.session_state.done = True
        st.session_state._error = ""

# Render 6x5 board
for r in range(6):
    cols = st.columns(5, gap="small")
    editable = (r == current_round) and (not st.session_state.done)
    for c in range(5):
        val = st.session_state.grid[r][c]
        status = st.session_state.status[r][c]
        with cols[c]:
            if editable:
                # Use raw text_input (no HTML wrappers) to avoid focus/overlay issues
                st.session_state.grid[r][c] = st.text_input(
                    "",
                    key=f"cell_{r}_{c}",
                    value=val,
                    max_chars=1,
                    placeholder="•",
                    label_visibility="collapsed",
                )
            else:
                color_class = status if status in {"green","yellow","gray"} else "neutral"
                st.markdown(
                    f"<div class='cell-fixed {color_class}'>" + (val if val != "" else "&nbsp;") + "</div>",
                    unsafe_allow_html=True,
                )

# Error / actions row
err = st.empty()
act1, act2, act3 = st.columns([2,1,1])
if act1.button("✅ Submit Guess", disabled=st.session_state.done, use_container_width=True):
    submit_guess()
    st.rerun()

# On-screen numpad for rock-solid UX
with act2:
    st.write("")
    st.caption("Numpad")
    keypad_rows = [("1","2","3"), ("4","5","6"), ("7","8","9"), ("←","0","↩")] 
    for rkeys in keypad_rows:
        k1, k2, k3 = st.columns(3)
        for k, col in zip(rkeys, (k1, k2, k3)):
            if col.button(k, use_container_width=True):
                if k == "←":
                    backspace()
                elif k == "↩":
                    submit_guess()
                else:
                    add_digit(k)
                st.rerun()

with act3:
    quick = st.text_input("Quick type", key=f"quick_{current_round}", max_chars=5, help="Type 5 digits to fill the current row")
    if quick:
        if quick.isdigit():
            quick = quick.zfill(5)[:5]
            for i,ch in enumerate(quick):
                st.session_state.grid[current_round][i] = ch
            st.rerun()
        else:
            err.error("Only digits 0–9 allowed in quick type.")

# Results & hints
if st.session_state.win:
    st.balloons()
    st.success(f"Perfect! You got it in {current_round+1} tries.")
elif st.session_state.done and not st.session_state.win:
    st.info(f"Answer: **{st.session_state.secret}**")

st.markdown("### Hints")
shown_any = False
for r in range(6):
    if st.session_state.hints[r]:
        shown_any = True
        with st.expander(f"After guess #{r+1}"):
            for h in st.session_state.hints[r]:
                st.markdown(f"<div class='hint'>• {h}</div>", unsafe_allow_html=True)
if not shown_any:
    st.caption("Hints will appear here after each incorrect guess.")

# Sidebar help
with st.sidebar:
    st.header("How to play")
    st.write(
        "Enter 5 digits per row and press **Submit Guess**. Cell colors mean:"
        "- Green: correct digit & position"
        "- Yellow: digit exists but wrong position"
        "- Gray: digit not in the number"
        "You have 6 tries. Leading zeros are allowed (00000–99999)."
    )
    st.divider()
    st.write("Use the on-screen **Numpad**, **Quick type**, or per-cell inputs. Cheers!")
