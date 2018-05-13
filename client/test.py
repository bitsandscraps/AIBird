import sys
import scipy.misc
import aibird_client

def main():
    abc = aibird_client.AIBirdClient()
    abc.connect()
    while True:
        c = input('>')[0]
        if c == 'h':
            print('h: help, s: score, c: cshoot, p: pshoot, i: zoom in,',
                  'o: zoom out, l: load level, r: restart level'
                  'e: is over? a: screenshot')
        elif c == 's':
            print(abc.current_score)
        elif c == 'c':
            arg = [int(x) for x in input('dx dy t1 t2: ').split()]
            print(abc.cart_shoot(arg[0], arg[1], arg[2], arg[3]))
        elif c == 'p':
            arg = input('r theta t1 t2: ').split()
            r = int(arg[0])
            theta = float(arg[1])
            t1 = int(arg[2])
            t2 = int(arg[3])
            print(abc.polar_shoot(r, theta, t1, t2))
        elif c == 'i':
            print(abc.zoom_in())
        elif c == 'o':
            print(abc.zoom_out())
        elif c == 'l':
            abc.current_level = int(input('level? '))
        elif c == 'r':
            print(abc.restart_level())
        elif c == 'e':
            print(abc.is_level_over)
        elif c == 'a':
            ss = abc.screenshot
            scipy.misc.imsave(input('filename? '), ss)





if __name__ == "__main__":
    main()
