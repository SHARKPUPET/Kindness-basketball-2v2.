# Kindness-basketball-2v2.
# Basketball 2v2 (Pygame)

A simple 2v2 basketball mini-game built with **Pygame**.  
You control a player, work with your AI teammate, and try to score while also building up a "Kindness" score by passing.  

Win the game by reaching a combined **Score + Kindness = 20**.

---

## 🎮 Controls

| Key / Button | Action |
|--------------|--------|
| **W / A / S / D** or **Arrow Keys** | Move player |
| **SPACE** | Shoot (only when possession freezes) |
| **E** | Pass to teammate (only when possession freezes) |
| **Q** | Call for the ball (ask teammate to pass) |
| **F** | Attempt a steal from opponents |
| **P** | Pause / Resume game |
| **R** | Reset game (hard reset) |
| **ESC** | Quit game |
| **Mouse (left click)** | Click UI buttons (Pause, Reset, Speed +/–, Shoot, Pass) |

---

## 🏆 Win Condition

- Your team wins when **Score + Kindness reaches 20**.  
- A victory screen appears with **YOU WIN!** and the game freezes.  
- Press **R** to restart after winning.

---

## 🤝 Kindness Score

- Passing to your teammate or your teammate stealing for you increases your **Kindness** score.  
- This encourages teamwork, not just scoring alone.  

---

## ⚙️ Features

- **Decision Freeze:** Whenever you gain possession, the game freezes and gives you options: **Shoot** or **Pass**.  
- **Call for Ball:** Press **Q** to ask your teammate to pass (they may ignore you if defenders are too close).  
- **AI Logic:** Teammate will move towards the hoop, sometimes shoot. Defenders chase and try to steal.  
- **Speed Controls:** UI buttons (or +/– keys) let you adjust player/AI speeds.  
- **Winning Screen:** Full-screen overlay when target is reached.  

---

## 🛠 Requirements

- Python 3.x  
- [Pygame](https://www.pygame.org/)  

Install dependencies:

```bash
pip install pygame
