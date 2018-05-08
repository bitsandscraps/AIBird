"""Module that handles AIBird server client communication protocol

Example:
    send(get_screenshot())          # Sends a screenshot request message
    result = recv(LEN_SCREENSHOT)   # Receives the response
    size, width, height = recv_screenshot_size(result)
    screenshot_raw = recv(size)
    screenshot = recv_screenshot(screenshot_raw, width, height)
"""
import struct

# Message IDs
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

# Length of response messages
LEN_CONFIGURE = 3       # Round Info = 1, Time Limit = 1, Available Levels = 1
LEN_SCREENSHOT = 4 + 4          # Width = 4, Height = 4
LEN_PIXEL = 3                   # RGB
LEN_GET_STATE = 1
LEN_GET_SCORE = 21 * 4          # Score for each Level = 4, 21 Levels
LEN_GET_CURRENT_LEVEL = 1       # Current Level = 1
LEN_ETC = 1                     # OK/ERR



class GameState:
    """ Data structure representing the game state.

    Args
        state -- an integer value between 0 and 7
    """
    # Response of a current state request message
    STATE_UNKNOWN = 0
    STATE_MAIN_MENU = 1
    STATE_EPISODE_MENU = 2
    STATE_LEVEL_SELECTION = 3
    STATE_LOADING = 4
    STATE_PLAYING = 5
    STATE_WON = 6
    STATE_LOST = 7

    STATE_STR = {
        STATE_UNKNOWN: 'unknown',
        STATE_MAIN_MENU: 'main menu',
        STATE_EPISODE_MENU: 'episode menu',
        STATE_LEVEL_SELECTION: 'level selection',
        STATE_LOADING: 'loading',
        STATE_PLAYING: 'playing',
        STATE_WON: 'won',
        STATE_LOST: 'lost'
    }

    def __init__(self, state):
        if state < self.STATE_UNKNOWN or state > self.STATE_LOST:
            raise ValueError('No state corresponding to {}'.format(state))
        self.state = state

    def __str__(self):
        return self.STATE_STR[self.state]

    def isover(self):
        """ Return true if the level is over. Return false otherwise. """
        return self.state == self.STATE_WON or self.state == self.STATE_LOST

    def won(self):
        """ Return true if won. Return false otherwise. """
        return self.state == self.STATE_WON


def configure(team_id):
    """Formulate a configure message"""
    return struct.pack('!bi', MID_CONFIGURE, team_id)

def recv_configure(result):
    """Parse the response of a configure message"""
    round_info, _, available_levels = struct.unpack('!bbb', result)
    if round_info == 0:
        raise ValueError('Configuration Failed')
    return available_levels

def get_screenshot():
    """Formulate a screenshot request message"""
    return struct.pack('!b', MID_SCREENSHOT)

def recv_screenshot_size(result):
    """Parse the received size information.

    Arguments
    result -- received data

    returns the tuple (number of pixels, width, height)
    """
    width, height = struct.unpack('!ii', result)
    return width * height, width, height        # with * height RGB tuples

def recv_pixel(result):
    """Parse the stream into an image

    Arguments
    result -- received data(r, g, b tuple in network order)

    returns a (r, g, b) tuple
    """
    red, green, blue = struct.unpack('!bbb', result)
    return red, green, blue

def get_state():
    """Formulate a message requesting the current state"""
    return struct.pack('!b', MID_GET_STATE)

def recv_state(result):
    """Parse the response of a state request message

    Return a GameState object corresponding to the current state.
    """
    return GameState(struct.unpack('!b', result)[0])

def get_best_score():
    """Formulate a message requesting the best score"""
    return struct.pack('!b', MID_GET_BEST_SCORE)

def get_my_score():
    """Formulate a message requesting my score"""
    return struct.pack('!b', MID_GET_MY_SCORE)

def recv_score(result):
    """Parse a response of a score request message.

    Returns a list of length 21, where i-th element is the i-th level score.
    """
    score_list = []
    for score in struct.iter_unpack('!i', result):
        score_list.append(score[0])
    return score_list

def get_current_level():
    """Formulate a message requesting the current level information"""
    return struct.pack('!b', MID_GET_CURRENT_LEVEL)

def recv_current_level(result):
    """Parse a response of a current level request message

    Returns an integer representing the current level.
    """
    level = struct.unpack('!b', result)[0]
    if level < 0 or level > 21:
        raise ValueError('Received current level = {}'.format(level))
    return level

def cart_shoot(fx, fy, dx, dy, t1, t2, mode='safe'):
    """Formulate a Cartesian shoot request message.

    Keyword Arg
    mode -- 'safe' and 'fast'
    """
    if mode == 'safe':
        mid = MID_CART_SHOOT_SAFE
    elif mode == 'fast':
        mid = MID_CART_SHOOT_FAST
    else:
        raise ValueError('cart_shoot mode = {}'.format(mode))
    return struct.pack('!biiiiii', mid, fx, fy, dx, dy, t1, t2)

def polar_shoot(fx, fy, r, theta, t1, t2, mode='safe'):
    """Formulate a polar shoot request message.

    Keyword Arg
    mode -- 'safe' and 'fast'
    """
    if mode == 'safe':
        mid = MID_POLAR_SHOOT_SAFE
    elif mode == 'fast':
        mid = MID_POLAR_SHOOT_FAST
    else:
        raise ValueError('polar_shoot mode = {}'.format(mode))
    return struct.pack('!biiiiii', mid, fx, fy, theta, r, t1, t2)

def zoom_out():
    """Formulate a zoom out request message"""
    return struct.pack('!b', MID_FULL_ZOOM_OUT)

def zoom_in():
    """Formulate a zoom in request message"""
    return struct.pack('!b', MID_FULL_ZOOM_IN)

def click_in_center():
    """Formulate a click in center request message"""
    return struct.pack('!b', MID_CLICK_IN_CENTER)

def load_level(level):
    """Formulate a load level request message.

    level -- integer representing the level to load
    """
    return struct.pack('!bb', MID_LOAD_LEVEL, level)

def restart_level():
    """Formulate a restart level request message"""
    return struct.pack('!b', MID_RESTART_LEVEL)

def recv_result(result):
    """Parse a response of the following request messages

    Available request messages:
    cart_shoot, polar_shoot, zoom_out, zoom_in, click_in_center,
    load_level, restart_level

    Return True when succeeded, False otherwise
    """
    res = struct.unpack('!b', result)[0]
    if res == 1:
        return True
    elif res == 0:
        return False
    else:
        raise ValueError('recv_result received: {}'.format(res[0]))
