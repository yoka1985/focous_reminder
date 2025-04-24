# Focus Reminder – Mindful Work Timer for Ubuntu 24

Focus Reminder is a distraction-free, mindfulness-centered Pomodoro timer built with Python and Tkinter. Designed for Ubuntu 24, it integrates goal setting, adaptive work cycles, and reflective daily logging to support intentional work habits.

## Features

### 🧘‍♂️ Mindful Productivity
- Set a **daily intention** and up to **3 goals**
- Track **goal progress**, with remarks on completion
- Evaluate the day with a **reflection prompt** and 1–10 rating

### ⏱ Adaptive Pomodoro Logic
- Custom Pomodoro duration (divided into thirds)
- Sound cues at each ⅓ interval (`short_0.333_pom_cue_bell.wav`)
- Meditation cue after every 2 Pomodoros (`break_meditate_cue_bell.wav`)
- Adaptive timing:
  - Pomodoros 1–4: 100% time  
  - 5–8: 90%  
  - 9+: 80%

### 🔊 Sound & Concentration
- Loopable ambient sound for focus (`2_min_concetration.wav`)
- All sound files stored in the `sounds/` directory
- Non-blocking audio playback with `pygame.mixer`

### ✅ Subtask Planning
- Each task includes 3 subtasks (14 char max)
- Subtask estimations (1–4 Pomodoros) are for planning only

### 🧾 Logging & Reflection
- Logs all:
  - Goal completions with remarks
  - Pauses (with reason)
  - End-of-day reflections
- Data saved in a **valid JSON array** in `log/daily_data.json`

### 🖥 GUI
- Small, persistent window (~7% x 10% of screen)
- Expand/contract button
- Pause/resume + concentration sound toggle
- Open gedit
- "Finish" button to end day early

## Directory Structure
focus_reminder/ │ ├── focus_reminder.py # Main application file ├── log/ │ └── daily_data.json # JSON log of daily sessions ├── sounds/ │ ├── 2_min_concetration.wav │ ├── short_0.333_pom_cue_bell.wav │ └── break_meditate_cue_bell.wav

## Requirements

- Ubuntu 24+
- Python 3.x
- Dependencies:
  - `pygame` (for sound)

Install dependencies:

```bash
pip install pygame
