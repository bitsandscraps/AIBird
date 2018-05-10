"""AIBird Client module"""
import socket
import numpy as np
import message

TIMEOUT = 30         # Timeout value for the socket
MAXTRIALS = 5       # Max number of zoom tries

FOCUS = [
    (194, 326),     # Level 1
    (208, 312),     # Level 2
    (170, 336),     # Level 3
    (194, 330),     # Level 4
    (188, 335),     # Level 5
    (184, 333),     # Level 6
    (171, 335),     # Level 7
    (184, 333),     # Level 8
    (174, 319),     # Level 9
    (175, 324),     # Level 10
    (172, 333),     # Level 11
    (164, 338),     # Level 12
    (165, 336),     # Level 13
    (171, 290),     # Level 14
    (154, 338),     # Level 15
    (156, 320),     # Level 16
    (175, 333),     # Level 17
    (171, 330),     # Level 18
    (162, 337),     # Level 19
    (177, 328),     # Level 20
    (177, 303)      # Level 21
]

class AIBirdClient:
    """Handles communication with the AIBird Server

    Attributes
        host (str): address of AIBird Server. Default is `localhost`
        port (int): port of AIBird Server. Default is `2004`
        team_id(int): team ID. Default is `1`

    Usage:
        client = AIBirdClient()
        client.connect()
        # Do whatever you want to do.
        img = client.screenshot()
        shoot = process_screenshot(img)     # A user defined function
        client.polar_shoot(*shoot)
    """
    def __init__(self, host='localhost', port=2004, team_id=1):
        self.host = host
        self.port = port
        self.team_id = team_id
        self.socket = None
        self.level = None
        self.current_level = 1

    def connect(self):
        """Connect to AIBird server."""
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.settimeout(TIMEOUT)
        self.socket.connect((self.host, self.port))
        self.load_level(self.current_level)

    def screenshot(self):
        """Get screenshot

        Return a numpy array containing the screenshot"""
        self.socket.sendall(message.get_screenshot())
        size, width, height = message.recv_screenshot_size(
            self.socket.recv(message.LEN_SCREENSHOT))
        img_data = []
        for _ in range(size):
            pixel = self.socket.recv(message.LEN_PIXEL)
            img_data.append(message.recv_pixel(pixel))
        img = np.asarray(img_data, dtype=np.uint8)
        img.resize(height, width, 3)
        return img

    def state(self):
        """Get current state

        Return a GameState object.
        """
        self.socket.sendall(message.get_state())
        return message.recv_state(self.socket.recv(message.LEN_GET_STATE))

    def my_score(self):
        """Get my score for level `level`

        If level is not specified, returns the list of length 21, containing the scores
        for each level.
        """
        self.socket.sendall(message.get_my_score())
        return message.recv_score(self.socket.recv(message.LEN_GET_SCORE))

    def send_and_recv_result(self, msg):
        """Send msg and parse its result.

        Return True if succeeded, False otherwise.
        """
        self.socket.sendall(msg)
        return message.recv_result(self.socket.recv(message.LEN_ETC))

    def cart_shoot(self, dx, dy, t1, t2, mode='safe'):
        """Send cart_shoot request.

        It assumes that the screen is fully zoomed out.

        Args
            dx, dy -- relative x, y coordinate of release point
            t1 -- release time
            t2 -- gap between release time and tap time

        Return True if accepted, False if rejected.
        """
        level = self.current_level
        fx, fy = FOCUS[level - 1]
        for _ in range(MAXTRIALS):
            if self.zoom_out():
                break
        else:
            raise Exception('cart_shoot: reached MAXTRIALS')

        return self.send_and_recv_result(
            message.cart_shoot(fx, fy, dx, dy, t1, t2, mode))

    def polar_shoot(self, r, theta, t1, t2, mode='safe'):
        """Send cart_shoot request.

        It assumes that the screen is fully zoomed out.

        Args
            r -- the radial coordinate
            theta -- the angular coordinate by degree from -90.00 to 90.00.
            t1 -- release time
            t2 -- gap between release time and tap time

        Return True if accepted, False if rejected.
        """
        level = self.current_level
        fx, fy = FOCUS[level - 1]
        for _ in range(MAXTRIALS):
            if self.zoom_out():
                break
        else:
            raise Exception('cart_shoot: reached MAXTRIALS')
        return self.send_and_recv_result(
            message.polar_shoot(fx, fy, r, theta, t1, t2, mode))

    def zoom_in(self):
        """Send zoom in request.
        Return True if succeeded, False otherwise.
        """
        return self.send_and_recv_result(message.zoom_in())

    def zoom_out(self):
        """Send zoom out request.
        Return True if succeeded, False otherwise.
        """
        return self.send_and_recv_result(message.zoom_out())

    def click_in_center(self):
        """Send click in center request.
        Return True if succeeded, False otherwise.
        """
        return self.send_and_recv_result(message.click_in_center())

    def load_level(self, level):
        """Send load level `level` request.
        Return True if succeeded, False otherwise.
        """
        result = self.send_and_recv_result(message.load_level(level))
        if result:
            self.current_level = level
        return result

    def restart_level(self):
        """Send restart level request.
        Return True if succeeded, False otherwise.
        """
        return self.send_and_recv_result(message.restart_level())
