import sys
import client

def main():
    abc = client.AIBirdClient()
    abc.connect()
    while True:
        c = sys.stdin.read(1)
        if c == 'h':
            print('h: help, s: score, c: cshoot, p: pshoot, i: zoom in,',
                  'o: zoom out, l: load level, r: restart level')
        elif c == 's':
            print(abc.my_score())
        elif c == 'c':
            arg = [int(x) for x in input('dx dy t1 t2').split()]
            print(abc.cart_shoot(arg[0], arg[1], arg[2], arg[3]))
        elif c == 'p':
            arg = input('r theta t1 t2').split()
            theta = float(arg[1])
            iarg = [int(x) for x in arg]
            print(abc.polar_shoot(iarg[0], theta, iarg[2], iarg[3]))
        elif c == 'i':
            print(abc.zoom_in())
        elif c == 'o':
            print(abc.zoom_out())
        elif c == 'l':
            print(abc.load_level(int(input('level?'))))
        elif c == 'r':
            print(abc.restart_level())


            
                


if __name__ == "__main__":
    main()
