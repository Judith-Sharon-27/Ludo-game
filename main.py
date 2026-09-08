import pygame
import random
import sys

pygame.init()
WIDTH, HEIGHT = 900, 760
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Ludo - Python Edition")
clock = pygame.time.Clock()

FONT = pygame.font.SysFont("arial", 22)
BIG = pygame.font.SysFont("arial", 34, bold=True)
SMALL = pygame.font.SysFont("arial", 17)

COLORS = {
    "red": (220, 55, 55),
    "green": (45, 170, 85),
    "yellow": (235, 190, 40),
    "blue": (55, 105, 210),
    "white": (248, 248, 248),
    "black": (30, 30, 30),
    "gray": (215, 215, 215),
    "darkgray": (110, 110, 110),
}

PLAYER_ORDER = ["red", "green", "yellow", "blue"]

# 52-square common track, represented clockwise around a 15x15 board.
TRACK = [
    (6,0),(7,0),(8,0),(8,1),(8,2),(9,2),(10,2),(11,2),(12,2),(12,3),
    (12,4),(12,5),(13,6),(14,6),(14,7),(14,8),(13,8),(12,9),(12,10),
    (12,11),(12,12),(11,12),(10,12),(9,12),(8,12),(8,13),(8,14),(7,14),
    (6,14),(6,13),(6,12),(5,12),(4,12),(3,12),(2,12),(2,11),(2,10),
    (2,9),(1,8),(0,8),(0,7),(0,6),(1,6),(2,5),(2,4),(2,3),(3,2),
    (4,2),(5,2),(6,2),(6,1)
]

# Entry index for each player on the shared track.
START = {"red": 0, "green": 13, "yellow": 26, "blue": 39}
HOME_ENTRY = {"red": 51, "green": 12, "yellow": 25, "blue": 38}

# Five safe squares: four starting squares + center-adjacent star.
SAFE = set(START.values()) | {8, 21, 34, 47}

# Home-lane coordinates, 5 spaces each, from track toward center.
LANES = {
    "red": [(7,1),(7,2),(7,3),(7,4),(7,5)],
    "green": [(13,7),(12,7),(11,7),(10,7),(9,7)],
    "yellow": [(7,13),(7,12),(7,11),(7,10),(7,9)],
    "blue": [(1,7),(2,7),(3,7),(4,7),(5,7)],
}
CENTER = (7, 7)

YARD = {
    "red": [(2,2),(4,2),(2,4),(4,4)],
    "green": [(10,2),(12,2),(10,4),(12,4)],
    "yellow": [(10,10),(12,10),(10,12),(12,12)],
    "blue": [(2,10),(4,10),(2,12),(4,12)],
}

# Each token state:
# -1 = yard
# 0..51 = shared track index
# 52..56 = home lane positions (56 means finished)
# A token can move from 52..56; 56 is finished.
players = {
    "red":   [-1,-1,-1,-1],
    "green": [-1,-1,-1,-1],
    "yellow": [-1,-1,-1,-1],
    "blue":  [-1,-1,-1,-1],
}
current = 0
dice = None
message = "Red's turn. Roll the dice!"
winner = None
must_choose = False

def board_to_screen(col, row):
    left, top = 55, 35
    cell = 45
    return left + col * cell, top + row * cell

def draw_text(text, x, y, font=FONT, color=COLORS["black"], center=False):
    surf = font.render(text, True, color)
    rect = surf.get_rect()
    if center:
        rect.center = (x, y)
    else:
        rect.topleft = (x, y)
    screen.blit(surf, rect)

def circle_at_grid(pos, radius, color, outline=COLORS["black"]):
    x, y = board_to_screen(*pos)
    pygame.draw.circle(screen, color, (x+22, y+22), radius)
    pygame.draw.circle(screen, outline, (x+22, y+22), radius, 2)

def track_pos(index):
    return TRACK[index % 52]

def absolute_distance(color, state):
    """Convert a token state to distance from its player's start."""
    if state < 0:
        return None
    if state <= 51:
        return (state - START[color]) % 52
    return 52 + (state - 52)

def token_screen_pos(color, idx):
    state = players[color][idx]
    if state == -1:
        return board_to_screen(*YARD[color][idx])
    if state <= 51:
        return board_to_screen(*track_pos(state))
    if state <= 56:
        if state == 56:
            return board_to_screen(CENTER)
        return board_to_screen(*LANES[color][state-52])
    return board_to_screen(CENTER)

def legal_tokens(color, roll):
    out = []
    for i, state in enumerate(players[color]):
        if state == 56:
            continue
        if state == -1:
            if roll == 6:
                out.append(i)
        else:
            distance = absolute_distance(color, state)
            if distance is not None and distance + roll <= 56:
                out.append(i)
    return out

def move_token(color, idx, roll):
    state = players[color][idx]
    if state == -1:
        # Enter directly onto starting square.
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
    if state < 0 or state > 51:
        return 0
    if state in SAFE:
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
    global current, dice, message, winner, must_choose
    for c in PLAYER_ORDER:
        players[c] = [-1,-1,-1,-1]
    current = 0
    dice = None
    winner = None
    must_choose = False
    message = "Red's turn. Roll the dice!"

def next_turn(extra=False):
    global current, dice, message, must_choose
    dice = None
    must_choose = False
    if not extra:
        current = (current + 1) % 4
    message = f"{PLAYER_ORDER[current].capitalize()}'s turn. Roll the dice!"

def draw_board():
    screen.fill((238,238,238))
    left, top = 55, 35
    cell = 45

    # Board background.
    pygame.draw.rect(screen, COLORS["white"], (left, top, 15*cell, 15*cell))
    pygame.draw.rect(screen, COLORS["black"], (left, top, 15*cell, 15*cell), 3)

    # Colored home bases.
    bases = {
        "red": (0,0,6,6),
        "green": (9,0,6,6),
        "yellow": (9,9,6,6),
        "blue": (0,9,6,6),
    }
    for c,(bx,by,bw,bh) in bases.items():
        pygame.draw.rect(screen, COLORS[c], (left+bx*cell, top+by*cell, bw*cell, bh*cell))
        pygame.draw.rect(screen, COLORS["black"], (left+bx*cell, top+by*cell, bw*cell, bh*cell), 2)
        # Inner yard.
        pygame.draw.rect(screen, COLORS["white"], (left+(bx+1)*cell, top+(by+1)*cell, 4*cell, 4*cell))
        for p in YARD[c]:
            circle_at_grid(p, 15, COLORS[c])

    # Track.
    for i, p in enumerate(TRACK):
        color = COLORS["white"]
        if i == START["red"]: color = COLORS["red"]
        elif i == START["green"]: color = COLORS["green"]
        elif i == START["yellow"]: color = COLORS["yellow"]
        elif i == START["blue"]: color = COLORS["blue"]
        circle_at_grid(p, 18, color)

    # Home lanes.
    for c, lane in LANES.items():
        for p in lane:
            circle_at_grid(p, 18, COLORS[c])

    # Center finish.
    x,y = board_to_screen(*CENTER)
    pygame.draw.polygon(screen, COLORS["red"], [(x+22,y),(x+44,y+44),(x+22,y+44)])
    pygame.draw.polygon(screen, COLORS["green"], [(x+22,y),(x+44,y),(x+22,y+44)])
    pygame.draw.polygon(screen, COLORS["yellow"], [(x+22,y),(x,y+44),(x+22,y+44)])
    pygame.draw.polygon(screen, COLORS["blue"], [(x+22,y),(x,y),(x+22,y+44)])

def draw_tokens():
    # Offset overlapping tokens so all are clickable/visible.
    for c in PLAYER_ORDER:
        groups = {}
        for i, state in enumerate(players[c]):
            pos = token_screen_pos(c, i)
            groups.setdefault(pos, []).append(i)
        for pos, ids in groups.items():
            x,y = board_to_screen(*pos)
            for k,i in enumerate(ids):
                ox = (-7,7,-7,7)[k % 4]
                oy = (-7,-7,7,7)[k % 4]
                pygame.draw.circle(screen, COLORS[c], (x+22+ox, y+22+oy), 13)
                pygame.draw.circle(screen, COLORS["black"], (x+22+ox, y+22+oy), 13, 2)
                draw_text(str(i+1), x+22+ox, y+22+oy, SMALL, COLORS["white"], True)

def draw_sidebar():
    x = 750
    draw_text("LUDO", x, 55, BIG, COLORS["black"], True)
    draw_text(f"Turn: {PLAYER_ORDER[current].upper()}", x, 105, FONT, COLORS[PLAYER_ORDER[current]], True)

    # Dice
    pygame.draw.rect(screen, COLORS["white"], (690,140,120,120), border_radius=12)
    pygame.draw.rect(screen, COLORS["black"], (690,140,120,120), 2, border_radius=12)
    draw_text("ROLL", 750, 155, SMALL, COLORS["darkgray"], True)
    draw_text("—" if dice is None else str(dice), 750, 205, BIG, COLORS["black"], True)

    pygame.draw.rect(screen, COLORS["white"], (665,280,170,60), border_radius=10)
    pygame.draw.rect(screen, COLORS["black"], (665,280,170,60), 2, border_radius=10)
    draw_text("Roll Dice", 750, 310, FONT, COLORS["black"], True)

    draw_text("Rules", 675, 380, FONT, COLORS["black"])
    rules = [
        "• Roll 6 to leave yard",
        "• Reach the center",
        "• Exact roll required",
        "• Safe squares cannot",
        "  be captured",
        "• Roll 6 = extra turn",
        "• Capture = extra turn",
    ]
    yy = 415
    for line in rules:
        draw_text(line, 675, yy, SMALL)
        yy += 24

    draw_text("R Restart", 675, 610, SMALL)
    draw_text("Esc Quit", 675, 635, SMALL)

    # Message box
    pygame.draw.rect(screen, COLORS["white"], (55,715,780,35), border_radius=8)
    pygame.draw.rect(screen, COLORS["black"], (55,715,780,35), 1, border_radius=8)
    draw_text(message, 70, 723, SMALL)

def roll_dice():
    global dice, message, must_choose
    if dice is not None or winner:
        return
    dice = random.randint(1,6)
    color = PLAYER_ORDER[current]
    legal = legal_tokens(color, dice)
    if not legal:
        message = f"{color.capitalize()} rolled {dice}; no legal move."
        pygame.time.set_timer(pygame.USEREVENT, 800, loops=1)
        return
    must_choose = True
    if len(legal) == 1:
        move_token(color, legal[0], dice)
        captured = capture_if_possible(color, legal[0])
        if has_won(color):
            globals()["winner"] = color
            message = f"{color.capitalize()} wins! Press R to restart."
            return
        extra = dice == 6 or captured > 0
        if extra:
            message = f"{color.capitalize()} gets another turn. Roll again!"
            dice = None
            must_choose = False
        else:
            next_turn()

def handle_token_click(mx, my):
    global message, must_choose, winner
    if not must_choose or winner or dice is None:
        return
    color = PLAYER_ORDER[current]
    legal = legal_tokens(color, dice)
    for i in legal:
        x,y = token_screen_pos(color, i)
        rect = pygame.Rect(x+5,y+5,35,35)
        if rect.collidepoint(mx,my):
            move_token(color, i, dice)
            captured = capture_if_possible(color, i)
            if has_won(color):
                winner = color
                message = f"{color.capitalize()} wins! Press R to restart."
                return
            extra = dice == 6 or captured > 0
            if extra:
                dice = None
                must_choose = False
                message = f"{color.capitalize()} gets another turn. Roll again!"
            else:
                next_turn()
            return
    message = "Click one of the highlighted legal tokens."

# Main loop
while True:
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

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx,my = event.pos
            if 665 <= mx <= 835 and 280 <= my <= 340:
                roll_dice()
            else:
                handle_token_click(mx,my)

        if event.type == pygame.USEREVENT:
            color = PLAYER_ORDER[current]
            # If no legal move, turn changes after short delay.
            next_turn()

    draw_board()
    draw_tokens()
    draw_sidebar()

    # Highlight legal tokens.
    if must_choose and dice is not None:
        color = PLAYER_ORDER[current]
        for i in legal_tokens(color, dice):
            x,y = token_screen_pos(color, i)
            pygame.draw.circle(screen, COLORS["black"], (x+22,y+22), 20, 3)

    if winner:
        overlay = pygame.Surface((620,180), pygame.SRCALPHA)
        overlay.fill((255,255,255,235))
        screen.blit(overlay, (80,250))
        draw_text(f"{winner.upper()} WINS!", 390, 300, BIG, COLORS[winner], True)
        draw_text("Press R to start a new game", 390, 350, FONT, COLORS["black"], True)

    pygame.display.flip()
    clock.tick(60)
