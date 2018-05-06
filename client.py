"""AIBird Client module"""
import socket
import message

TIMEOUT = 5         # Timeout value for the socket

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

    def connect(self):
        """Connect to AIBird server."""
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.settimeout(TIMEOUT)
        self.socket.connect((self.host, self.port))
        self.socket.sendall(message.configure(self.team_id))
        data = self.socket.recv(message.LEN_CONFIGURE)
        message.recv_configure(data)

    def screenshot(self):
        """Get screenshot

        Return a numpy array containing the screenshot"""
        self.socket.sendall(message.get_screenshot())
        size = message.recv_screenshot_size(
                self.socket.recv(message.LEN_SCREENSHOT))
        return message.recv_screenshot(self.socket.recv(size))

    def my_score(self):
        """Get my score

        Return a list of lenth 21 where each slot indicates a best score of
        the corresponding level.
        """
        self.socket.sendall(message.get_my_score())
        return message.recv_score(self.socket.recv(message.LEN_GET_SCORE))

    def current_level(self):
        """Get current level"""
        self.socket.sendall(message.get_current_level())
        return message.recv_current_level(
                self.socket.recv(message.LEN_GET_CURRENT_LEVEL))

    def send_and_recv_result(self, msg):
        """Send msg and parse its result.

        Return True if succeeded, False otherwise.
        """
        self.socket.sendall(msg)
        return message.recv_result(self.socket.recv(message.LEN_ETC))

    def cart_shoot(self, fx, fy, dx, dy, t1, t2, mode='safe'):
        """Send cart_shoot request.

        Args
            fx, fy -- x, y coordinate of slingshot
            dx, dy -- relative x, y coordinate of release point w.r.t (fx,fy)
            t1 -- release time
            t2 -- gap between release time and tap time

        Return True if accepted, False if rejected.
        """
        return self.send_and_recv_result(
                message.cart_shoot(fx, fy, dx, dy, t1, t2, mode))

    def polar_shoot(self, fx, fy, theta, r, t1, t2, mode='safe'):
        """Send cart_shoot request.

        Args
            fx, fy -- x, y coordinate of slingshot
            theta, r -- relative polar coordinates of release point w.r.t (fx,fy)
            t1 -- release time
            t2 -- gap between release time and tap time

        Return True if accepted, False if rejected.
        """
        return self.send_and_recv_result(
                message.polar_shoot(fx, fy, theta, r, t1, t2, mode))

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
        return self.send_and_recv_result(message.load_level(level))

    def restart_level(self):
        """Send restart level request.
        Return True if succeeded, False otherwise.
        """
        return self.send_and_recv_result(message.restart_level())

