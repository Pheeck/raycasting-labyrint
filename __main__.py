#! /usr/bin/env python3

"""
Raycasting labyrint
Zápočtový program
Filip Kastl, I. ročník
zimní semestr 2020/21
Programování I NPRG030
"""


from sys import argv, exit
from level import Level
from game import Game


SIZE = (800, 600)
# 4800, 2400, 1200, 600
RAYS = 600  # 1200  # Should be a multiple of 4 and a divisor of (window width * (360 / fov))
FOV = 60
FPS = 60


def main():
    print()  # Newline after the pygame hello message

    # Parse arguments to get the path to a level file
    if len(argv) < 2:
        print("Missing argument: Path to a labyrinth file")
        exit(1)
    levelFile = argv[1]

    # Create level object from level file
    level = Level(levelFile)

    # Create game
    game = Game(level=level, winSize=SIZE, totalRays=RAYS, fovDegrees=FOV, targetFps=FPS)

    # Run game
    game.run()


if __name__ == "__main__":
    main()
