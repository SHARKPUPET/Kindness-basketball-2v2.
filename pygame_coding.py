import pygame, random, math
pygame.init()

# Keep mouse noise down; only use clicks for UI
pygame.event.set_blocked(
    [pygame.MOUSEMOTION, pygame.MOUSEWHEEL, pygame.MOUSEBUTTONUP]
)
pygame.event.set_allowed([pygame.QUIT, pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN])

# -------- window --------
WIDTH, HEIGHT = 900, 540
WIN = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Basketball: 2v2")

# Hoops
left_hoop = pygame.Rect(50, HEIGHT // 2 - 50, 20, 100)
right_hoop = pygame.Rect(WIDTH - 70, HEIGHT // 2 - 50, 20, 100)
HOOP_COLOR = (255, 165, 0)

# Colors
BG = (235, 235, 235)

PLAYER = (60, 120, 255)
TEAM = (23, 236, 236)
DEF = (220, 40, 40)
TXT = (20, 20, 20)
BALL = (0, 0, 0)
FONT = pygame.font.SysFont(None, 26)

def clamp(v, lo, hi): return max(lo, min(hi, v))
def dist(a, b): return math.hypot(a.centerx - b.centerx, a.centery - b.centery)
def clamp_rect_to_screen(r: pygame.Rect):
    r.x = clamp(r.x, 0, WIDTH - r.width)
    r.y = clamp(r.y, 0, HEIGHT - r.height)

# NEW: shot animation helpers
def qbezier(p0, p1, p2, t):
    u = 1 - t
    return (u*u*p0[0] + 2*u*t*p1[0] + t*t*p2[0],
            u*u*p0[1] + 2*u*t*p1[1] + t*t*p2[1])

def make_shot_anim(shooter_rect, hoop_rect, frames=36):
    sx, sy = shooter_rect.center
    hx, hy = hoop_rect.center
    mx, my = (sx + hx) / 2, (sy + hy) / 2 - 130  # arc height
    return {
        "start": (sx, sy),
        "ctrl":  (mx, my),
        "end":   (hx - 6, hy),
        "t": 0.0,
        "dt": 1.0 / max(1, int(frames)),
        "shooter_id": ("player" if shooter_rect is player else
                       "teammate" if shooter_rect is teammate else
                       "def1" if shooter_rect is def1 else "def2")
    }

# Entities
player = pygame.Rect(150, HEIGHT // 2, 28, 28)
teammate = pygame.Rect(250, HEIGHT // 2 - 60, 24, 24)
def1 = pygame.Rect(WIDTH - 200, HEIGHT // 2, 28, 28)
def2 = pygame.Rect(WIDTH - 250, HEIGHT // 2 - 60, 28, 28)

# --- Call-for-ball settings ---
CALL_KEY = pygame.K_q
CALL_RANGE = 360
CALL_CD_FRAMES = 45
call_cd = 0

# Params (defaults restored on hard reset)
DEFAULT_SPEED = 5
DEFAULT_DEF_SPD = 3
DEFAULT_TM_SPD = 4
MIN_SPD, MAX_SPD = 1, 15
MIN_AI_SPD, MAX_AI_SPD = 2, 12
PASS_RANGE, SHOOT_RANGE = 340, 90
FPS = 60

# Speeds (runtime)
speed = DEFAULT_SPEED
defender_speed = DEFAULT_DEF_SPD
teammate_speed = DEFAULT_TM_SPD

# Steal settings
STEAL_KEY = pygame.K_f
STEAL_RANGE = 36
STEAL_CD_FRAMES = 20

# RAGE: emotion meter settings/state
RAGE_MIN, RAGE_MAX = 0, 100
RAGE_DECAY_FRAMES = 75
rage = 0
rage_decay_tick = 0

# Game state
score = opp_score = 0
kindness_score = 0
msg = ("Move: WASD/Arrows | Shoot: SPACE | Pass: E | Call: Q| Steal: F | "
       "Reset: R | Pause: P | Quit: ESC")
ball_holder = "player"         # "player", "teammate", "def1", "def2"
shooting_anim = None
paused = False
teammate_shot_cooldown = 0
player_steal_cd = 0

# WIN: add win target and flag
WIN_TARGET = 20
game_over = False

# Passing state
passing = None  # {"pos":[x,y], "to":Rect, "vx":float, "vy":float, "frames":int}

# Off-ball targets
player_target = [player.x, player.y]
teammate_target = [teammate.x, teammate.y]

# Always-freeze-when-you-have-ball
FREEZE_ON_POSSESSION = True
decision_mode = False
decision_holder = None

# UI buttons
BTN_RESET = pygame.Rect(WIDTH - 140, 12, 120, 36)
BTN_PAUSE = pygame.Rect(WIDTH - 140, 60, 120, 36)
BTN_PLUS  = pygame.Rect(WIDTH - 140, 108, 56, 36)
BTN_MINUS = pygame.Rect(WIDTH - 76, 108, 56, 36)
BTN_SHOOT = pygame.Rect(WIDTH - 140, 156, 120, 36)
BTN_PASS  = pygame.Rect(WIDTH - 140, 204, 120, 36)

def teammate_should_pass(to_player: pygame.Rect) -> bool:
    d = dist(teammate, to_player)
    if d > CALL_RANGE:
        return False
    base = 0.85 - clamp((d - 60) / 240.0, 0, 1) * 0.50
    near_passer = min(dist(teammate, def1), dist(teammate, def2))
    near_receiver = min(dist(to_player, def1), dist(to_player, def2))
    penalty = 0.0
    if near_passer < 60:   penalty += 0.25
    if near_receiver < 60: penalty += 0.25
    p = clamp(base - penalty, 0.10, 0.90)
    return random.random() < p

def draw_button(rect, label):
    mouse_pos = pygame.mouse.get_pos()
    base = (210, 210, 210) if rect.collidepoint(mouse_pos) else (190, 190, 190)
    pygame.draw.rect(WIN, base, rect, border_radius=6)
    pygame.draw.rect(WIN, (100, 100, 100), rect, 2, border_radius=6)
    WIN.blit(FONT.render(label, True, (20, 20, 20)),
             (rect.x + 12, rect.y + 7))

def draw_ball_outline(rect):
    pygame.draw.circle(WIN, BALL, rect.center, rect.width // 2 + 3, 5)

def toggle_pause():
    global paused, msg
    if game_over:
        return
    paused = not paused
    msg = "Paused. Press P or Button to resume." if paused else "Resumed!"

def adjust_speed(delta):
    global speed, teammate_speed, defender_speed, msg
    speed = clamp(speed + delta, MIN_SPD, MAX_SPD)
    teammate_speed = clamp(teammate_speed + delta, MIN_AI_SPD, MAX_AI_SPD)
    defender_speed = clamp(defender_speed + delta, MIN_AI_SPD, MAX_AI_SPD)
    msg = (f"Speeds -> Player:{speed}  Teammate:{teammate_speed}  "
           f"Defenders:{defender_speed}")

def shot_make_prob(shooter_rect, hoop_rect, defenders):
    dx = shooter_rect.centerx - hoop_rect.centerx
    dy = shooter_rect.centery - hoop_rect.centery
    d = math.hypot(dx, dy)
    base = 0.85 - clamp((d - 40) / 200.0, 0, 1) * 0.65
    closest = min(dist(shooter_rect, de) for de in defenders)
    contest = clamp((80 - closest) / 80.0, 0, 1)
    p = base - 0.35 * contest
    return clamp(p, 0.05, 0.95)

def start_pass(from_rect, to_rect, frames=18):
    global passing, ball_holder, msg
    sx, sy = from_rect.center
    tx, ty = to_rect.center
    frames = max(1, int(frames))
    passing = {"pos": [float(sx), float(sy)],
               "to": to_rect,
               "vx": (tx - sx) / frames,
               "vy": (ty - sy) / frames,
               "frames": frames}
    ball_holder = None
    msg = "Passing..."

def enter_decision():
    global decision_mode, decision_holder, msg
    decision_mode = True
    decision_holder = "player"
    msg = "Your ball. Choose: Shoot or Pass."

def exit_decision():
    global decision_mode, decision_holder
    decision_mode = False
    decision_holder = None

def give_ball_to(who):
    global ball_holder
    if game_over:
        return
    ball_holder = who
    if who == "player" and FREEZE_ON_POSSESSION:
        enter_decision()

# Rage helpers
def check_rage_loss():
    global game_over, paused, decision_mode, msg
    if not game_over and rage >= 50:
        game_over = True
        paused = True
        decision_mode = False
        msg = "You lost! Too much rage. Press R to restart."

def adjust_rage(delta, note=None):
    global rage, msg
    old = rage
    rage = clamp(rage + delta, RAGE_MIN, RAGE_MAX)
    if note:
        msg = f"{note} Rage {old}->{rage}."
    check_rage_loss()

# WIN: check function
def check_win():
    global game_over, paused, decision_mode, msg
    if not game_over and (score + kindness_score) >= WIN_TARGET:
        game_over = True
        paused = True
        decision_mode = False
        msg = "You win! Press R to restart."

def try_player_steal(holder_rect):
    if dist(player, holder_rect) > STEAL_RANGE:
        return False
    d = dist(player, holder_rect)
    p = clamp(0.45 - (d / max(1.0, STEAL_RANGE)) * 0.35, 0.10, 0.45)
    return random.random() < p

def hard_reset():
    global speed, defender_speed, teammate_speed
    global score, opp_score, kindness_score, msg, shooting_anim
    global teammate_shot_cooldown, player_steal_cd, passing
    global player_target, teammate_target, decision_mode, decision_holder
    global call_cd, game_over
    global rage, rage_decay_tick

    call_cd = 0
    game_over = False

    # reset speeds to defaults
    speed = DEFAULT_SPEED
    defender_speed = DEFAULT_DEF_SPD
    teammate_speed = DEFAULT_TM_SPD

    # reset positions
    player.update(150, HEIGHT // 2, 28, 28)
    teammate.update(250, HEIGHT // 2 - 60, 24, 24)
    def1.update(WIDTH - 200, HEIGHT // 2, 28, 28)
    def2.update(WIDTH - 250, HEIGHT // 2 - 60, 28, 28)

    # reset game state
    score = 0
    opp_score = 0
    kindness_score = 0
    msg = ("Reset. Move: WASD/Arrows | Shoot: SPACE | Pass: E | Steal: F | "
           "Reset: R | Pause: P | Quit: ESC")
    shooting_anim = None
    teammate_shot_cooldown = 0
    player_steal_cd = 0
    passing = None

    # targets
    player_target[:] = [player.x, player.y]
    teammate_target[:] = [teammate.x, teammate.y]

    # RAGE: reset
    rage = 0
    rage_decay_tick = 0

    # give ball to player and freeze
    decision_mode = False
    decision_holder = None
    give_ball_to("player")

# initial hard reset to clean start
hard_reset()

clock = pygame.time.Clock()
running = True
while running:
    clock.tick(FPS)

    # ---------- EVENTS ----------
    for e in pygame.event.get():
        if e.type == pygame.QUIT:
            running = False

        # Mouse UI
        if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
            if BTN_PAUSE.collidepoint(e.pos):
                toggle_pause()
            elif BTN_RESET.collidepoint(e.pos):
                hard_reset()
            elif BTN_PLUS.collidepoint(e.pos):
                adjust_speed(+1)
            elif BTN_MINUS.collidepoint(e.pos):
                adjust_speed(-1)
            elif decision_mode and decision_holder == "player" and not game_over:
                if BTN_SHOOT.collidepoint(e.pos):
                    # queue shot
                    close_d = min(dist(player, def1), dist(player, def2))
                    block_chance = (0.02 +
                                    clamp((60 - close_d) / 60.0, 0, 1) * 0.25)
                    if close_d < 60 and random.random() < block_chance:
                        msg = "Shot BLOCKED!"
                        adjust_rage(+10, "Shot BLOCKED!")
                        exit_decision()
                        give_ball_to(random.choice(["def1", "def2"]))
                    else:
                        msg = "Shot Attempt..."
                        shooting_anim = make_shot_anim(player, right_hoop, frames=36)
                        exit_decision()
                elif BTN_PASS.collidepoint(e.pos):
                    start_pass(player, teammate, frames=18)
                    kindness_score += 1
                    adjust_rage(-2, "Nice pass.")
                    check_win()
                    exit_decision()

        # Keys
        if e.type == pygame.KEYDOWN:
            if e.key == pygame.K_ESCAPE:
                running = False
            elif e.key == pygame.K_p:
                toggle_pause()
            elif e.key == pygame.K_r:
                hard_reset()
            elif e.key in (pygame.K_EQUALS, pygame.K_PLUS):
                adjust_speed(+1)
            elif e.key in (pygame.K_MINUS, pygame.K_UNDERSCORE):
                adjust_speed(-1)

            # Decision hotkeys (SPACE=shoot, E=pass) when frozen
            elif decision_mode and decision_holder == "player" and not game_over:
                if e.key == pygame.K_SPACE:
                    close_d = min(dist(player, def1), dist(player, def2))
                    block_chance = (0.02 +
                                    clamp((60 - close_d) / 60.0, 0, 1) * 0.25)
                    if close_d < 60 and random.random() < block_chance:
                        msg = "Shot BLOCKED!"
                        adjust_rage(+10, "Shot BLOCKED!")
                        exit_decision()
                        give_ball_to(random.choice(["def1", "def2"]))
                    else:
                        msg = "Shot Attempt..."
                        shooting_anim = make_shot_anim(player, right_hoop, frames=36)
                        exit_decision()
                elif e.key == pygame.K_e:
                    start_pass(player, teammate, frames=18)
                    kindness_score += 1
                    adjust_rage(-2, "Nice pass.")
                    check_win()
                    exit_decision()

            # Steal input during live play (opponent has ball)
            elif (not paused and not decision_mode and not game_over and
                  ball_holder in ("def1", "def2") and e.key == STEAL_KEY):
                if player_steal_cd == 0:
                    holder = def1 if ball_holder == "def1" else def2
                    if try_player_steal(holder):
                        msg = "You stole the ball!"
                        adjust_rage(-5, "You stole it.")
                        give_ball_to("player")
                    else:
                        msg = "Steal failed."
                        adjust_rage(+2, "Steal failed.")
                    player_steal_cd = STEAL_CD_FRAMES
                else:
                    msg = "Steal cooling down..."
            # Call for the ball (Q) when teammate has it
            elif ball_holder == "teammate" and e.key == CALL_KEY and not game_over:
                if call_cd == 0 and passing is None and shooting_anim is None:
                    if (dist(player, teammate) <= CALL_RANGE and
                            teammate_should_pass(player)):
                        start_pass(teammate, player,
                                   frames=max(10, int(dist(player, teammate)
                                                      / 20)))
                        msg = "You called for it! Teammate passing..."
                        adjust_rage(-1, "Got the ball.")
                        call_cd = CALL_CD_FRAMES
                    else:
                        msg = "Teammate ignored your call."
                        adjust_rage(+1, "Ignored call.")
                        call_cd = CALL_CD_FRAMES
                else:
                    msg = "Call cooling down..."

    # ---------- UPDATES ----------
    if not paused and not decision_mode and not game_over:
        # cooldowns
        if teammate_shot_cooldown > 0:
            teammate_shot_cooldown -= 1
        if player_steal_cd > 0:
            player_steal_cd -= 1
        if call_cd > 0:
            call_cd -= 1

        # RAGE: passive decay
        if rage > 0:
            rage_decay_tick += 1
            if rage_decay_tick >= RAGE_DECAY_FRAMES:
                rage = max(RAGE_MIN, rage - 1)
                rage_decay_tick = 0

        # pass animation
        if passing is not None:
            passing["pos"][0] += passing["vx"]
            passing["pos"][1] += passing["vy"]
            passing["frames"] -= 1
            if passing["frames"] <= 0:
                # pass completed
                target = passing["to"]
                passing = None
                msg = "Pass received!"
                if target is teammate:
                    ball_holder = "teammate"
                elif target is player:
                    give_ball_to("player")
                else:
                    ball_holder = ball_holder  # shouldn't happen

        # player movement (manual, live)
        if shooting_anim is None:
            keys = pygame.key.get_pressed()
            dx = ((keys[pygame.K_RIGHT] or keys[pygame.K_d]) -
                  (keys[pygame.K_LEFT]  or keys[pygame.K_a]))
            dy = ((keys[pygame.K_DOWN]  or keys[pygame.K_s]) -
                  (keys[pygame.K_UP]    or keys[pygame.K_w]))
            if dx or dy:
                mag = (dx*dx + dy*dy) ** 0.5
                player.x += int(speed * dx / (mag or 1))
                player.y += int(speed * dy / (mag or 1))
                clamp_rect_to_screen(player)
                player_target = [player.x, player.y]

        # player off-ball drift
        if ball_holder != "player":
            dx, dy = player_target[0] - player.x, player_target[1] - player.y
            d = max(1, math.hypot(dx, dy))
            if d > 2:
                player.x += int(speed * dx / d)
                player.y += int(speed * dy / d)
                clamp_rect_to_screen(player)

        # teammate logic
        if ball_holder == "teammate":
            tx, ty = right_hoop.center
            dx, dy = tx - teammate.centerx, ty - teammate.centery
            d = max(1, math.hypot(dx, dy))
            teammate.x += int(teammate_speed * dx / d)
            teammate.y += int(teammate_speed * dy / d)
            clamp_rect_to_screen(teammate)
            teammate_target = [teammate.x, teammate.y]

            # shoot logic
            if (dist(teammate, right_hoop) < SHOOT_RANGE and
                    shooting_anim is None and
                    teammate_shot_cooldown == 0):
                closest_def = min(dist(teammate, def1), dist(teammate, def2))
                if closest_def > 50 or random.random() < 0.35:
                    msg = "Teammate shoots!"
                    shooting_anim = make_shot_anim(teammate, right_hoop, frames=36)
                    teammate_shot_cooldown = 45

        elif ball_holder in ("def1", "def2"):
            # teammate retreats/help
            enemy = def1 if ball_holder == "def1" else def2
            tx = (left_hoop.centerx + enemy.centerx) // 2
            ty = (left_hoop.centery + enemy.centery) // 2
            dx, dy = tx - teammate.centerx, ty - teammate.centery
            d = max(1, math.hypot(dx, dy))
            teammate.x += int(teammate_speed * dx / d)
            teammate.y += int(teammate_speed * dy / d)
            clamp_rect_to_screen(teammate)

        else:
            # roaming
            if random.random() < 0.01 or dist(teammate, player) < 40:
                teammate_target = [random.randint(80, WIDTH - 80),
                                   random.randint(80, HEIGHT - 80)]
            dx, dy = teammate_target[0] - teammate.x, teammate_target[1] - teammate.y
            d = max(1, math.hypot(dx, dy))
            if d > 2:
                teammate.x += int(teammate_speed * dx / d)
                teammate.y += int(teammate_speed * dy / d)
                clamp_rect_to_screen(teammate)

        # defenders
        if ball_holder in ("def1", "def2") and shooting_anim is None:
            for d_rect in (def1, def2):
                tx, ty = left_hoop.center
                dx, dy = tx - d_rect.centerx, ty - d_rect.centery
                d = max(1, math.hypot(dx, dy))
                d_rect.x += int(defender_speed * dx / d)
                d_rect.y += int(defender_speed * dy / d)
                clamp_rect_to_screen(d_rect)
            holder = def1 if ball_holder == "def1" else def2
            if dist(holder, left_hoop) < SHOOT_RANGE and shooting_anim is None:
                msg = "Opponent shoots!"
                shooter = def1 if ball_holder == "def1" else def2
                shooting_anim = make_shot_anim(shooter, left_hoop, frames=36)
        else:
            if ball_holder == "player":
                ball_rect, off_rect = player, teammate
            elif ball_holder == "teammate":
                ball_rect, off_rect = teammate, player
            else:
                ball_rect, off_rect = player, teammate

            if dist(def1, ball_rect) <= dist(def2, ball_rect):
                main_def, help_def = def1, def2
            else:
                main_def, help_def = def2, def1

            dx = ball_rect.centerx - main_def.centerx
            dy = ball_rect.centery - main_def.centery
            d = max(1, math.hypot(dx, dy))
            main_def.x += int(defender_speed * dx / d + random.randint(-1, 1))
            main_def.y += int(defender_speed * dy / d + random.randint(-1, 1))
            clamp_rect_to_screen(main_def)

            dx = off_rect.centerx - help_def.centerx
            dy = off_rect.centery - help_def.centery
            d = max(1, math.hypot(dx, dy))
            if d > 40:
                help_def.x += int(defender_speed * dx / d + random.randint(-2, 2))
                help_def.y += int(defender_speed * dy / d + random.randint(-2, 2))
                clamp_rect_to_screen(help_def)

            if random.random() < 0.005:
                def1, def2 = def2, def1

            # AI steal
            if (ball_rect.colliderect(main_def) and random.random() < 0.1 and
                    shooting_anim is None and passing is None):
                msg = "Ball stolen!"
                adjust_rage(+5, "Ball stolen!")
                give_ball_to("def1" if main_def == def1 else "def2")

        # teammate clutch-steal
        if ball_holder in ("def1", "def2") and shooting_anim is None:
            holder = def1 if ball_holder == "def1" else def2
            if teammate.colliderect(holder) and random.random() < 0.08:
                msg = "Teammate stole the ball!"
                ball_holder = "teammate"
                kindness_score += 1
                adjust_rage(-3, "Teammate steal.")
                check_win()

        # NEW: shooting animation + resolution
        if shooting_anim:
            shooting_anim["t"] += shooting_anim["dt"]
            t = min(1.0, shooting_anim["t"])

            if t >= 1.0:
                # resolve make/miss
                if shooting_anim["shooter_id"] in ("player", "teammate"):
                    shooter_rect = player if shooting_anim["shooter_id"] == "player" else teammate
                    hoop = right_hoop
                    defenders_list = [def1, def2]
                    team_scored = True
                else:
                    shooter_rect = def1 if shooting_anim["shooter_id"] == "def1" else def2
                    hoop = left_hoop
                    defenders_list = [player, teammate]
                    team_scored = False

                p = shot_make_prob(shooter_rect, hoop, defenders_list)
                if random.random() < p:
                    if team_scored:
                        score += 1
                        msg = "Bucket!"
                        adjust_rage(-6, "Bucket!")
                        give_ball_to(random.choice(["def1", "def2"]))
                        check_win()
                    else:
                        opp_score += 1
                        msg = "Opponent scored!"
                        adjust_rage(+8, "Opponent scored!")
                        give_ball_to("player")
                else:
                    msg = "Missed!"
                    if team_scored:
                        adjust_rage(+2, "Missed.")
                    nxt = random.choice(
                        (["def1", "def2"] if team_scored else ["player", "teammate"])
                        + ["player", "teammate", "def1", "def2"]
                    )
                    if nxt == "player":
                        give_ball_to("player")
                    else:
                        ball_holder = nxt

                shooting_anim = None

    # -------- Draw --------
    WIN.fill(BG)
    pygame.draw.rect(WIN, HOOP_COLOR, left_hoop)
    pygame.draw.rect(WIN, HOOP_COLOR, right_hoop)
    pygame.draw.circle(WIN, PLAYER, player.center, player.width // 2)
    pygame.draw.circle(WIN, TEAM, teammate.center, teammate.width // 2)
    pygame.draw.circle(WIN, DEF, def1.center, def1.width // 2)
    pygame.draw.circle(WIN, DEF, def2.center, def2.width // 2)

    # Ball render
    if passing is not None:
        cx, cy = int(passing["pos"][0]), int(passing["pos"][1])
        pygame.draw.circle(WIN, BALL, (cx, cy), 14, 0)
        pygame.draw.circle(WIN, BALL, (cx, cy), 18, 4)
    elif shooting_anim:
        bx, by = qbezier(shooting_anim["start"],
                         shooting_anim["ctrl"],
                         shooting_anim["end"],
                         min(1.0, shooting_anim["t"]))
        pygame.draw.circle(WIN, BALL, (int(bx), int(by)), 14, 0)
        pygame.draw.circle(WIN, BALL, (int(bx), int(by)), 18, 4)
    else:
        if ball_holder == "player":   draw_ball_outline(player)
        elif ball_holder == "teammate": draw_ball_outline(teammate)
        elif ball_holder == "def1":   draw_ball_outline(def1)
        elif ball_holder == "def2":   draw_ball_outline(def2)

    # HUD
    WIN.blit(FONT.render(f"Score: {score}  Opp: {opp_score}", True, TXT),
             (16, 12))
    WIN.blit(FONT.render(msg, True, TXT), (16, 40))
    WIN.blit(FONT.render(f"Kindness: {kindness_score}", True, TXT),
             (16, 68))
    WIN.blit(FONT.render(f"Speed: {speed}", True, TXT), (16, 96))
    WIN.blit(FONT.render("Steal: F", True, TXT), (16, 124))
    WIN.blit(FONT.render(f"Win at: Score + Kindness = {WIN_TARGET}", True,
                         TXT), (16, 152))

    # RAGE: label + bar
    WIN.blit(FONT.render(f"Rage: {rage}", True, TXT), (16, 180))
    meter_bg = pygame.Rect(16, 200, 180, 10)
    pygame.draw.rect(WIN, (200, 200, 200), meter_bg)
    fill_w = int(meter_bg.width * rage / RAGE_MAX)
    pygame.draw.rect(WIN, (220, 80, 80),
                     (meter_bg.x, meter_bg.y, fill_w, meter_bg.height))

    # Buttons
    draw_button(BTN_PAUSE, "PAUSE (P)")
    draw_button(BTN_RESET, "RESET (R)")
    draw_button(BTN_PLUS,  "+")
    draw_button(BTN_MINUS, "–")

    # Decision overlay
    if decision_mode and decision_holder == "player" and not game_over:
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 110))
        WIN.blit(overlay, (0, 0))

        def draw_big_button(rect, label):
            mouse_pos = pygame.mouse.get_pos()
            base = (230, 230, 230) if rect.collidepoint(mouse_pos) else (200, 200, 200)
            pygame.draw.rect(WIN, base, rect, border_radius=8)
            pygame.draw.rect(WIN, (80, 80, 80), rect, 2, border_radius=8)
            WIN.blit(FONT.render(label, True, (10, 10, 10)),
                     (rect.x + 18, rect.y + 7))

        draw_big_button(BTN_SHOOT, "SHOOT (SPACE)")
        draw_big_button(BTN_PASS,  "PASS (E)")

    # Paused overlay
    if paused and not game_over:
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 90))
        WIN.blit(overlay, (0, 0))
        WIN.blit(FONT.render("Paused", True, (10, 10, 10)),
                 (WIDTH // 2 - 40, 12))

    # WIN: victory screen (only if not rage-lost)
    if game_over and rage < 50:
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 140))
        WIN.blit(overlay, (0, 0))

        title = FONT.render("YOU WIN!", True, (255, 255, 255))
        sub   = FONT.render(f"Score + Kindness = {score + kindness_score} / "
                            f"{WIN_TARGET}", True, (230, 230, 230))
        hint  = FONT.render("Press R to restart", True, (210, 210, 210))

        WIN.blit(title, (WIDTH//2 - title.get_width()//2, HEIGHT//2 - 40))
        WIN.blit(sub,   (WIDTH//2 - sub.get_width()//2,   HEIGHT//2 - 10))
        WIN.blit(hint,  (WIDTH//2 - hint.get_width()//2,  HEIGHT//2 + 20))

    # lose
    if game_over and rage >= 50:
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        WIN.blit(overlay, (0, 0))

        title = FONT.render("YOU LOSE!", True, (255, 80, 80))
        sub   = FONT.render(f"Rage hit {rage} / 50", True, (240, 200, 200))
        hint  = FONT.render("Press R to restart", True, (220, 220, 220))

        WIN.blit(title, (WIDTH//2 - title.get_width()//2, HEIGHT//2 - 40))
        WIN.blit(sub,   (WIDTH//2 - sub.get_width()//2,   HEIGHT//2 - 10))
        WIN.blit(hint,  (WIDTH//2 - hint.get_width()//2,  HEIGHT//2 + 20))

    # flip every frame
    pygame.display.flip()

pygame.quit()
