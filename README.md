# LuckyLoop+ Blackjack
### Final Project – CIS 1051
### Author: Maria Abato (Junior, Temple University)
#### Link to video: https://youtu.be/3yM9YBqXCxg
#Overview
LuckyLoop+ Blackjack is a roguelike-inspired blackjack game built using Python and Pygame.  
It combines traditional blackjack rules with:
- Random encounters
- Stackable skills
- Level thresholds
- Adjustable betting
- Progressive difficulty
- Casino-style animations and audio

The goal is to survive rounds, earn money, and advance through levels while encountering bonuses and challenges along the way.

---

#Gameplay Features

### Blackjack Core
- Standard blackjack logic (hit, stand, double, dealer rules)
- Sliding card animations and dealing sound effect

### Roguelike Systems
- Skills persist across game overs
- Balance resets but upgrades carry over
- Random encounters that change rules or rewards
- Dynamic level thresholds that get harder each run

### Betting System
- Player can increase/decrease bet each round
- Maximum bet limited by current balance
- Early rounds have tutorial-friendly minimums

### Audio & Visuals
- Multiple looping background music tracks
- Card dealing sound effect
- High-visibility HUD with balance, level, round, and goals

### 
- I also included a file I made using R Studio.
- I used the Python code to collect the game data into a CSV file that I could analyze
- I also included some further analysis of the graphs and what they mean for the game

---

#Challenges & What I Learned

1. Managing GameState
   Preventing new features (skills, encounters, persistent upgrades) from interfering with existing blackjack logic. Solved by restructuring GameState and separating:
   - Persistent upgrades
   - Temporary round data
   - Level progression

2. Event Handling Bugs
   Issues came from mixing mouse input, keyboard shortcuts, and sound events:
   - Music not looping
   - Card sound triggering multiple times
   - Mismatched event variables (`ev`, `event`)

3. Scaling Difficulty Without Making the Game Unfair*
   Developed formulas for level thresholds and bet scaling to feel gradual and fair.

4. Audio System* 
   Integrated multiple songs, automatic playlist switching, volume control, and timed sound effects using a music manager.

5. Balancing Roguelike Mechanics  
   Designed a system where money resets on death but skills persist, balancing challenge and player progression.

---

#AI Assistance
Some brainstorming, design suggestions, and debugging help came from ChatGPT (OpenAI).  
This included:
- Ideas for roguelike mechanics  
- Suggestions for code structure  
- Help diagnosing errors  

All final code, gameplay, and design decisions were completed by me.

---

# Audio & Visual Credits

### Background Music
1. **“This Casino Funk Jazz Groove” – Lowtone Music**  
   FreeMusicArchive  
   [Link](https://freemusicarchive.org/music/lowtone-music/this-casino-funk-groove/this-casino-funk-jazz-groove/)

2. **“Casino Jazz 317385” – Pixabay**  
   [Link](https://pixabay.com/music/traditional-jazz-casino-jazz-317385/)

3. **“Jazz Music Casino Poker Roulette Las Vegas Intro Theme 287498” – Pixabay**  
   [Link](https://pixabay.com/music/traditional-jazz-jazz-music-casino-poker-roulette-las-vegas-background-intro-theme-287498/)

### Sound Effects
- **“Dealing Cards Sound” – Orange Free Sounds**  

### Visual Assets
- **Playing card pack “PNG-cards-1.3”** (open/free online asset)
