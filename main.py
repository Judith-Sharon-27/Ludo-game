import pygame
import random
import sys
import math

pygame.init()
WIDTH, HEIGHT = 1180, 820
BOARD_SIZE = 720
BOARD_X, BOARD_Y = 35, 50
CELL = BOARD_SIZE // 15
PANEL_X = 790

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Ludo - Classic Board Game")
clock = pygame.time.Clock()

# ----------------------------- Fonts -------------------------
FONT = pygame.font.SysFont("arial", 20)
SMALL = pygame.font.SysFont("arial", 15)
MEDIUM = pygame.font.SysFont("arial", 25, bold=True)
BIG = pygame.font.SysFont("arial", 38, bold=True)
TITLE = pygame.font.SysFont("arial", 46, bold=True)

# ---------------------------- Colors -------------------------
BG = (242, 239, 232)
BOARD = (250, 249, 245)
GRID = (75, 75, 75)
DARK = (38, 38, 38)
WHITE = (255, 255, 255)
BLACK = (25, 25, 25)
SHADOW = (0, 0, 0, 35)

COLORS = {
    "red": (221, 63, 65),
    "green": (52, 166, 91),
    "yellow": (245, 193, 55),
    "blue": (65, 112, 208),
}

LIGHT = {
    "red": (255, 224, 224),
    "green": (220, 247, 229),
    "yellow": (255, 245, 202),
    "blue": (222, 232, 255),
}

PLAYER_ORDER = ["red", "green", "yellow", "blue"]

# Standard 52-space outer track.
TRACK = [
    (6,0),(7,0),(8,0),(8,1),(8,2),
    (9,2),(10,2),(11,2),(12,2),(13,2),(14,2),
    (14,3),(14,4),(14,5),(14,6),(13,6),(12,6),
    (12,7),(12,8),(13,8),(14,8),(14,9),(14,10),
    (14,11),(14,12),(14,13),(14,14),(13,14),(12,14),
    (11,14),(10,14),(9,14),(8,14),(8,13),(8,12),
    (8,11),(8,10),(8,9),(7,9),(6,9),(6,10),(6,11),
    (6,12),(6,13),(6,14),(5,14),(4,14),(3,14),(2,14),
    (1,14),(0,14),(0,13),(0,12),(0,11),(0,10),(0,9),
    (1,9),(2,9),(2,8),(1,8),(0,8),(0,7),(0,6),(0,5),
    (0,4),(0,3),(0,2),(1,2),(2,2),(3,2),(4,2),(5,2),
    (6,2),(6,1)
]

# We use the first 52 positions of the classic perimeter path.
TRACK = TRACK[:52]

START = {
    "red": 0,
    "green": 13,
    "yellow": 26,
    "blue": 39,
}

# Five-space home lanes.
LANES = {
    "red": [(7,1),(7,2),(7,3),(7,4),(7,5)],
    "green": [(13,7),(12,7),(11,7),(10,7),(9,7)],
    "yellow": [(7,13),(7,12),(7,11),(7,10),(7,9)],
    "blue": [(1,7),(2,7),(3,7),(4,7),(5,7)],
}

CENTER = (7, 7)

# Safe squares: starting squares + four star/safe positions.
SAFE = set(START.values()) | {8, 21, 34, 47}

# Yard/home token positions.
YARD = {
    "red": [(2,2),(4,2),(2,4),(4,4)],
    "green": [(10,2),(12,2),(10,4),(12,4)],
    "yellow": [(10,10),(12,10),(10,12),(12,12)],
    "blue": [(2,10),(4,10),(2,12),(4,12)],
}

BASES = {
    "red": (0,0),
    "green": (9,0),
    "yellow": (9,9),
    "blue": (0,9),
}

# Token state:
# -1 = yard
# 0..51 = outer track
# 52..56 = home lane, 56 = center/finished.
players = {c: [-1, -1, -1, -1] for c in PLAYER_ORDER}

current = 0
dice = None
winner = None
must_choose = False
message = "Red's turn — roll the dice!"
rolling = False
roll_frames = 0
roll_value = 1
no_move_timer = 0

# ------------------------- Helpers ----------------------------

def board_rect():
    return pygame.Rect(BOARD_X, BOARD_Y, BOARD_SIZE, BOARD_SIZE)


def cell_rect(col, row):
    return pygame.Rect(
        BOARD_X + col * CELL,
        BOARD_Y + row * CELL,
        CELL,
        CELL
    )


def cell_center(pos):
    col, row = pos
    r = cell_rect(col, row)
    return r.center


def draw_text(text, pos, font=FONT, color=DARK, center=False):
    surf = font.render(text, True, color)
    rect = surf.get_rect()
    if center:
        rect.center = pos
    else:
        rect.topleft = pos
    screen.blit(surf, rect)


def draw_round_rect(rect, color, radius=14, outline=None, width=1):
    pygame.draw.rect(screen, color, rect, border_radius=radius)
    if outline:
        pygame.draw.rect(screen, outline, rect, width, border_radius=radius)


def shade(color, amount):
    return tuple(max(0, min(255, c + amount)) for c in color)


def track_pos(index):
    return TRACK[index % 52]


def absolute_distance(color, state):
    if state < 0:
        return None
    if state <= 51:
        return (state - START[color]) % 52
    return 52 + (state - 52)


def token_grid_pos(color, idx):
    state = players[color][idx]

    if state == -1:
        return YARD[color][idx]

    if state <= 51:
        return track_pos(state)

    if state <= 56:
        if state == 56:
            return CENTER
        return LANES[color][state - 52]

    return CENTER


def token_pixel_pos(color, idx, offset=(0, 0)):
    x, y = cell_center(token_grid_pos(color, idx))
    return int(x + offset[0]), int(y + offset[1])


def legal_tokens(color, roll):
    result = []

    for i, state in enumerate(players[color]):
        if state == 56:
            continue

        if state == -1:
            if roll == 6:
                result.append(i)
        else:
            distance = absolute_distance(color, state)
            if distance is not None and distance + roll <= 56:
                result.append(i)

    return result


def move_token(color, idx, roll):
    state = players[color][idx]

    if state == -1:
        players[color][idx] = START[color]
        return

    distance = absolute_distance(color, state)
    new_distance = distance + roll

    if new_distance >= 52:
        players[color][idx] = 52 + (new_distance - 52)
    else:
        players[color][idx] = (START[color] + new_distance) % 52


def capture_if_possible(color, idx):
    state = players[color][idx]

    if state < 0 or state > 51 or state in SAFE:
        return 0

    captured = 0

    for other in PLAYER_ORDER:
        if other == color:
            continue

        for j, other_state in enumerate(players[other]):
            if other_state == state:
                players[other][j] = -1
                captured += 1

    return captured


def has_won(color):
    return all(s == 56 for s in players[color])


def reset_game():
    global current, dice, winner, must_choose, message
    global rolling, roll_frames, roll_value, no_move_timer

    for c in PLAYER_ORDER:
        players[c] = [-1, -1, -1, -1]

    current = 0
    dice = None
    winner = None
    must_choose = False
    rolling = False
    roll_frames = 0
    roll_value = 1
    no_move_timer = 0
    message = "Red's turn — roll the dice!"


def next_turn(extra=False):
    global current, dice, must_choose, message

    dice = None
    must_choose = False

    if not extra:
        current = (current + 1) % 4

    message = f"{PLAYER_ORDER[current].capitalize()}'s turn — roll the dice!"


def finish_move(color, idx, roll):
    global dice, must_choose, winner, message

    move_token(color, idx, roll)
    captured = capture_if_possible(color, idx)

    if has_won(color):
        winner = color
        dice = None
        must_choose = False
        message = f"{color.capitalize()} wins! Press R to play again."
        return

    extra = roll == 6 or captured > 0

    if extra:
        dice = None
        must_choose = False

        if captured:
            message = f"{color.capitalize()} captured a token — extra turn!"
        else:
            message = f"{color.capitalize()} rolled a 6 — extra turn!"
    else:
        next_turn()


# ------------------------- Drawing ----------------------------

def draw_background():
    screen.fill(BG)

    # Header
    draw_text("LUDO", (BOARD_X, 8), TITLE, DARK)
    draw_text(
        "Classic four-player board game",
        (BOARD_X + 150, 23),
        SMALL,
        (105, 105, 105)
    )


def draw_base(color):
    bx, by = BASES[color]
    outer = pygame.Rect(
        BOARD_X + bx * CELL,
        BOARD_Y + by * CELL,
        CELL * 6,
        CELL * 6
    )

    # Shadow
    shadow = outer.move(5, 6)
    pygame.draw.rect(screen, (215, 211, 202), shadow, border_radius=18)

    draw_round_rect(outer, COLORS[color], 18)

    inner = pygame.Rect(
        outer.x + CELL,
        outer.y + CELL,
        CELL * 4,
        CELL * 4
    )

    draw_round_rect(inner, WHITE, 18, shade(COLORS[color], -35), 2)

    # Four token homes
    for p in YARD[color]:
        cx, cy = cell_center(p)
        pygame.draw.circle(screen, LIGHT[color], (cx, cy), CELL // 2 - 7)
        pygame.draw.circle(screen, shade(COLORS[color], -20), (cx, cy), CELL // 2 - 7, 2)


def draw_board_cells():
    br = board_rect()

    pygame.draw.rect(screen, BOARD, br, border_radius=20)
    pygame.draw.rect(screen, DARK, br, 4, border_radius=20)

    # Light grid.
    for row in range(15):
        for col in range(15):
            r = cell_rect(col, row)
            pygame.draw.rect(screen, (232, 231, 226), r, 1)

    # Four colored bases.
    for color in PLAYER_ORDER:
        draw_base(color)

    # Outer track cells.
    for i, p in enumerate(TRACK):
        r = cell_rect(*p)

        fill = WHITE
        if i == START["red"]:
            fill = COLORS["red"]
        elif i == START["green"]:
            fill = COLORS["green"]
        elif i == START["yellow"]:
            fill = COLORS["yellow"]
        elif i == START["blue"]:
            fill = COLORS["blue"]

        pygame.draw.rect(screen, fill, r, border_radius=5)
        pygame.draw.rect(screen, GRID, r, 1, border_radius=5)

        # Safe square marker/star.
        if i in SAFE and i not in START.values():
            cx, cy = r.center
            pygame.draw.polygon(
                screen,
                shade(fill, -30),
                star_points((cx, cy), CELL * 0.28, CELL * 0.12, 5)
            )

    # Home lanes.
    for color, lane in LANES.items():
        for p in lane:
            r = cell_rect(*p)
            pygame.draw.rect(screen, LIGHT[color], r, border_radius=5)
            pygame.draw.rect(screen, COLORS[color], r, 2, border_radius=5)

    # Center home triangle.
    center = cell_rect(7, 7)
    x, y, w, h = center
    pygame.draw.polygon(screen, COLORS["red"], [(x, y), (x+w, y), (x+w/2, y+h/2)])
    pygame.draw.polygon(screen, COLORS["green"], [(x+w, y), (x+w, y+h), (x+w/2, y+h/2)])
    pygame.draw.polygon(screen, COLORS["yellow"], [(x+w, y+h), (x, y+h), (x+w/2, y+h/2)])
    pygame.draw.polygon(screen, COLORS["blue"], [(x, y+h), (x, y), (x+w/2, y+h/2)])
    pygame.draw.rect(screen, DARK, center, 2)

    # Decorative outer frame.
    pygame.draw.rect(screen, DARK, br, 3, border_radius=20)


def star_points(center, outer_r, inner_r, points):
    cx, cy = center
    result = []

    for i in range(points * 2):
        angle = -math.pi / 2 + i * math.pi / points
        radius = outer_r if i % 2 == 0 else inner_r
        result.append((cx + math.cos(angle) * radius,
                       cy + math.sin(angle) * radius))

    return result


def draw_tokens():
    # Group tokens occupying the same cell so all remain visible.
    groups = {}

    for color in PLAYER_ORDER:
        for idx in range(4):
            pos = token_grid_pos(color, idx)
            groups.setdefault(pos, []).append((color, idx))

    offsets = [
        (-13, -13),
        (13, -13),
        (-13, 13),
        (13, 13),
        (0, 0),
    ]

    for pos, items in groups.items():
        for k, (color, idx) in enumerate(items):
            offset = offsets[k] if len(items) > 1 else (0, 0)
            cx, cy = cell_center(pos)
            cx += offset[0]
            cy += offset[1]

            # Highlight legal tokens.
            if (
                color == PLAYER_ORDER[current]
                and must_choose
                and dice is not None
                and idx in legal_tokens(color, dice)
            ):
                pygame.draw.circle(screen, WHITE, (cx, cy), 25)
                pygame.draw.circle(screen, COLORS[color], (cx, cy), 24, 4)

            # Token shadow.
            pygame.draw.circle(screen, (190, 188, 183), (cx + 3, cy + 4), 17)

            # Token body.
            pygame.draw.circle(screen, COLORS[color], (cx, cy), 16)
            pygame.draw.circle(screen, WHITE, (cx, cy), 16, 2)
            pygame.draw.circle(screen, shade(COLORS[color], 35), (cx - 5, cy - 5), 6)

            # Token number.
            draw_text(
                str(idx + 1),
                (cx, cy + 1),
                SMALL,
                WHITE,
                center=True
            )


def draw_dice(rect, value, enabled=True):
    # Shadow
    shadow = rect.move(4, 5)
    draw_round_rect(shadow, (215, 211, 203), 20)

    draw_round_rect(rect, WHITE, 20, DARK, 2)

    # Tiny title
    draw_text("DICE", (rect.centerx, rect.y + 17), SMALL, (100, 100, 100), True)

    pip_map = {
        1: [(0,0)],
        2: [(-1,-1),(1,1)],
        3: [(-1,-1),(0,0),(1,1)],
        4: [(-1,-1),(1,-1),(-1,1),(1,1)],
        5: [(-1,-1),(1,-1),(0,0),(-1,1),(1,1)],
        6: [(-1,-1),(-1,0),(-1,1),(1,-1),(1,0),(1,1)],
    }

    value = max(1, min(6, value))
    cx = rect.centerx
    cy = rect.centery + 10
    spacing = 25

    for px, py in pip_map[value]:
        pygame.draw.circle(screen, DARK, (cx + px * spacing, cy + py * spacing), 7)


def draw_player_card(color, idx, y):
    active = idx == current and winner is None

    rect = pygame.Rect(PANEL_X, y, 350, 62)

    fill = LIGHT[color] if active else WHITE
    outline = COLORS[color] if active else (215, 213, 208)

    draw_round_rect(rect, fill, 14, outline, 2 if active else 1)

    pygame.draw.circle(screen, COLORS[color], (rect.x + 27, rect.centery), 13)

    draw_text(
        color.capitalize(),
        (rect.x + 50, rect.y + 9),
        MEDIUM,
        COLORS[color]
    )

    finished = sum(1 for s in players[color] if s == 56)
    out = sum(1 for s in players[color] if s >= 0)

    draw_text(
        f"Tokens out: {out}/4   Home: {finished}/4",
        (rect.x + 50, rect.y + 36),
        SMALL,
        (90, 90, 90)
    )

    if active:
        pygame.draw.circle(screen, COLORS[color], (rect.right - 20, rect.centery), 6)


def draw_sidebar():
    panel = pygame.Rect(PANEL_X - 15, 45, 380, 735)

    draw_round_rect(panel, (232, 228, 219), 22)

    draw_text("GAME", (PANEL_X + 10, 65), SMALL, (115, 110, 100))
    draw_text(
        f"{PLAYER_ORDER[current].upper()}'S TURN",
        (PANEL_X + 10, 84),
        BIG,
        COLORS[PLAYER_ORDER[current]]
    )

    dice_rect = pygame.Rect(PANEL_X + 70, 145, 210, 180)
    display_value = roll_value if rolling else (dice if dice is not None else 1)
    draw_dice(dice_rect, display_value)

    button = pygame.Rect(PANEL_X + 50, 345, 250, 62)

    can_roll = (
        winner is None
        and not rolling
        and dice is None
        and no_move_timer == 0
    )

    button_fill = COLORS[PLAYER_ORDER[current]] if can_roll else (180, 178, 173)
    draw_round_rect(button, button_fill, 16)

    draw_text(
        "ROLL DICE",
        button.center,
        MEDIUM,
        WHITE,
        True
    )

    # Player cards.
    y = 440
    for idx, color in enumerate(PLAYER_ORDER):
        draw_player_card(color, idx, y)
        y += 72

    # Controls.
    draw_text("R  Restart game", (PANEL_X, 742), SMALL, (85, 82, 78))
    draw_text("ESC  Quit", (PANEL_X + 150, 742), SMALL, (85, 82, 78))


def draw_message():
    rect = pygame.Rect(BOARD_X, 780, 720, 32)
    draw_round_rect(rect, WHITE, 10, (215, 211, 204), 1)
    draw_text(message, rect.center, SMALL, DARK, True)


def draw_winner_overlay():
    if not winner:
        return

    overlay = pygame.Surface((BOARD_SIZE, BOARD_SIZE), pygame.SRCALPHA)
    overlay.fill((20, 20, 20, 120))
    screen.blit(overlay, (BOARD_X, BOARD_Y))

    card = pygame.Rect(BOARD_X + 90, BOARD_Y + 245, 540, 210)
    draw_round_rect(card, WHITE, 25, COLORS[winner], 5)

    draw_text(
        f"{winner.upper()} WINS!",
        card.centerx and (card.centerx, card.y + 60),
        TITLE,
        COLORS[winner],
        True
    )

    draw_text(
        "All four tokens reached home.",
        (card.centerx, card.y + 115),
        FONT,
        DARK,
        True
    )

    draw_text(
        "Press R to start a new game",
        (card.centerx, card.y + 160),
        SMALL,
        (95, 95, 95),
        True
    )


# ------------------------- Game logic ------------------------

def start_roll():
    global rolling, roll_frames, roll_value

    if winner or rolling or dice is not None or no_move_timer > 0:
        return

    rolling = True
    roll_frames = 0
    roll_value = random.randint(1, 6)


def finish_roll():
    global rolling, dice, must_choose, message, no_move_timer

    rolling = False
    dice = random.randint(1, 6)

    color = PLAYER_ORDER[current]
    legal = legal_tokens(color, dice)

    if not legal:
        must_choose = False
        message = (
            f"{color.capitalize()} rolled {dice}. "
            "No legal move — next player's turn."
        )
        no_move_timer = pygame.time.get_ticks() + 850
        return

    must_choose = True

    # Auto-move if there is only one possible token.
    if len(legal) == 1:
        finish_move(color, legal[0], dice)


def token_at_mouse(mx, my):
    if not must_choose or dice is None or winner:
        return None

    color = PLAYER_ORDER[current]
    legal = legal_tokens(color, dice)

    for idx in legal:
        cx, cy = token_pixel_pos(color, idx)
        if math.hypot(mx - cx, my - cy) <= 24:
            return idx

    return None


def roll_button_rect():
    return pygame.Rect(PANEL_X + 50, 345, 250, 62)


# ---------------------------- Main ----------------------------

reset_game()

while True:
    now = pygame.time.get_ticks()

    if rolling:
        roll_frames += 1

        if roll_frames % 4 == 0:
            roll_value = random.randint(1, 6)

        if roll_frames >= 32:
            finish_roll()

    if no_move_timer and now >= no_move_timer:
        no_move_timer = 0
        next_turn()

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                pygame.quit()
                sys.exit()

            if event.key == pygame.K_r:
                reset_game()

            if event.key == pygame.K_SPACE:
                start_roll()

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = event.pos

            if roll_button_rect().collidepoint(mx, my):
                start_roll()
            else:
                idx = token_at_mouse(mx, my)
                if idx is not None:
                    color = PLAYER_ORDER[current]
                    finish_move(color, idx, dice)

    # ------------------------- Render -------------------------
    draw_background()
    draw_board_cells()
    draw_tokens()
    draw_sidebar()
    draw_message()
    draw_winner_overlay()

    pygame.display.flip()
    clock.tick(60)
