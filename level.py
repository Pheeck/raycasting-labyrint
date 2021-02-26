from pygame import Vector2

class Level:
    """
    Represents a maze already loaded into program memory. Loading a maze from a file
    happens on object creation. Coordinates used inside of this object are in blocks,
    not in units.
    """

    def __init__(self, levelFile):
        """
        Parameters
        ----------
        levelFile : string
        """
        self.walls = []
        self.size = None
        self.startBlock = None
        self.flagBlock = None

        # Load walls and player positions from level file
        with open(levelFile, "r") as f:
            width, height = map(int, f.readline().split())
            self.size = Vector2(width, height)

            self.walls = [[False] * height for i in range(width)]

            for y, line in enumerate(f):
                if y > self.size[1]:
                    raise Exception("There are too many lines for the specified level height (%d specified)")

                line = line.split()

                for x, char in enumerate(line):
                    if x > self.size[0]:
                        raise Exception("Line %d has too many blocks for the specified level width (%d specified):\n%s" %
                                        (y + 1, line, self.size[0]))

                    if char.lower() == "w":
                        self.walls[x][y] = True
                    elif char.lower() == "p":
                        if not self.startBlock is None:
                            raise Exception("Player starting position is present more than one time.")
                        self.startBlock = Vector2(x, y)
                    elif char.lower() == "f":
                        if not self.flagBlock is None:
                            raise Exception("Flag position is present more than one time.")
                        self.flagBlock = Vector2(x, y)
            
            if self.startBlock is None:
                raise Exception("There is no player position.")
            if self.flagBlock is None:
                raise Exception("There is no flag position.")
    
    def get_walls(self):
        """
        Returns a 2d array.
        """
        return self.walls
    
    def get_size(self):
        """
        Returns the size of the level in blocks as a pygame vector.
        """
        return self.size
    
    def get_start_block(self):
        """
        Returns the block coordinates, where player starts as a pygame vector.
        """
        return self.startBlock
    
    def get_flag_block(self):
        """
        Returns the block coordinates of flag as a pygame vector.
        """
        return self.flagBlock
    
    def is_wall_at(self, x, y):
        """
        Returns if wall is present at given block coordinates. Returns False if
        coordinates outside of the level.

        Parameters
        ----------
        x : int
        y : int
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

        Parameters
        ----------
        x : int
        y : int
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
