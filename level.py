from pygame.math import Vector2


class Level:
    """
    Represents a maze already loaded into program memory. Loading a maze from a file
    happens on object creation. Coordinates used inside of this object are in blocks,
    not in units.
    """

    def __init__(self, levelFile):
        self.walls = []
        self.size = None
        self.startBlock = None
        self.flagBlock = None

        # Load walls and player positions from level file
        with open(levelFile, "r") as f:  # TODO throw errors: blby mezery, 2x hrac, zadna vlajka, ...
            width, height = map(int, f.readline().split())
            self.size = Vector2(width, height)

            self.walls = [[False] * height for i in range(width)]

            for y, line in enumerate(f):
                line = line.split()

                for x, char in enumerate(line):
                    if char.lower() == "w":
                        self.walls[x][y] = True
                    elif char.lower() == "p":
                        self.startBlock = Vector2(x, y)
                    elif char.lower() == "f":
                        self.flagBlock = Vector2(x, y)
    
    def get_walls(self):
        return self.walls
    
    def get_size(self):
        return self.size
    
    def get_start_block(self):
        return self.startBlock
    
    def get_flag_block(self):
        return self.flagBlock
    
    def is_wall_at(self, x, y):
        """
        Returns if wall is present at given block coordinates. Returns False if
        coordinates outside of the level.
        """
        if x < 0 or x >= self.size.x:
            return False
        if y < 0 or y >= self.size.y:
            return False
        return self.walls[x][y]
    
    def is_wall_at_vector(self, v):
        """
        Like is_wall_at(), but takes pygame vector as argument.
        """
        x = int(v.x)
        y = int(v.y)
        return self.is_wall_at(x, y)
    
    def is_flag_at(self, x, y):
        """
        Returns if wall is present at given block coordinates. Returns False if
        coordinates outside of the level.
        """
        if x < 0 or x >= self.size.x:
            return False
        if y < 0 or y >= self.size.y:
            return False
        return x == int(self.flagBlock.x) and y == int(self.flagBlock.y)
    
    def is_flag_at_vector(self, v):
        """
        Like is_flag_at(), but takes pygame vector as argument.
        """
        x = int(v.x)
        y = int(v.y)
        return self.is_flag_at(x, y)
