class Player:
    """
    Represents the state of the player: his position and camera orientation.
    """

    def __init__(self, startPos, startRay, raycasting, fovRays):
        """
        Parameters
        ----------
        startPos : numpy.Vector2
        startRay : int
        raycasting : Raycasting object from raycasting.py
        fovRays : int
        """
        self.pos = startPos
        self.middleRay = startRay  # Which ray should be in the middle of the screen
        self.raycasting = raycasting

        self.leftRay = None
        self.rightRay = None

        # Rays on the far left and right of the screen
        self.leftRay = self.raycasting.offset_ray(self.middleRay, int(-(fovRays // 2)))  
        self.rightRay = self.raycasting.offset_ray(self.middleRay,
                                                   fovRays - int((fovRays // 2)))   
    
    def get_pos(self):
        return self.pos
    
    def get_middle_ray(self):
        """
        Get the ray in the middle of FOV.
        """
        return self.middleRay
    
    def get_left_ray(self):
        """
        Get the ray in the far left of FOV.
        """
        return self.leftRay
    
    def get_right_ray(self):
        """
        Get the ray in the far right of FOV.
        """
        return self.rightRay
    
    #
    # Movement
    #
    
    def _move_absolute(self, vector):
        """
        Parameters
        ----------
        vector : pygame.Vector2
        """
        self.pos += vector
    
    def _move_in_ray(self, magnitude, ray):
        """
        Move a specified number of units along a ray unless
        a collision is detected in that direction.

        Parameters
        ----------
        magnitude : float
        ray : int
        """
        # Check for collision with a wall first
        foo, bar, foobar = self.raycasting.cast_rays(ray, ray, self.pos)
        distanceToWall = foo[0]
        collision = (not distanceToWall is None) and distanceToWall <= magnitude

        if not collision:
            # Now move
            vector = self.raycasting.get_ray_vector(ray)
            self._move_absolute(vector * magnitude)

    def move_forward(self, magnitude):
        """
        Move a specified number of units forward.
        a collision is detected in that direction.

        Parameters
        ----------
        magnitude : float
        """
        ray = self.middleRay
        self._move_in_ray(magnitude, ray)        
    
    def move_backward(self, magnitude):
        """
        Move a specified number of units backward.
        a collision is detected in that direction.

        Parameters
        ----------
        magnitude : float
        """
        ray = self.middleRay
        ray = self.raycasting.reverse_ray(ray)
        self._move_in_ray(magnitude, ray) 
    
    def move_right(self, magnitude):
        """
        Move a specified number of units to the right.
        a collision is detected in that direction.

        Parameters
        ----------
        magnitude : float
        """
        ray = self.middleRay
        ray = self.raycasting.perpendicular_right_ray(ray)
        self._move_in_ray(magnitude, ray) 
    
    def move_left(self, magnitude):
        """
        Move a specified number of units to the left.
        a collision is detected in that direction.

        Parameters
        ----------
        magnitude : float
        """
        ray = self.middleRay
        ray = self.raycasting.perpendicular_left_ray(ray)
        self._move_in_ray(magnitude, ray) 

    def turn(self, n):
        """
        Turn the camera a specified number of rays left (negative n)
        or right (positive n). 

        Parameters
        ----------
        n : int
        """
        self.middleRay = self.raycasting.offset_ray(self.middleRay, n)
        self.leftRay = self.raycasting.offset_ray(self.leftRay, n)
        self.rightRay = self.raycasting.offset_ray(self.rightRay, n)
