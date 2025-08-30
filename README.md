🏀 Kindness Basketball 2v2 (Pygame)

A simple 2v2 basketball mini-game built with Pygame.
You control a player, work with your AI teammate, and try to score — while also building a Kindness score through passing and teamwork.

💡 Win the game by reaching a combined Score + Kindness = 20.

| Key / Button                        | Action                                                |
| ----------------------------------- | ----------------------------------------------------- |
| **W / A / S / D** or **Arrow Keys** | Move player                                           |
| **SPACE**                           | Shoot (when possession freezes)                       |
| **E**                               | Pass to teammate (when possession freezes)            |
| **Q**                               | Call for the ball (ask teammate to pass)              |
| **F**                               | Attempt a steal from opponents                        |
| **P**                               | Pause / Resume game                                   |
| **R**                               | Reset game (hard reset)                               |
| **ESC**                             | Quit game                                             |
| **Mouse (left click)**              | Use UI buttons (Pause, Reset, Speed +/–, Shoot, Pass) |

🏆 Win Condition

Victory is achieved when Score + Kindness = 20.

A full-screen overlay appears with YOU WIN!

Press R to restart after winning.

🤝 Kindness Score

Passing to your teammate or your teammate stealing boosts your Kindness score.

This rewards teamwork, not just solo scoring.

⚙️ Features

Decision Freeze: Whenever you get possession, the game pauses for you to choose Shoot or Pass.

Call for Ball: Press Q to ask your teammate to pass (they might ignore you if defenders are too close).

AI Teammate & Defenders: Teammate runs plays, shoots sometimes; defenders chase, guard, and steal.

Speed Controls: Adjust speeds using UI buttons or the + / – keys.

Winning Screen: Big overlay when you reach the target.

🛠 Requirements

Python 3.8+

Pygame
 (2.6+ recommended)

Install with:

pip install pygame

▶️ How to Run
Option 1 — Command Prompt / Terminal
python main.py

Option 2 — VS Code

Open the folder in VS Code.

Open main.py.

Press ▶ Run (top-right).
