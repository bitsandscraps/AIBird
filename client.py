import socket
import message

MAX_TRIALS = 5

class AIBirdClient:
    def __init__(self, host='localhost', port=2004, team_id=1):
        self.host = host
        self.port = port
        self.team_id = team_id
        self.socket = None

    def connect(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((self.host, self.port))
        self.socket.sendall(message.configure(self.team_id))
        data = self.socket.recv(message.LEN_CONFIGURE)
        message.recv_configure(data)

    def screenshot(self):
        self.socket.sendall(message.get_screenshot())
        size = message.recv_screenshot_size(self.socket.recv(message.LEN_SCREENSHOT))
        return message.recv_screenshot(self.socket.recv(size))

    def best_score(self):
        self.socket.sendall(message.get_best_score())
        return message.recv_score(self.socket.recv(message.LEN_GET_SCORE))

    def my_score(self):
        self.socket.sendall(message.get_my_score())
        return message.recv_score(self.socket.recv(message.LEN_GET_SCORE))

    def current_level(self):
        self.socket.sendall(message.get_current_level())
        return message.recv_current_level(self.socket.recv(message.LEN_GET_CURRENT_LEVEL))

    def retry_until_success(self, msg):
        for _ in range(MAX_TRIALS):
            self.socket.sendall(msg)
            if message.recv_result(self.socket.recv(message.LEN_ETC)):
                return True
        return False

    def cart_shoot(self, fx, fy, dx, dy, t1, t2, mode='safe'):
        if not self.retry_until_success(message.cart_shoot(fx, fy, dx, dy, t1, t2, mode)):
            raise ValueError('Max Trial Exceeded: cart_shoot')
        
    def polar_shoot(self, fx, fy, theta, r, t1, t2, mode='safe'):
        if not self.retry_until_success(message.polar_shoot(fx, fy, theta, r, t1, t2, mode)):
            raise ValueError('Max Trial Exceeded: polar_shoot')
        
    def zoom_in(self):
        if not self.retry_until_success(message.zoom_in()):
            raise ValueError('Max Trial Exceeded: zoom_in')

    def zoom_out(self):
        if not self.retry_until_success(message.zoom_out()):
            raise ValueError('Max Trial Exceeded: zoom_out')

    def click_in_center(self):
        if not self.retry_until_success(message.click_in_center()):
            raise ValueError('Max Trial Exceeded: click_in_center')

    def load_level(self, level):
        if not self.retry_until_success(message.load_level(level)):
            raise ValueError('Max Trial Exceeded: load_level')

    def restart_level(self):
        if not self.retry_until_success(message.restart_level()):
            raise ValueError('Max Trial Exceeded: restart_level')

