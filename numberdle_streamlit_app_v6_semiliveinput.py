# numberdle_app_improved.py
# Numberdle with NY Times style typing, side hints, and mode explanations
# Run: streamlit run numberdle_app_improved.py

import random
from typing import List, Tuple
import streamlit as st

# Local stats + JS key handler
import os, json, statistics
import streamlit.components.v1 as components
from collections import Counter, defaultdict

st.set_page_config(page_title="Numberdle", layout="wide")

# ============================ Utilities ============================

def new_secret() -> str:
    return f"{random.randint(0, 99999):05d}"

def evaluate_guess(secret: str, guess: str) -> List[str]:
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

def gen_clues(secret: str, guess: str, round_idx: int) -> List[str]:
    rng = random.Random(hash((secret, round_idx)) & 0xFFFFFFFF)
    s_digits = list(map(int, secret))
    s_val = int(secret)
    clues = []
    lo, hi = clamp_range_around_guess(guess, secret)
    clues.append(f"The number is between {lo:05d} and {hi:05d}.")
    clues.append("It is an even number." if s_val % 2 == 0 else "It is an odd number.")
    clues.append(f"Sum of digits {sum(s_digits) % 3} (mod 3).")
    i, j = rng.choice([(0,1),(1,2),(2,3),(3,4)])
    rel = "<" if s_digits[i] < s_digits[j] else (">" if s_digits[i] > s_digits[j] else "=")
    clues.append(f"Digit {i+1} {rel} digit {j+1}.")
    clues.append("At least one digit repeats." if len(set(secret)) < 5 else "All digits are distinct.")
    pick = rng.sample(range(len(clues)), k=2)
    return [clues[k] for k in sorted(pick)]

def clean_digits(s: str) -> str:
    return "".join(ch for ch in s if ch.isdigit())[:5]

# ============================ Simple Stats ============================

STATS_PATH = "numberdle_stats.json"

def _load_stats():
    try:
        if os.path.exists(STATS_PATH):
            with open(STATS_PATH, "r") as f:
                data = json.load(f)
            if isinstance(data, list):
                out = []
                for x in data:
                    try:
                        out.append(int(x))
                    except Exception:
                        pass
                return out
    except Exception:
        pass
    return []

def _save_stats(data):
    try:
        with open(STATS_PATH, "w") as f:
            json.dump([int(x) for x in data], f)
    except Exception:
        pass

def _update_leaderboard_in_state():
    data = _load_stats()
    st.session_state.last_solved_tries = (data[-1] if data else None)
    st.session_state.last10_avg = (round(statistics.mean(data[-10:]), 2) if data else None)

# ====================== Hard/Ultra Mode Helpers ======================

def _build_knowledge(upto_round: int, mode: str):
    """Aggregate constraints from previous feedback."""
    greens = {}                      # position -> digit (str)
    min_count = defaultdict(int)     # digit -> minimum occurrences
    max_count = defaultdict(lambda: 5)  # digit -> maximum occurrences
    banned_yellow = defaultdict(set) # digit -> positions not allowed (yellow spots)
    banned_all = defaultdict(set)    # digit -> positions not allowed (yellow + gray-derived in Ultra)

    for r in range(upto_round):
        row = st.session_state.grid[r]
        sts = st.session_state.status[r]
        # Tolerate partially empty rows
        if not row or not sts: 
            continue
        counts = Counter([d for d in row if d != ""])
        matches = Counter()

        # Collect greens/yellows and per-round matches
        for i in range(5):
            d = row[i]
            if d == "":
                continue
            s = sts[i]
            if s == "green":
                greens[i] = d
                matches[d] += 1
            elif s == "yellow":
                banned_yellow[d].add(i)
                banned_all[d].add(i)
                matches[d] += 1
            elif s == "gray":
                # in Ultra we'll add gray positions to banned_all only when there are some matches for that digit in the same round
                pass

        # Update min counts from this round's matches
        for d, k in matches.items():
            if k > min_count[d]:
                min_count[d] = k

        # Update max counts & gray-position bans per round
        for d, m in counts.items():
            k = matches.get(d, 0)
            if k == 0:
                # digit was guessed this round but had 0 matches => secret contains 0 of this digit
                # only applied as a hard cap in Ultra
                max_count[d] = min(max_count[d], 0)
            else:
                # cap by observed matches for this round (Ultra)
                if max_count[d] > k:
                    max_count[d] = k
                # Ultra: any gray instances of this digit in this round are position-banned
                if mode == "Ultra":
                    for i in range(5):
                        if row[i] == d and sts[i] == "gray":
                            banned_all[d].add(i)

    return greens, min_count, max_count, banned_yellow, banned_all


def _validate_guess_against_history(guess: str, mode: str) -> (bool, str):
    """Return (ok, message). Enforces Normal/Hard/Ultra rules."""
    if mode not in ("Hard", "Ultra"):
        return True, ""

    upto = st.session_state.round
    greens, min_count, max_count, banned_yellow, banned_all = _build_knowledge(upto, mode)
    # Greens must stay fixed
    for i, d in greens.items():
        if guess[i] != d:
            return False, f"Position {i+1} must be {d} based on previous feedback."

    # Count occurrences in this guess
    gcount = Counter(guess)

    # Hard rules: include all known digits (at least min_count) and avoid yellowed positions
    for d, mn in min_count.items():
        if gcount.get(d, 0) < mn:
            needed = mn - gcount.get(d, 0)
            return False, f"Use digit {d} at least {mn} time(s); missing {needed}."
    for d, bad_idxs in banned_yellow.items():
        for i in bad_idxs:
            if guess[i] == d:
                return False, f"Digit {d} cannot be in position {i+1} (yellow earlier)."

    if mode == "Ultra":
        # No disallowed digits & respect max counts
        for d, mx in max_count.items():
            if mx == 0 and gcount.get(d, 0) > 0:
                return False, f"Digit {d} is not in the number based on earlier feedback."
            if gcount.get(d, 0) > mx:
                return False, f"Too many '{d}' digits; max allowed is {mx}."
        # Also ban gray-derived positions
        for d, bad_idxs in banned_all.items():
            for i in bad_idxs:
                if guess[i] == d:
                    return False, f"Digit {d} cannot be in position {i+1} (ruled out earlier)."

    return True, ""


# ============================ State ============================

def init_state():
    st.session_state.secret = new_secret()
    st.session_state.round = 0
    st.session_state.grid = [["" for _ in range(5)] for _ in range(6)]
    st.session_state.status = [["" for _ in range(5)] for _ in range(6)]
    st.session_state.done = False
    st.session_state.win = False
    st.session_state.hints = [[] for _ in range(6)]
    st.session_state.current_input = ""
    st.session_state.error = ""
    if 'mode' not in st.session_state:
        st.session_state.mode = "Normal"
    _update_leaderboard_in_state()

if "secret" not in st.session_state:
    init_state()

def submit_guess():
    if st.session_state.done:
        return
    current_input = st.session_state.current_input
    if len(current_input) != 5:
        st.session_state.error = "Enter exactly 5 digits."
        return
    guess = current_input
    # Mode validation
    mode = st.session_state.get('mode', 'Normal')
    ok, msg = _validate_guess_against_history(guess, mode)
    if not ok:
        st.session_state.error = f"{msg}"
        return
    
    # Update grid with current input
    for i in range(5):
        st.session_state.grid[st.session_state.round][i] = current_input[i] if i < len(current_input) else ""
    
    secret = st.session_state.secret
    st.session_state.status[st.session_state.round] = evaluate_guess(secret, guess)
    if guess == secret:
        st.session_state.done = True
        st.session_state.win = True
        st.session_state.error = ""
        # record win
        tries = st.session_state.round + 1
        data = _load_stats()
        data.append(tries)
        _save_stats(data)
        _update_leaderboard_in_state()
    else:
        st.session_state.hints[st.session_state.round] = gen_clues(secret, guess, st.session_state.round)
        st.session_state.round += 1
        st.session_state.current_input = ""
        st.session_state.error = ""
        if st.session_state.round >= 6:
            st.session_state.done = True

# ============================ Styles ============================

st.markdown(
    """
    <style>
      .title {text-align:center; font-weight:800; font-size:2rem; margin: 0.2rem 0 0.2rem;}
      .subtle {text-align:center; color:#6b7280; margin-bottom: 0.4rem;}
      .leader {text-align:center; color:#374151; font-weight:600; margin-bottom: 0.6rem;}
      
      .board {display:grid; grid-template-columns: repeat(5, 60px); gap:10px; justify-content:center; margin: 12px 0 14px;}
      .tile {height:60px; width:60px; border-radius:10px; display:flex; align-items:center; justify-content:center;
             font-size:1.4rem; font-weight:800; border:2px solid #e5e7eb; background:#f9fafb; color:#111827;}
      .green {background:#16a34a; color:#fff; border-color:#16a34a;}
      .yellow {background:#f59e0b; color:#fff; border-color:#f59e0b;}
      .gray {background:#9ca3af; color:#fff; border-color:#9ca3af;}
      .current {border-color:#3b82f6; border-width:3px; background:#dbeafe;}
      .neutral {}
      
      .hints-side {width: 100%; max-width: 350px;}
      .hintcard {
        background: #f3f4f6;
        border: 1px solid #e5e7eb;
        border-radius: 10px;
        padding: 10px 12px;
        margin-bottom: 8px;
        min-height: 50px;
      }
      .hinttitle {
        font-weight: 700;
        margin-bottom: 6px;
        font-size: 0.9rem;
        color: #374151;
      }
      .hintline {
        font-size: 0.85rem;
        color: #111827;
        margin-bottom: 3px;
      }
      
      .center {display:flex; align-items:center; justify-content:center; gap:10px;}
      
      /* Mode descriptions */
      .mode-desc {
        background: #f8f9fa;
        border-radius: 8px;
        padding: 10px;
        margin: 10px 0;
        font-size: 0.85rem;
        border-left: 3px solid #3b82f6;
      }
      .mode-title {
        font-weight: 600;
        color: #1f2937;
        margin-bottom: 4px;
      }
      .mode-text {
        color: #4b5563;
        line-height: 1.4;
      }

      /* Hide input visually but keep it functional */
      .stTextInput > div > div > input {
        position: fixed !important;
        top: -200px !important;
        left: -200px !important;
        opacity: 0.01 !important;
        pointer-events: none !important;
      }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown('<div class="title">Numberdle</div>', unsafe_allow_html=True)
st.markdown('<div class="subtle">Guess the 5-digit number (00000-99999). 6 tries. Just start typing!</div>', unsafe_allow_html=True)

# Leaderboard summary
_last = st.session_state.get("last_solved_tries")
_avg = st.session_state.get("last10_avg")
leader_txt = []
leader_txt.append(f"Last solved in {int(_last)} tries" if _last is not None else "No solves yet")
leader_txt.append(f"Last 10 average: {float(_avg):.2f}" if _avg is not None else "Last 10 average: --")
st.markdown(f"<div class='leader'>{' | '.join(leader_txt)}</div>", unsafe_allow_html=True)

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

# ============================ Game Board + Hints ============================

# Update current row with typing
current_round = st.session_state.round
current_input = st.session_state.current_input

# Build board and hints side by side
board_col, hints_col = st.columns([1.5, 1])

with board_col:
    # Build entire board as one HTML string
    tiles_html = []
    for r in range(6):
        for c in range(5):
            if r == current_round and not st.session_state.done:
                # Current active row - show what's being typed
                val = current_input[c] if c < len(current_input) else ""
                if c < len(current_input):
                    css = "neutral"
                elif c == len(current_input):
                    css = "current"  # Blue border for next position
                else:
                    css = "neutral"
            else:
                # Completed or future rows
                val = st.session_state.grid[r][c] if st.session_state.grid[r][c] else ""
                status = st.session_state.status[r][c] if st.session_state.status[r][c] else ""
                css = status if status in {"green", "yellow", "gray"} else "neutral"
            
            tiles_html.append(f"<div class='tile {css}' id='tile-{r}-{c}'>{val or '&nbsp;'}</div>")
    
    board_html = "<div class='board'>" + "".join(tiles_html) + "</div>"
    st.markdown(board_html, unsafe_allow_html=True)

with hints_col:
    st.markdown("**💡 Hints**")
    
    hints_html = ""
    for r in range(6):
        hs = st.session_state.hints[r]
        if hs:
            lines_html = "".join(f"<div class='hintline'>• {h}</div>" for h in hs)
            hints_html += f"<div class='hintcard'><div class='hinttitle'>After guess #{r+1}</div>{lines_html}</div>"
        elif r < st.session_state.round:
            hints_html += f"<div class='hintcard'><div class='hinttitle'>Guess #{r+1}</div><div class='hintline'>No hints available</div></div>"
    
    if hints_html:
        st.markdown(f"<div class='hints-side'>{hints_html}</div>", unsafe_allow_html=True)
    else:
        st.markdown("<div class='hints-side'><div class='hintcard'><div class='hintline'>Hints will appear after each guess</div></div></div>", unsafe_allow_html=True)

# ============================ Hidden Input Handler ============================

# This is the key - hidden but functional input that auto-focuses
with st.form(key="typing_form", clear_on_submit=False):
    typed_input = st.text_input(
        "Hidden typing input",
        value=st.session_state.current_input,
        max_chars=5,
        key="main_input",
        help="This handles all typing - you don't need to click here"
    )
    
    # Submit happens on Enter or when length reaches 5
    submitted = st.form_submit_button("Submit", type="primary")

# Process input changes
cleaned_input = clean_digits(typed_input)
if cleaned_input != st.session_state.current_input:
    st.session_state.current_input = cleaned_input
    st.rerun()

# Auto-submit when 5 digits are entered
if len(cleaned_input) == 5 and not st.session_state.done and not submitted:
    # Don't auto-submit, let user press Enter
    pass

# Handle form submission
if submitted and not st.session_state.done:
    submit_guess()
    st.rerun()

# Auto-focus script to keep input always focused
components.html(
    """
    <script>
    (function() {
        function focusInput() {
            try {
                const inputs = window.parent.document.querySelectorAll('input[type="text"]');
                for(let input of inputs) {
                    if(input.getAttribute('aria-label') && input.getAttribute('aria-label').includes('Hidden typing input')) {
                        input.focus();
                        input.style.caretColor = 'transparent';
                        break;
                    }
                }
            } catch(e) {
                console.log('Focus attempt failed:', e);
            }
        }
        
        // Focus immediately
        setTimeout(focusInput, 100);
        
        // Re-focus when clicking anywhere
        document.addEventListener('click', function() {
            setTimeout(focusInput, 50);
        });
        
        // Re-focus on any interaction
        setInterval(focusInput, 1000);
    })();
    </script>
    """,
    height=0
)

# ============================ Feedback ============================

if st.session_state.error:
    st.error(st.session_state.error)

if st.session_state.win:
    st.success(f"🎉 Solved in {current_round + 1} tries!")
elif st.session_state.done and not st.session_state.win:
    st.info(f"Game over! The answer was: {st.session_state.secret}")

# ============================== Sidebar ==========================

with st.sidebar:
    st.subheader("🎮 Game Mode")
    mode_options = ["Normal", "Hard", "Ultra"]
    current_mode_idx = mode_options.index(st.session_state.get("mode", "Normal"))
    
    new_mode = st.selectbox(
        "Select difficulty:",
        mode_options,
        index=current_mode_idx
    )
    
    if new_mode != st.session_state.mode:
        st.session_state.mode = new_mode
        st.rerun()
    
    # Mode descriptions
    if st.session_state.mode == "Normal":
        st.markdown("""
        <div class="mode-desc">
            <div class="mode-title">🟢 Normal Mode</div>
            <div class="mode-text">
                Standard gameplay. No restrictions between guesses. 
                Make any 5-digit guess based on the color feedback.
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    elif st.session_state.mode == "Hard":
        st.markdown("""
        <div class="mode-desc">
            <div class="mode-title">🟡 Hard Mode</div>
            <div class="mode-text">
                Must use revealed information! Green letters must stay in the same position. 
                Yellow letters must be included in your next guess (but in different positions).
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    elif st.session_state.mode == "Ultra":
        st.markdown("""
        <div class="mode-desc">
            <div class="mode-title">🔴 Ultra Mode</div>
            <div class="mode-text">
                Hard mode rules PLUS: Cannot reuse any digits that were marked gray. 
                Must respect all maximum count constraints. Most challenging!
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")
    
    st.header("📋 How to Play")
    st.markdown("""
    • **Just start typing** - the page captures your keystrokes!
    • **5 digits** - from 00000 to 99999 
    • **6 tries** to guess correctly
    • **Colors mean:**
      - 🟢 **Green**: Right digit, right position
      - 🟡 **Yellow**: Right digit, wrong position  
      - ⬜ **Gray**: Digit not in the number
    • **Backspace** to delete, **Enter** to submit
    • **Hints** appear after each guess to help you
    """)
    
    st.markdown("---")
    st.caption("💡 Tip: Focus on the range hints and digit relationships!")
