import time
import client

def main():
    abc = client.AIBirdClient()
    abc.connect()
    time.sleep(3)
    for level in range(1, 22):
        print('------------------Level {}------------------'.format(level))
        abc.load_level(level)
        abc.zoom_out()
        abc.cart_shoot(-50, 50, 0, 0)
        print('Current score:', abc.my_score(level))
        while True:
            state = abc.state()
            print(state)
            if state.isover():
                break
            abc.cart_shoot(-50, 50, 0, 0)
            print('Current score:', abc.my_score(level))

if __name__ == "__main__":
    main()
