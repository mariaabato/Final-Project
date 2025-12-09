
import pygame
import os
import sys
import random
import csv
import time
import textwrap
from collections import namedtuple

# Configuration & Paths

CARD_FOLDER_PATH = os.path.join("Playing Cards", "PNG-cards-1.3")


TABLE_BG_FILENAME = "table_background.png"

# Sound assets folder
SND_FOLDER = os.path.join("assets", "sounds")


# Window & visuals

SCREEN_WIDTH, SCREEN_HEIGHT = 1280, 720
FPS = 60

# Card display size (tweak up/down if needed)
CARD_W, CARD_H = 160, 230


# Game values

STARTING_BALANCE = 300
BASE_BETS = {1: 100, 2: 200, 3: 500}  # tutorial rounds start higher


LEVELS = {
    1: {"decks": 1, "dealer_hits_soft_17": False, "blackjack_payout": 1.5, "threshold": 500},
    2: {"decks": 2, "dealer_hits_soft_17": True, "blackjack_payout": 1.33, "threshold": 1200},
    3: {"decks": 4, "dealer_hits_soft_17": True, "blackjack_payout": 1.2, "threshold": 2500}
}

ENCOUNTER_CHANCE = 0.18

SKILLS = {
    "Luck Charm": {"desc": "+5% illustrative win chance for this level", "type":"win_chance", "value":0.05},
    "Card Peek": {"desc": "Reveal dealer's hole card for the level", "type":"peek", "value":None},
    "Extra Double": {"desc": "Allow one extra double-down this level", "type":"extra_double", "value":1},
    "Reward Booster": {"desc": "Multiply win rewards by 1.5 this level", "type":"reward_mult", "value":1.5},
    "Safety Net": {"desc": "First loss that would drop below 0 is halved", "type":"safety_net", "value":None}
}

ENCOUNTERS = [
    {"name":"Lucky Deck", "effect":{"decks_delta":-1}, "desc":"Fewer decks this round — easier!"},
    {"name":"Dealer Mistake", "effect":{"dealer_stands_early":True}, "desc":"Dealer stands early this round"},
    {"name":"High Stakes", "effect":{"payout_mult":2, "house_edge":0.05}, "desc":"Double payout but house edge increases"},
    {"name":"Bonus Card", "effect":{"player_extra_card":True}, "desc":"Player draws an extra card automatically"},
    {"name":"Foggy Table", "effect":{"dealer_hits_soft_12":True}, "desc":"Dealer hits more aggressively this round"},
]

CSV_FILE = "results.csv"


# Initialize Pygame

pygame.init()

# audio setup
AUDIO_AVAILABLE = False
try:
    pygame.mixer.init()
    AUDIO_AVAILABLE = True
except Exception:
    pass


# Background music files
MUSIC_FOLDER = "."  
music_files = [
    "casino-jazz-317385.mp3",
    "jazz-music-casino-poker-roulette-las-vegas-background-intro-theme-287498.mp3",
    "Lowtone Music - This Casino _ Funk Jazz Groove.mp3"
]
music_paths = [os.path.join(MUSIC_FOLDER, f) for f in music_files]
current_music_index = 0

MUSIC_END_EVENT = pygame.USEREVENT + 1

def play_next_song(fade_ms=1000):
    global current_music_index
    if not music_paths:
        return
    pygame.mixer.music.load(music_paths[current_music_index])
    pygame.mixer.music.play(fade_ms=fade_ms)
    current_music_index = (current_music_index + 1) % len(music_paths)

if AUDIO_AVAILABLE and music_paths:
    pygame.mixer.music.set_volume(0.3)
    pygame.mixer.music.set_endevent(MUSIC_END_EVENT)
    play_next_song()

# Card dealing sound effect
CARD_SLIDE_SOUND_FILE = os.path.join(MUSIC_FOLDER, "Dealing-cards-sound.mp3")
SND_CARD_SLIDE = None
if AUDIO_AVAILABLE and os.path.exists(CARD_SLIDE_SOUND_FILE):
    try:
        SND_CARD_SLIDE = pygame.mixer.Sound(CARD_SLIDE_SOUND_FILE)
        SND_CARD_SLIDE.set_volume(0.4)
    except Exception:
        SND_CARD_SLIDE = None


screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("LuckyLoop+ Blackjack")
clock = pygame.time.Clock()

FONT = pygame.font.SysFont("arial", 20)
BIG_FONT = pygame.font.SysFont("arial", 36, bold=True)
TITLE_FONT = pygame.font.SysFont("arial", 64, bold=True)

# loading table background
TABLE_IMG = None
if os.path.exists(TABLE_BG_FILENAME):
    try:
        TABLE_IMG = pygame.image.load(TABLE_BG_FILENAME).convert()
        TABLE_IMG = pygame.transform.smoothscale(TABLE_IMG, (SCREEN_WIDTH, SCREEN_HEIGHT))
    except Exception:
        TABLE_IMG = None

# load optional sounds
def load_sound(fname):
    if not AUDIO_AVAILABLE:
        return None
    p = os.path.join(SND_FOLDER, fname)
    if os.path.exists(p):
        try:
            return pygame.mixer.Sound(p)
        except Exception:
            return None
    return None

SND_DING = load_sound("ding.wav")
SND_LOSE = load_sound("buzz.wav")
SND_LEVEL = load_sound("levelup.wav")

# Card loader
RANK_MAP = {
    1: "ace", 2:"2", 3:"3", 4:"4", 5:"5", 6:"6", 7:"7",
    8:"8", 9:"9", 10:"10", 11:"jack", 12:"queen", 13:"king"
}
SUITS = ["hearts", "spades", "diamonds", "clubs"]

def find_card_file(rank_name, suit):
    candidates = []
    if rank_name in ("jack","queen","king"):
        candidates.append(f"{rank_name}_of_{suit}2.png")
    candidates.append(f"{rank_name}_of_{suit}.png")
    for fname in candidates:
        p = os.path.join(CARD_FOLDER_PATH, fname)
        if os.path.exists(p):
            return p
    return None

def load_card_image(rank_name, suit):
    path = find_card_file(rank_name, suit)
    if path:
        try:
            img = pygame.image.load(path).convert_alpha()
            img = pygame.transform.smoothscale(img, (CARD_W, CARD_H))
            return img
        except Exception as e:
            print("Error loading:", path, e)
    surf = pygame.Surface((CARD_W, CARD_H), pygame.SRCALPHA)
    surf.fill((240,240,240))
    pygame.draw.rect(surf, (30,30,30), surf.get_rect(), 2, border_radius=8)
    txt = FONT.render(f"{rank_name[0].upper()}{suit[0].upper()}", True, (10,10,10))
    surf.blit(txt, (10,10))
    return surf

# Preload card images
CARD_IMAGES = {}
for r_idx in range(1,14):
    for s in SUITS:
        key = f"{RANK_MAP[r_idx]}_of_{s}"
        CARD_IMAGES[key] = load_card_image(RANK_MAP[r_idx], s)

# card back
CARD_BACK = None
for name in ("card_back.png", "back.png", "cardback.png"):
    p = os.path.join(CARD_FOLDER_PATH, name)
    if os.path.exists(p):
        CARD_BACK = pygame.transform.smoothscale(pygame.image.load(p).convert_alpha(), (CARD_W, CARD_H))
        break
if CARD_BACK is None:
    CARD_BACK = pygame.Surface((CARD_W, CARD_H))
    CARD_BACK.fill((12, 60, 12))
    pygame.draw.rect(CARD_BACK, (255,255,255), CARD_BACK.get_rect(), 2, border_radius=8)


# Card helpers

Card = namedtuple("Card", ["rank","suit","value"])
def make_card(ridx, suit):
    name = RANK_MAP[ridx]
    if name == "ace": v = 11
    elif name in ("jack","queen","king"): v = 10
    else: v = int(name)
    return Card(name, suit, v)

class Shoe:
    def __init__(self, decks=1):
        self.decks = max(1, decks)
        self.reset()
    def reset(self):
        self.cards = []
        for _ in range(self.decks):
            for r in range(1,14):
                for s in SUITS:
                    self.cards.append(make_card(r,s))
        random.shuffle(self.cards)
    def draw(self):
        if not self.cards:
            self.reset()
        return self.cards.pop()

def hand_value(cards):
    total = 0; aces = 0
    for c in cards:
        if c.rank == "ace":
            aces += 1; total += 11
        elif c.rank in ("jack","queen","king"):
            total += 10
        else:
            total += int(c.rank)
    while total > 21 and aces:
        total -= 10; aces -= 1
    return total


# CSV logging into R Studio
def ensure_csv():
    if not os.path.exists(CSV_FILE):
        with open(CSV_FILE, "w", newline="") as f:
            w = csv.writer(f)
            w.writerow([
                "Round",
                "Level",
                "Skill",
                "Encounter",
                "PlayerValue",
                "DealerValue",
                "Result",
                "Reward",
                "Balance",
                "PersistentSkills"
            ])
def log_round(rnd, level, skill, encounter, pv, dv, result, reward, balance, persistent_skills=None):
    with open(CSV_FILE, "a", newline="") as f:
        csv.writer(f).writerow([
            rnd,
            level,
            skill or "",
            encounter or "",
            pv,
            dv,
            result,
            reward,
            balance,
            ",".join(persistent_skills) if persistent_skills else ""
        ])

ensure_csv()


# Game state

class GameState:
    def __init__(self, persistent_skills=None):
        # skills persist between games
        self.active_skills = persistent_skills or []
        
        # round-specific values
        self.balance = STARTING_BALANCE
        self.level = 1
        self.round_no = 0
        self.level_round_no = 0
        self.max_rounds_per_level = 5
        self.shoe = Shoe(LEVELS[self.level]["decks"])
        self.player_skill = None
        self.skill_used_flags = {}
        self.encounter = None
        self.game_over = False
        self.player_cards = []
        self.dealer_cards = []
        self.current_bet = BASE_BETS.get(self.level, 15)
        self.in_round = False
        self.reveal_dealer = False
        self.local_shoe = None

    def start_level(self, level):
        self.level = level
        self.level_round_no = 0
        conf = LEVELS[level]
        self.shoe = Shoe(conf["decks"])
        self.player_skill = None
        self.skill_used_flags = {}
        self.encounter = None
        self.game_over = False
        self.current_bet = BASE_BETS.get(self.level, 15)
        self.in_round = False
        self.reveal_dealer = False

game = GameState()



# Encounters

def roll_encounter():
    if random.random() < ENCOUNTER_CHANCE:
        return random.choice(ENCOUNTERS)
    return None


# Sliding card animation

def slide_card(img, start_pos, end_pos, speed=25):
    x, y = start_pos
    ex, ey = end_pos
    dx = (ex - x)
    dy = (ey - y)
    steps = max(1, int(max(abs(dx), abs(dy)) / speed))
    
    # Play card sound once at start of animation
    if AUDIO_AVAILABLE and SND_CARD_SLIDE:
        SND_CARD_SLIDE.play()

    for i in range(steps):
        t = (i+1)/steps
        xi = int(x + dx * t)
        yi = int(y + dy * t)
        # draw background & HUD
        if TABLE_IMG:
            screen.blit(TABLE_IMG, (0,0))
        else:
            screen.fill((18,130,77))
        draw_hud(game)
        # draw the moving card on top
        screen.blit(img, (xi, yi))
        pygame.display.flip()
        clock.tick(FPS)



# Round flow

def deal_new_round(state: GameState):
    if state.game_over:
        return
    if state.balance < state.current_bet:
            state.game_over = True
            show_game_over(state)
            return
    # increment both global and level-specific round counters
    state.round_no += 1
    state.level_round_no += 1

    # get level configuration
    conf = LEVELS[state.level]

    # roll random encounter
    enc = roll_encounter()
    state.encounter = enc

    # determine decks for this round
    decks = conf["decks"]
    if enc and enc["effect"].get("decks_delta"):
        decks = max(1, decks + enc["effect"]["decks_delta"])
    local_shoe = Shoe(decks)
    state.local_shoe = local_shoe

    # draw initial cards
    p1 = local_shoe.draw()
    p2 = local_shoe.draw()
    d1 = local_shoe.draw()
    d2 = local_shoe.draw()

    state.player_cards = []
    state.dealer_cards = []

    # helper to animate cards once with sound per card
    def animate_card(card, start_pos, end_pos, is_player=True, back=False):
        if back:
            img = CARD_BACK
        else:
            img = card_image_for(card)
        slide_card(img, start_pos, end_pos, speed=35)
        if is_player:
            state.player_cards.append(card)
        else:
            state.dealer_cards.append(card)

    # initial four cards
    animate_card(p1, (SCREEN_WIDTH + 50, SCREEN_HEIGHT//2), player_card_positions(1)[0])
    animate_card(d1, (SCREEN_WIDTH + 50, -50), dealer_card_positions(1)[0], is_player=False, back=True)
    animate_card(p2, (SCREEN_WIDTH + 50, SCREEN_HEIGHT//2), player_card_positions(2)[1])
    animate_card(d2, (SCREEN_WIDTH + 50, -50), dealer_card_positions(2)[1], is_player=False)

    # optional extra card when encounter
    if enc and enc["effect"].get("player_extra_card"):
        card = local_shoe.draw()
        state.player_cards.append(card)
        img = card_image_for(card)
        start = (SCREEN_WIDTH + 50, SCREEN_HEIGHT//2)
        end = player_card_positions(len(state.player_cards))[-1]
        slide_card(img, start, end, speed=35)

    # reset bet
    state.in_round = True
    state.reveal_dealer = (state.player_skill == "Card Peek")

    # play card deal sound 
    if AUDIO_AVAILABLE and SND_DING:
        SND_DING.play()

    # checking if I exceeded max rounds per level
    if state.level_round_no > state.max_rounds_per_level:
        if state.balance >= conf["threshold"]:
            # advance to next level if possible
            if state.level < max(LEVELS.keys()):
                state.start_level(state.level + 1)
                choose_skill_ui(state)
            else:
                # no higher level; just reset rounds for replay
                state.level_round_no = 0
        else:
            # game over
            state.game_over = True
            show_game_over(state)




def card_image_for(card):
    key = f"{card.rank}_of_{card.suit}"
    return CARD_IMAGES.get(key, CARD_BACK)

def player_hit(state: GameState):
    if not state.in_round: return
    card = state.local_shoe.draw()
    state.player_cards.append(card)
    img = card_image_for(card)
    start = (SCREEN_WIDTH + 50, SCREEN_HEIGHT//2)
    end = player_card_positions(len(state.player_cards))[-1]
    slide_card(img, start, end, speed=30)
    if hand_value(state.player_cards) > 21:
        resolve_round(state)

def player_double(state: GameState):
    if not state.in_round: return
    if state.balance >= state.current_bet:  # player must have enough to DOUBLE the bet
        state.balance -= state.current_bet     # deduct extra
        state.current_bet *= 2
        player_hit(state)
        if state.in_round:
            resolve_round(state)

def player_stand(state: GameState):
    if not state.in_round: return
    resolve_round(state)

def dealer_play_and_resolve(state: GameState):
    conf = LEVELS[state.level]
    dealer_hits_soft_17 = conf["dealer_hits_soft_17"]
    if state.encounter and state.encounter["effect"].get("dealer_stands_early"):
        stop_threshold = 14
    elif state.encounter and state.encounter["effect"].get("dealer_hits_soft_12"):
        stop_threshold = 18
    else:
        stop_threshold = None
    while True:
        dv = hand_value(state.dealer_cards)
        if stop_threshold is not None:
            if dv >= stop_threshold: break
            else:
                card = state.local_shoe.draw()
                state.dealer_cards.append(card)
                img = card_image_for(card)
                start = (SCREEN_WIDTH + 50, -50)
                end = dealer_card_positions(len(state.dealer_cards))[-1]
                slide_card(img, start, end, speed=30)
                continue
        if dv < 17:
            card = state.local_shoe.draw()
            state.dealer_cards.append(card)
            img = card_image_for(card)
            start = (SCREEN_WIDTH + 50, -50)
            end = dealer_card_positions(len(state.dealer_cards))[-1]
            slide_card(img, start, end, speed=30)
            continue
        if dv == 17 and dealer_hits_soft_17:
            if random.random() < 0.5:
                card = state.local_shoe.draw()
                state.dealer_cards.append(card)
                img = card_image_for(card)
                start = (SCREEN_WIDTH + 50, -50)
                end = dealer_card_positions(len(state.dealer_cards))[-1]
                slide_card(img, start, end, speed=30)
                continue
        break

def resolve_round(state: GameState):
    # dealer plays
    dealer_play_and_resolve(state)
    pv = hand_value(state.player_cards)
    dv = hand_value(state.dealer_cards)
    conf = LEVELS[state.level]
    result = "push"; reward = 0
    p_black = (len(state.player_cards)==2 and pv==21)
    d_black = (len(state.dealer_cards)==2 and dv==21)

    reward_mult = 1.0
    if state.player_skill:
        sk = SKILLS.get(state.player_skill)
        if sk and sk["type"] == "reward_mult":
            reward_mult *= sk["value"]
    if state.encounter and state.encounter["effect"].get("payout_mult"):
        reward_mult *= state.encounter["effect"]["payout_mult"]

    if p_black and not d_black:
        result = "win"; reward = int(round(state.current_bet * conf["blackjack_payout"] * reward_mult))
    elif d_black and not p_black:
        result = "loss"; reward = -state.current_bet
    elif pv > 21:
        result = "loss"; reward = -state.current_bet
    elif dv > 21:
        result = "win"; reward = state.current_bet
    else:
        if pv > dv:
            result = "win"; reward = state.current_bet
        elif pv < dv:
            result = "loss"; reward = -state.current_bet
        else:
            result = "push"; reward = 0

    # safety net
    if state.player_skill == "Safety Net" and result == "loss" and (state.balance + reward) < 0:
        reward = int(reward / 2)

    reward = int(round(reward * reward_mult))

    state.balance += reward

    # log
    log_round(
    state.round_no,
    state.level,
    state.player_skill or "",
    (state.encounter["name"] if state.encounter else ""),
    pv, dv, result, reward, state.balance,
    persistent_skills=state.active_skills
)
    # sounds
    if AUDIO_AVAILABLE:
        if result == "win" and SND_DING: SND_DING.play()
        if result == "loss" and SND_LOSE: SND_LOSE.play()

    # level up
    next_level = state.level
    if state.balance >= LEVELS[state.level]["threshold"] and state.level < max(LEVELS.keys()):
        next_level = state.level + 1

    state.in_round = False
    state.reveal_dealer = True

    if next_level != state.level:
        if AUDIO_AVAILABLE and SND_LEVEL: SND_LEVEL.play()
        state.start_level(next_level)
        choose_skill_ui(state)

    if state.balance <= 0:
        state.game_over = True
        show_game_over(state)
        return



# UI helpers & drawing

def centered(x): return SCREEN_WIDTH//2 - x//2

def draw_text_wrapped_center(surface, text, rect, font, color=(255,255,255)):
    wrapper = textwrap.TextWrapper(width=30)
    lines = wrapper.wrap(text)
    h = len(lines) * font.get_linesize()
    start_y = rect.y + (rect.height - h)//2
    for i, ln in enumerate(lines):
        surf = font.render(ln, True, color)
        surf_x = rect.x + (rect.width - surf.get_width())//2
        surface.blit(surf, (surf_x, start_y + i*font.get_linesize()))

def draw_button(rect, text, color=(60,120,60), text_color=(255,255,255)):
    pygame.draw.rect(screen, color, rect, border_radius=10)
    pygame.draw.rect(screen, (0,0,0), rect, 2, border_radius=10)
    txt = FONT.render(text, True, text_color)
    screen.blit(txt, (rect.x + (rect.width - txt.get_width())//2, rect.y + (rect.height - txt.get_height())//2))

# card positions
def player_card_positions(n):
    center_x = SCREEN_WIDTH//2
    base_y = SCREEN_HEIGHT - CARD_H - 60
    total_w = (n*CARD_W) + ((n-1)*20)
    start_x = center_x - total_w//2
    return [(start_x + i*(CARD_W+20), base_y) for i in range(n)]

def dealer_card_positions(n):
    center_x = SCREEN_WIDTH//2
    base_y = 60
    total_w = (n*CARD_W) + ((n-1)*20)
    start_x = center_x - total_w//2
    return [(start_x + i*(CARD_W+20), base_y) for i in range(n)]

# HUD & buttons
BTN_W, BTN_H = 160, 56
BTN_X = SCREEN_WIDTH - BTN_W - 40
BTN_HIT = pygame.Rect(BTN_X, SCREEN_HEIGHT - 220, BTN_W, BTN_H)
BTN_STAND = pygame.Rect(BTN_X, SCREEN_HEIGHT - 150, BTN_W, BTN_H)
BTN_DOUBLE = pygame.Rect(BTN_X, SCREEN_HEIGHT - 80, BTN_W, BTN_H)
BTN_NEXT = pygame.Rect(SCREEN_WIDTH - BTN_W - 40, 40, BTN_W, 48)
BTN_BET_UP = pygame.Rect(BTN_X, SCREEN_HEIGHT - 290, 80, 40)
BTN_BET_DOWN = pygame.Rect(BTN_X + 90, SCREEN_HEIGHT - 290, 80, 40)


def draw_hud(state: GameState):
    # background
    if TABLE_IMG:
        screen.blit(TABLE_IMG, (0,0))
    else:
        screen.fill((18,130,77))

    # top banner
    banner = pygame.Rect(0,0,SCREEN_WIDTH,60)
    pygame.draw.rect(screen, (10,10,30), banner)
    title = TITLE_FONT.render("LuckyLoop+", True, (255,215,100))
    screen.blit(title, (20, 6))

    # encounter banner if any
    if state.encounter:
        enc_text = f"Encounter: {state.encounter['name']} - {state.encounter['desc']}"
        txt = FONT.render(enc_text, True, (255,200,0))
        screen.blit(txt, (SCREEN_WIDTH//2 - txt.get_width()//2, 20))

    # right info panel
    info_x = SCREEN_WIDTH - 320
    pygame.draw.rect(screen, (30,30,40), (info_x, 80, 300, 200), border_radius=10)
    screen.blit(FONT.render(f"Balance: ${state.balance}", True, (255,255,255)), (info_x + 12, 90))
    screen.blit(FONT.render(f"Level: {state.level}", True, (255,255,255)), (info_x + 12, 120))
    screen.blit(FONT.render(f"Round: {state.level_round_no}", True, (255,255,255)), (info_x + 12, 150))
    screen.blit(FONT.render(f"Skill: {state.player_skill or 'None'}", True, (255,255,255)), (info_x + 12, 180))
    screen.blit(FONT.render(f"Goal: ${LEVELS[state.level]['threshold']}", True, (255,255,255)), (info_x + 12, 210))
    # Current Bet Display
    screen.blit(FONT.render(f"Bet: ${state.current_bet}", True, (255,255,255)), (BTN_X, SCREEN_HEIGHT - 330))

# Draw + / - buttons
    draw_button(BTN_BET_UP, "+", color=(50,200,50))
    draw_button(BTN_BET_DOWN, "-", color=(200,50,50))

    # left panel for active skill
    left_panel = pygame.Rect(20, SCREEN_HEIGHT - 220, 420, 200)
    pygame.draw.rect(screen, (40,40,60), left_panel, border_radius=10)
    screen.blit(FONT.render("Active Skill", True, (200,200,200)), (left_panel.x + 12, left_panel.y + 8))
    if state.player_skill:
        desc_rect = pygame.Rect(left_panel.x + 10, left_panel.y + 40, left_panel.width - 20, left_panel.height - 48)
        draw_text_wrapped_center(screen, SKILLS[state.player_skill]["desc"], desc_rect, FONT, (240,240,240))

    # buttons
    draw_button(BTN_NEXT, "Next Round", color=(70,130,70))
    draw_button(BTN_HIT, "Hit", color=(80,80,200))
    draw_button(BTN_STAND, "Stand", color=(200,80,80))
    draw_button(BTN_DOUBLE, "Double", color=(200,160,80))


# Skill selection screen

def choose_skill_ui(state: GameState):
    skill_keys = list(SKILLS.keys())
    btns = []
    w = 420; h = 90
    start_x = centered(w)
    start_y = 140
    gap = 18
    for i,k in enumerate(skill_keys):
        r = pygame.Rect(start_x, start_y + i*(h+gap), w, h)
        btns.append((r,k))
    running = True
    while running:
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT: pygame.quit(); sys.exit()
            if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                mx,my = ev.pos
                for r,k in btns:
                    if r.collidepoint(mx,my):
                        state.player_skill = k
                        state.skill_used_flags = {}
                        running = False
            if ev.type == pygame.KEYDOWN and ev.key == pygame.K_ESCAPE:
                state.player_skill = None
                running = False
        # draw
        if TABLE_IMG: screen.blit(TABLE_IMG,(0,0))
        else: screen.fill((6,10,20))
        draw_big = BIG_FONT.render(f"Choose a Skill for Level {state.level}", True, (240,240,240))
        screen.blit(draw_big, (centered(draw_big.get_width()), 40))
        for r,k in btns:
            pygame.draw.rect(screen, (60,60,100), r, border_radius=12)
            pygame.draw.rect(screen, (0,0,0), r, 2, border_radius=12)
            draw_text_wrapped_center(screen, f"{k}: {SKILLS[k]['desc']}", pygame.Rect(r.x+8, r.y+8, r.width-16, r.height-16), FONT, (230,230,230))
        hint = FONT.render("Click a skill to choose it (Esc = no skill).", True, (200,200,200))
        screen.blit(hint, (centered(hint.get_width()), start_y + len(btns)*(h+gap) + 8))
        pygame.display.flip()
        clock.tick(FPS)


# Intro screen 
def intro_screen():
    # prepare text
    title_surface = TITLE_FONT.render("LuckyLoop+", True, (255,215,100))
    subtitle = BIG_FONT.render("A Blackjack Roguelike by Maria Abato", True, (220,220,220))
    prompt = FONT.render("Press any key or click to start", True, (200,200,200))
    fade_alpha = 255
    fade_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
    fade_surface.fill((0,0,0))

    while True:
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if ev.type == pygame.KEYDOWN or (ev.type == pygame.MOUSEBUTTONDOWN and ev.button==1):
                return

        # background
        if TABLE_IMG:
            screen.blit(TABLE_IMG, (0,0))
        else:
            screen.fill((6, 20, 40))

        screen.blit(title_surface, (centered(title_surface.get_width()), 150))
        screen.blit(subtitle, (centered(subtitle.get_width()), 260))
        screen.blit(prompt, (centered(prompt.get_width()), 340))

        if fade_alpha > 0:
            fade_alpha = max(0, fade_alpha - 4)
            fade_surface.set_alpha(fade_alpha)
            screen.blit(fade_surface, (0,0))

        pygame.display.flip()
        clock.tick(FPS)
def show_game_over(state: GameState):
    fade_alpha = 0
    fade_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
    fade_surface.fill((0, 0, 0))
    
    running = True
    while running:
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if ev.type == pygame.KEYDOWN or (ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1):
                # Restart the game
                persistent_skills = state.active_skills  # keep unlocked/stacked skills
                state.__init__(persistent_skills=persistent_skills)  # reset balance but keep skills
                choose_skill_ui(state)  # optionally let player pick a new skill
                running = False

        # Draw background
        if TABLE_IMG:
            screen.blit(TABLE_IMG, (0, 0))
        else:
            screen.fill((18, 30, 50))

        # Game Over banner
        go_text = TITLE_FONT.render("GAME OVER", True, (255, 50, 50))
        screen.blit(go_text, (centered(go_text.get_width()), 150))

        # Final stats
        stats_text = [
            f"Final Balance: ${state.balance}",
            f"Level Reached: {state.level}",
            f"Rounds Completed This Level: {state.level_round_no}/{state.max_rounds_per_level}"
        ]
        for i, txt in enumerate(stats_text):
            surf = BIG_FONT.render(txt, True, (255, 215, 100))
            screen.blit(surf, (centered(surf.get_width()), 260 + i*60))

        # Prompt to restart
        prompt = FONT.render("Press any key or click to restart", True, (220, 220, 220))
        screen.blit(prompt, (centered(prompt.get_width()), SCREEN_HEIGHT - 120))

        # Optional fade-in effect
        if fade_alpha < 180:
            fade_alpha += 5
            fade_surface.set_alpha(fade_alpha)
            screen.blit(fade_surface, (0, 0))

        pygame.display.flip()
        clock.tick(FPS)





# Main loop

def main():
    # validate folders
    if not os.path.isdir(CARD_FOLDER_PATH):
        print("ERROR: CARD_FOLDER_PATH does not exist:", CARD_FOLDER_PATH)
        print("Make sure your card PNGs are at that relative path from this script.")
        pygame.quit(); sys.exit()

    state = game
    intro_screen()
    choose_skill_ui(state)

    running = True
    while running:
        for event in pygame.event.get():

    # Quit game

            if event.type == pygame.QUIT:
                running = False


    # Looping background music
            if event.type == MUSIC_END_EVENT:
                play_next_song()

    # Keyboard Input

            if event.type == pygame.KEYDOWN:

        # N = auto resolve next round
                if event.key == pygame.K_n:
                    if not state.in_round:
                        deal_new_round(state)
                    while state.in_round and hand_value(state.player_cards) < 17:
                        player_hit(state)
                    if state.in_round:
                        player_stand(state)

        # R = restart game fully
                if event.key == pygame.K_r:
                    state.__init__()      # reset GameState
                    choose_skill_ui(state)

    # Mouse Input

            if event.type == pygame.MOUSEBUTTONDOWN:
                mx, my = event.pos
                
        # Next round button
                if pygame.Rect(BTN_NEXT).collidepoint(mx, my):
                    if not state.in_round:
                        deal_new_round(state)

        # Hit
                if BTN_HIT.collidepoint(mx, my) and state.in_round:
                    player_hit(state)

        # Stand
                if BTN_STAND.collidepoint(mx, my) and state.in_round:
                    player_stand(state)

        # Double
                if BTN_DOUBLE.collidepoint(mx, my) and state.in_round:
                    player_double(state)
        # Increase bet
                if BTN_BET_UP.collidepoint(mx,my):
                    if state.current_bet + 50 <= state.balance:
                        state.current_bet += 50

        # Decrease bet
                if BTN_BET_DOWN.collidepoint(mx,my):
                    if state.current_bet - 50 >= 10:
                        state.current_bet -= 50


        # render
        draw_hud(state)

        # draw dealer
        if state.dealer_cards:
            for i, c in enumerate(state.dealer_cards):
                pos = dealer_card_positions(len(state.dealer_cards))[i]
                if i == 0 and state.in_round and not state.reveal_dealer:
                    screen.blit(CARD_BACK, pos)
                else:
                    screen.blit(card_image_for(c), pos)

        # draw player
        if state.player_cards:
            for i,c in enumerate(state.player_cards):
                pos = player_card_positions(len(state.player_cards))[i]
                # drop shadow
                shadow = pygame.Surface((CARD_W, CARD_H), pygame.SRCALPHA)
                shadow.fill((0,0,0,80))
                screen.blit(shadow, (pos[0]+6, pos[1]+6))
                screen.blit(card_image_for(c), pos)

        # bottom hint
        if state.in_round:
            msg = FONT.render("Your turn — Hit / Stand / Double", True, (255,255,255))
        else:
            msg = FONT.render("Click Next Round to play (or press N for autoplay)", True, (220,220,220))
        screen.blit(msg, (40, SCREEN_HEIGHT - 40))

        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()

if __name__ == "__main__":
    main()

