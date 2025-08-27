# Numberdle

A Wordle-inspired number guessing game implemented in Streamlit. Players have 6 attempts to guess a 5-digit number (00000-99999) using color-coded feedback and strategic hints.

## Overview

Numberdle adapts the popular Wordle format to numerical guessing, challenging players to deduce a secret 5-digit number through logical reasoning and pattern recognition. The game includes multiple difficulty modes, adaptive hints, and performance tracking to enhance the puzzle-solving experience.

## Game Mechanics

### Core Gameplay
- **Secret Number**: Random 5-digit number from 00000 to 99999
- **Attempts**: 6 guesses to find the correct number
- **Feedback System**: Color-coded tiles indicate correctness
  - **Green**: Correct digit in correct position
  - **Yellow**: Correct digit in wrong position  
  - **Gray**: Digit not present in the number

### Difficulty Modes

**Normal Mode**
- Standard gameplay with no restrictions between guesses
- Any 5-digit combination allowed based on previous feedback

**Hard Mode**
- Must incorporate all revealed information in subsequent guesses
- Green digits must remain in their confirmed positions
- Yellow digits must be included but in different positions

**Ultra Mode** 
- All Hard Mode constraints plus additional restrictions
- Cannot reuse digits marked gray (completely eliminated)
- Must respect maximum count constraints derived from feedback
- Most challenging mode requiring systematic constraint tracking

## Features

### Intelligent Hint System
The game provides contextual hints after each incorrect guess:

- **Range Clues**: Numerical bounds around the target
- **Mathematical Properties**: Parity (even/odd), digit sum modulo arithmetic
- **Positional Relationships**: Comparisons between digit positions
- **Pattern Information**: Repetition analysis and distinctness

### User Interface Design

**Interactive Grid**
- 6x5 tile layout matching Wordle aesthetics
- Real-time color feedback as players type
- Clean, responsive design optimized for focus

**Multiple Input Methods**
- Direct typing with auto-focus capabilities
- On-screen numpad for touch devices
- Keyboard shortcuts and form submission

**Progressive Enhancement**
- Type-anywhere functionality using JavaScript integration
- Seamless input handling across different interaction patterns
- Visual feedback for current position and game state

### Performance Tracking
- Local statistics persistence using JSON storage
- Recent game performance metrics
- Rolling averages for skill assessment
- Win streak tracking and analysis

## Technical Implementation

### Architecture
```python
# Core game logic
def evaluate_guess(secret: str, guess: str) -> List[str]:
    """Wordle-style evaluation with duplicate handling"""
    # Implements proper color logic for repeated digits

def gen_clues(secret: str, guess: str, round_idx: int) -> List[str]:
    """Generate adaptive hints based on guess quality"""
    # Deterministic hint selection per round
```

### Constraint Validation System
The Hard and Ultra modes implement sophisticated constraint tracking:

```python
def _validate_guess_against_history(guess: str, mode: str) -> (bool, str):
    """Enforce mode-specific rules using accumulated knowledge"""
    # Tracks green positions, yellow constraints, and elimination rules
    # Builds comprehensive constraint set from game history
```

### State Management
- Streamlit session state for game persistence
- Grid synchronization between input buffer and display
- Error handling and validation messaging
- Clean state transitions between rounds

## Installation and Usage

### Requirements
```bash
pip install streamlit
```

### Running the Game
```bash
git clone https://github.com/steppingstonesqueeze/numberdle
cd numberdle
streamlit run numberdle_streamlit_app_v6_semiliveinput.py
```

### Development Versions
The repository includes multiple implementation versions:

- `v1.py`: Basic implementation with manual input
- `v2.py`: Enhanced UI with improved styling  
- `v3.py`: Side-by-side hint display system
- `v5.py`: Multiple difficulty modes introduction
- `v6.py`: Advanced typing system with auto-focus

## Game Strategy

### Optimal Opening Moves
- Start with numbers containing diverse digits (12345, 67890)
- Avoid repeated digits in early guesses for maximum information
- Use mathematical properties from hints to narrow ranges quickly

### Advanced Techniques
- **Constraint Satisfaction**: Track all revealed information systematically  
- **Elimination Strategy**: Use gray feedback to reduce possibility space
- **Pattern Recognition**: Identify common number patterns and sequences
- **Position Analysis**: Leverage yellow feedback for placement optimization

### Mode-Specific Strategies

**Hard Mode Tips**
- Maintain running list of confirmed digits and positions
- Plan guesses to incorporate all yellow digits in new positions
- Balance information gathering with constraint satisfaction

**Ultra Mode Mastery**
- Track maximum occurrence counts for each digit
- Avoid any previously eliminated digits completely
- Use constraint propagation to deduce impossible combinations

## Educational Applications

### Mathematical Skills Development
- **Number Sense**: Understanding digit patterns and relationships
- **Logical Reasoning**: Constraint satisfaction and deduction
- **Modular Arithmetic**: Applying mathematical properties strategically
- **Systematic Thinking**: Managing multiple constraints simultaneously

### Cognitive Benefits
- **Working Memory**: Tracking multiple pieces of information
- **Pattern Recognition**: Identifying numerical sequences and relationships  
- **Strategic Planning**: Balancing exploration vs exploitation in guesses
- **Error Analysis**: Learning from feedback to improve future performance

## Code Structure

### Version Evolution
The codebase demonstrates iterative development with progressive feature additions:

1. **Core Mechanics**: Basic Wordle adaptation for numbers
2. **UI Enhancements**: Improved visual design and interaction patterns
3. **Advanced Features**: Hint systems and difficulty modes
4. **Input Optimization**: Seamless typing experience with JavaScript integration
5. **Performance Tracking**: Statistics and progress monitoring
6. **Accessibility**: Multiple input methods and responsive design

### Key Design Patterns
- **State Machine**: Clean game state transitions
- **Strategy Pattern**: Different difficulty mode implementations  
- **Observer Pattern**: UI updates based on game state changes
- **Command Pattern**: Input handling and action processing

## Future Enhancements

### Potential Features
- **Multiplayer Mode**: Competitive and cooperative gameplay
- **Custom Ranges**: User-defined number bounds (3-digit, 6-digit, etc.)
- **Themed Variants**: Date guessing, mathematical sequences, prime numbers
- **Analytics Dashboard**: Detailed performance analysis and improvement suggestions
- **Accessibility Features**: Screen reader support, keyboard navigation optimization

### Technical Improvements
- **Mobile Optimization**: Touch-first interaction design
- **Performance Optimization**: Faster rendering for complex constraint checking
- **Offline Mode**: Local storage with sync capabilities
- **Social Features**: Score sharing and leaderboard systems

---

*Numberdle transforms numerical reasoning into an engaging puzzle experience, combining mathematical thinking with strategic game mechanics to create an educational and entertaining challenge.*