import struct

MID_CONFIGURE = 1
MID_SCREENSHOT = 11
MID_GET_STATE = 12
MID_GET_BEST_SCORE = 13
MID_GET_MY_SCORE = 23
MID_GET_CURRENT_LEVEL = 14
MID_CART_SHOOT_SAFE = 31
MID_CART_SHOOT_FAST = 41
MID_POLAR_SHOOT_SAFE = 32
MID_POLAR_SHOOT_FAST = 42
MID_SEQ_SHOTS_SAFE = 33
MID_SEQ_SHOTS_FAST = 43
MID_FULL_ZOOM_OUT = 34
MID_FULL_ZOOM_IN = 35
MID_CLICK_IN_CENTER = 36
MID_LOAD_LEVEL = 51
MID_RESTART_LEVEL = 52

LEN_CONFIGURE = 3               # Round Info = 1, Time Limit = 1, Available Levels = 1
LEN_SCREENSHOT = 4 + 4          # Width = 4, Height = 4
LEN_GET_STATE = 1
LEN_GET_SCORE = 21 * 4       # Score for each Level = 4, 21 Levels
LEN_GET_CURRENT_LEVEL = 1       # Current Level = 1
LEN_ETC = 1                     # OK/ERR

STATE_UNKNOWN = 0
STATE_MAIN_MENU = 1
STATE_EPISODE_MENU = 2
STATE_LEVEL_SELECTION = 3
STATE_LOADING = 4
STATE_PLAYING = 5
STATE_WON = 6
STATE_LOST = 7

def configure(team_id):
    return struct.pack('!bi', MID_CONFIGURE, team_id)

def recv_configure(result):
    round_info, time_limit, available_levels = struct.unpack('!bbb', result)
    if round_info == 0:
        raise ValueError('Configuration Failed')
    return available_levels

def get_screenshot():
    return struct.pack('!b', MID_SCREENSHOT)

def recv_screenshot_size(result):
    width, height = struct.unpack('!ii', result)
    print('width = {}, height = {}'.format(width, height))
    return width * height * 3           # with * height RGB tuples

def recv_screenshot(result):
    screenshot = []
    for red, green, blue in struct.iter_unpack('!bbb', result):
        screenshot.append([red, green, blue])
    return screenshot

def get_state():
    return struct.pack('!b', MID_GET_STATE)

def recv_state(result):
    return struct.unpack('!b', result)

def get_best_score():
    return struct.pack('!b', MID_GET_BEST_SCORE)

def get_my_score():
    return struct.pack('!b', MID_GET_MY_SCORE)

def recv_score(result):
    score_list = []
    for score in struct.iter_unpack('!b', result):
        score_list.append(score)
    return score_list

def get_current_level():
    return struct.pack('!b', MID_GET_CURRENT_LEVEL)

def recv_current_level(result):
    level = struct.unpack('!b', result)
    if level < 0 or level > 21:
        raise ValueError('Received current level = ' + level)
    return level

def cart_shoot(fx, fy, dx, dy, t1, t2, mode='safe'):
    if mode == 'safe':
        mid = MID_CART_SHOOT_SAFE
    elif mode == 'fast':
        mid = MID_CART_SHOOT_FAST
    else:
        raise ValueError('cart_shoot mode = ' + mode)
    return struct.pack('!biiiiii', mid, fx, fy, dx, dy, t1, t2)

def polar_shoot(fx, fy, theta, r, t1, t2, mode='safe'):
    if mode == 'safe':
        mid = MID_POLAR_SHOOT_SAFE
    elif mode == 'fast':
        mid = MID_POLAR_SHOOT_FAST
    else:
        raise ValueError('polar_shoot mode = ' + mode)
    return struct.pack('!biiiiii', mid, fx, fy, theta, r, t1, t2)

def zoom_out():
    return struct.pack('!b', MID_FULL_ZOOM_OUT)

def zoom_in():
    return struct.pack('!b', MID_FULL_ZOOM_IN)

def click_in_center():
    return struct.pack('!b', MID_CLICK_IN_CENTER)

def load_level(level):
    return struct.pack('!bb', MID_LOAD_LEVEL, level)

def restart_level():
    return struct.pack('!b', MID_RESTART_LEVEL)

def recv_result(result):
    return struct.unpack('!b', result)

