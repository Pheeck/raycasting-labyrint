class Player:
    """
    Represents the state of the player: his position and camera orientation.
    """

    def __init__(self, startPos, startRay, raycasting, fovRays):
        """
        Parameters
        ----------
        startPos : numpy Vector2
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
        return self.middleRay
    
    def get_left_ray(self):
        return self.leftRay
    
    def get_right_ray(self):
        return self.rightRay
    
    def move_absolute(self, vector):
        self.pos += vector
    
    def move_in_ray(self, magnitude, ray):
        # Check for collision with a wall first
        foo, bar, foobar = self.raycasting.cast_rays(ray, ray, self.pos)
        distanceToWall = foo[0]
        collision = (not distanceToWall is None) and distanceToWall <= magnitude

        if not collision:
            # Now move
            vector = self.raycasting.get_ray_vector(ray)
            vector *= magnitude
            self.move_absolute(vector)

    def move_forward(self, magnitude):
        ray = self.middleRay
        self.move_in_ray(magnitude, ray)        
    
    def move_backward(self, magnitude):
        ray = self.middleRay
        ray = self.raycasting.reverse_ray(ray)
        self.move_in_ray(magnitude, ray) 
    
    def move_right(self, magnitude):
        ray = self.middleRay
        ray = self.raycasting.perpendicular_right_ray(ray)
        self.move_in_ray(magnitude, ray) 
    
    def move_left(self, magnitude):
        ray = self.middleRay
        ray = self.raycasting.perpendicular_left_ray(ray)
        self.move_in_ray(magnitude, ray) 

    def turn(self, n):
        self.middleRay = self.raycasting.offset_ray(self.middleRay, n)
        self.leftRay = self.raycasting.offset_ray(self.leftRay, n)
        self.rightRay = self.raycasting.offset_ray(self.rightRay, n)
