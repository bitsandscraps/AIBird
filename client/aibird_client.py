"""AIBird Client module"""
import base64
import io
import socket

import numpy as np
from PIL import Image

import aibird_message

TIMEOUT = 60         # Timeout value for the socket
MAXTRIALS = 5       # Max number of zoom tries
DOWNSCALEFACTOR = 2

# FOCUS = [
#     (194, 326),     # Level 1
#     (208, 312),     # Level 2
#     (170, 336),     # Level 3
#     (194, 330),     # Level 4
#     (188, 335),     # Level 5
#     (184, 333),     # Level 6
#     (171, 335),     # Level 7
#     (184, 333),     # Level 8
#     (174, 319),     # Level 9
#     (175, 324),     # Level 10
#     (172, 333),     # Level 11
#     (164, 338),     # Level 12
#     (165, 336),     # Level 13
#     (171, 290),     # Level 14
#     (154, 338),     # Level 15
#     (156, 320),     # Level 16
#     (175, 333),     # Level 17
#     (171, 330),     # Level 18
#     (162, 337),     # Level 19
#     (177, 328),     # Level 20
#     (177, 303)      # Level 21
# ]

class AIBirdClient:
    """Handles communication with the AIBird Server

    Attributes
        host (str): address of AIBird Server. Default is `localhost`
        port (int): port of AIBird Server. Default is `2004`

    Usage:
        client = AIBirdClient()
        client.connect()
        # Do whatever you want to do.
        img = client.screenshot
        shoot = process_screenshot(img)     # A user defined function
        client.polar_shoot(*shoot)
    """
    def __init__(self, host='localhost', port=2004):
        self.host = host
        self.port = port
        self.socket = None
        self._scores = [0] * 21
        self._current_level = 1

    def connect(self):
        """Connect to AIBird server."""
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.settimeout(TIMEOUT)
        self.socket.connect((self.host, self.port))
        self._load_level(self._current_level)

    def disconnect(self):
        """Disconnect from AIBird server."""
        self.socket.close()

    @property
    def current_level(self):
        """ Return current level """
        return self._current_level

    @current_level.setter
    def current_level(self, level):
        if level > 21 and level < 0:
            print("Level must be between 0 and 21. Received {}.".format(level))
        else:
            if self._load_level(level):
                self._current_level = level
            else:
                print("Failed to load level {}".format(level))

    @property
    def total_score(self):
        """ Sum of the scores for each level(there are 21 of them) """
        return sum(self._scores)

    @property
    def current_score(self):
        """ Score of the current level """
        score = self._get_score()
        self._scores[self._current_level - 1] = score
        return score

    @property
    def screenshot(self):
        """ A numpy array containing the screenshot"""
        self.socket.sendall(aibird_message.get_screenshot())
        size = aibird_message.recv_screenshot_size(
            self.socket.recv(aibird_message.LEN_SCREENSHOT))
        # print(size, width, height)
        data = b''
        while len(data) < size:
            packet = self.socket.recv(size - len(data))
            data += packet
        img = np.array(Image.open(io.BytesIO(base64.b64decode(data))))
        return img
        #return rescale(img, 1/DOWNSCALEFACTOR)  # The blue bird is almost invisible.

    @property
    def state(self):
        """Get current state

        Return a GameState object.
        """
        self.socket.sendall(aibird_message.get_state())
        return aibird_message.recv_state(self.socket.recv(aibird_message.LEN_GET_STATE))

    @property
    def is_level_over(self):
        """Send is level over query.
        Return True if level is over. False otherwise
        """
        return self._send_and_recv_result(aibird_message.get_is_level_over())

    def _get_score(self):
        """Request the server for my score"""
        self.socket.sendall(aibird_message.get_my_score())
        return aibird_message.recv_score(self.socket.recv(aibird_message.LEN_GET_SCORE))

    def _get_cached_score(self):
        return self._scores[self._current_level - 1]

    def _send_and_recv_result(self, msg):
        """Send msg and parse its result.

        Return True if succeeded, False otherwise.
        """
        self.socket.sendall(msg)
        return aibird_message.recv_result(self.socket.recv(aibird_message.LEN_ETC))

    def cart_shoot(self, dx, dy, tap_time, mode='safe'):
        """Send cart_shoot request.

        It assumes that the screen is fully zoomed out.

        Args
            dx, dy -- relative x, y coordinate of release point
            tap_time -- in seconds

        Return True if accepted, False if rejected.
        """
        # level = self.current_level
        # fx, fy = FOCUS[level - 1]
        for _ in range(MAXTRIALS):
            if self.zoom_out():
                break
        else:
            raise Exception('cart_shoot: reached MAXTRIALS')

        result = self._send_and_recv_result(
            aibird_message.cart_shoot(dx, dy, tap_time, mode))
        if result:
            initial_score = self._get_cached_score()
            return self.current_score - initial_score
        return -1

    def polar_shoot(self, theta, tap_time, mode='safe'):
        """Send cart_shoot request.

        It assumes that the screen is fully zoomed out.

        Args
            theta -- the angular coordinate by degree from -90.00 to 90.00.
            tap_time -- in seconds

        Return True if accepted, False if rejected.
        """
        # level = self.current_level
        # fx, fy = FOCUS[level - 1]
        for _ in range(MAXTRIALS):
            if self.zoom_out():
                break
        else:
            raise Exception('cart_shoot: reached MAXTRIALS')
        result = self._send_and_recv_result(
            aibird_message.polar_shoot(50, theta, tap_time, mode)) # always shoot max
        if result:
            initial_score = self._get_cached_score()
            return self.current_score - initial_score
        return -1

    def zoom_in(self):
        """Send zoom in request.
        Return True if succeeded, False otherwise.
        """
        return self._send_and_recv_result(aibird_message.zoom_in())

    def zoom_out(self):
        """Send zoom out request.
        Return True if succeeded, False otherwise.
        """
        return self._send_and_recv_result(aibird_message.zoom_out())

    def click_in_center(self):
        """Send click in center request.
        Return True if succeeded, False otherwise.
        """
        return self._send_and_recv_result(aibird_message.click_in_center())

    def next_level(self):
        """ Load next level.
        Return False if current level is 21, True otherwie.
        """
        if self.current_level < 21:
            self.current_level = self.current_level + 1
            return True
        return False


    def _load_level(self, level):
        """Send load level `level` request.
        Return True if succeeded, False otherwise.
        """
        result = self._send_and_recv_result(aibird_message.load_level(level))
        if result:
            self._current_level = level
        return result

    def restart_level(self):
        """Send restart level request.
        Return True if succeeded, False otherwise.
        """
        return self._send_and_recv_result(aibird_message.restart_level())
