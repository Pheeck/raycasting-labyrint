"""
Contains miscellanious functions used for computing graphics and physics.
"""

import numpy as np
from math import sin, cos, pi, radians

from pygame.math import Vector2


class Raycasting:
    """
    Contains logic for everything that has something to do with rays.
    """

    def __init__(self, totalRays, blockSize, level):
        self.totalRays = totalRays
        self.blockSize = blockSize
        self.level = level

        self.renderDistance = 10

        self.rayAngles = []   # Angles of rays in radians
        self.rayVectors = []  # Normalized pygame 2d vector for every ray
        self.rayHorizontalHypotenuses = []  # See documentation
        self.rayVerticalHypotenuses = []

        for x in range(totalRays):
            # Compute ray angles. Equally distribute across 2pi radians.
            angle = x * 2*pi / totalRays  # In radians
            self.rayAngles.append(angle)

            # Compute ray vectors
            v = Vector2(cos(angle), sin(angle))
            self.rayVectors.append(v)

            # Compute vertical hypotenuses
            # Test if hypotenuse isn't parallel to the horizontal grid lines first
            delta = 10e-10  # So that we don't compare floats with ==
            if (pi/2 - delta) < angle < (pi/2 + delta) or \
               (3*pi/2 - delta) < angle < (3*pi/2 - delta):
                # Hypotenuse is parallel to the horizontal grid lines
                hypotenuse = v * self.blockSize  # TODO maybe do something else with these horizontal vectors
            else:
                lenght = blockSize / abs(cos(angle))
                hypotenuse = v * lenght
            self.rayVerticalHypotenuses.append(hypotenuse)

            # Compute horizontal hypotenuses
            # Test if hypotenuse isn't parallel to the vertical grid lines first
            delta = 10e-10  # So that we don't compare floats with ==
            if angle > (2*pi - delta) or angle < (0*pi + delta) or \
               (pi - delta) < angle < (pi - delta):
                # Hypotenuse is parallel to the vertical grid lines
                hypotenuse = v * self.blockSize
            else:
                lenght = blockSize / abs(sin(angle))
                hypotenuse = v * lenght
            self.rayHorizontalHypotenuses.append(hypotenuse)

    #
    # Getting properties of rays
    #

    def get_ray_angle(self, ray):
        """
        Returns angle of the given ray in radians.
        """
        return self.rayAngles[ray]

    def get_ray_vector(self, ray):
        """
        Returns the normalized pygame 2d vector coresponding to the given ray.
        """
        return self.rayVectors[ray]

    def get_horizontal_hypotenuse(self, ray):
        """
        Returns the horizontal hypotenuse lenght coresponding to the given ray.
        See documentation for details about ray hypotenuses. 
        """
        return self.rayHorizontalHypotenuses[ray]
    
    def get_vertical_hypotenuse(self, ray):
        """
        Returns the vertical hypotenuse lenght coresponding to the given ray.
        See documentation for details about ray hypotenuses. 
        """
        return self.rayHorizontalHypotenuses[ray]

    #
    # Miscellaneous ray computations
    #

    def offset_ray(self, ray, n):
        """
        Given ray A, the function returns a ray B, which is n positions to the right.

        Parameters
        ----------
        ray : int
        n : int
        """
        ray += n
        ray %= self.totalRays
        return ray

    def perpendicular_right_ray(self, ray):
        """
        Given ray A, the function returns ray B where angle(B) = angle(A) + 90 degrees.
        """
        newRay = ray + (self.totalRays // 4)
        newRay %= self.totalRays
        return newRay

    def perpendicular_left_ray(self, ray):
        """
        Given ray A, the function returns ray B where angle(B) = angle(A) - 90 degrees.
        """
        newRay = ray - (self.totalRays // 4)
        newRay %= self.totalRays
        return newRay

    def reverse_ray(self, ray):
        """
        Given ray A, the function returns ray B where angle(B) = -angle(A)
        """
        newRay = ray + (self.totalRays // 2)
        newRay %= self.totalRays
        return newRay

    def degrees_to_ray_number(self, degrees):
        """
        Returns how many rays (rounded down) it takes to span the given viewing angle.
        """
        degreesPerRay = 360 / self.totalRays
        return degrees // degreesPerRay

    #
    # Casting rays
    #
    
    def cast_rays(self, startRay, endRay, fromPos):
        """
        For each ray in range <startRay, endRay> (including both of these), cast it
        from the coordinates fromPos and return the distance it traveled until it hit
        a wall and the coordinates of the hit and the distance it traveled until it
        intersected flag (if it did intersect it) in a tupple of two lists
        (of the same lenght):
        
        (
            list of floats: distances,
            list of Vector2s: intersections,
            list of floats: flagDistances
        )

        If something is going wrong with the program, the reason is probably somewhere
        in this method. It does the most computations and it is pretty messy and long.
        """
        resultDistances = []
        resultIntersections = []
        resultFlagDistances = []

        #
        # Prepare necessary values and functions first
        #

        # On which block is the player standing?
        fromBlockPos = Vector2(
            fromPos.x // self.blockSize,
            fromPos.y // self.blockSize
        )

        # Find the nearest vertical and horizontal lines to player pos in all directions
        rightVerticalLine = fromBlockPos.x
        leftVerticalLine = fromBlockPos.x - 1
        downHorizontalLine = fromBlockPos.y
        upHorizontalLine = fromBlockPos.y - 1

        levelSize = self.level.get_size()
        if rightVerticalLine > levelSize.x - 2:
            rightVerticalLine = None  # None means that there are no more lines in that direction
        if leftVerticalLine < 0:
            leftVerticalLine = None
        if downHorizontalLine > levelSize.y - 2:
            downHorizontalLine = None
        if upHorizontalLine < 0:
            upHorizontalLine = None
        
        # Line and ray intersection functions
        def inter_ray_line_vertical(rayVector, line):
            """
            Return the intersection coordinates of given ray cast from fromPos and
            given vertical line.

            Ray argument is taken as the vector corresponding to the given ray.
            """
            lineVector = Vector2(0, 1)  # Downward unit vector
            linePos = Vector2((line + 1) * self.blockSize, 0)
            return self.intersect_lines(fromPos, rayVector, linePos, lineVector)
        
        def inter_ray_line_horizontal(rayVector, line):
            """
            Return the intersection coordinates of given ray cast from fromPos and
            given horizontal line.

            Ray argument is taken as the vector corresponding to the given ray.
            """
            lineVector = Vector2(1, 0)  # Leftward unit vector
            linePos = Vector2(0, (line + 1) * self.blockSize)
            return self.intersect_lines(fromPos, rayVector, linePos, lineVector)
        
        #
        # Cast the rays
        #

        currRay = startRay
        endRay = self.offset_ray(endRay, 1)  # We want to include the original endRay
        while currRay != endRay:
            rayVector = self.get_ray_vector(currRay)

            # Vertical
            flagDistanceVert = None

            if rayVector.x > 0:
                if rightVerticalLine is None:
                    interVert = None
                    distanceVert = None
                else:
                    # Find intersection with the nearest grid line.
                    interVert = inter_ray_line_vertical(rayVector, rightVerticalLine)

                    # Check if ray actually hits a wall at this intersection. Otherwise
                    # "extend" the ray and compute another intersection. Do until a wall
                    # is hit or max render distance is exceeded. (*)
                    interBlock = self.rightBlockOfPos(interVert - Vector2(0.1, 0.1)) #### TODO
                    i = 0
                    while i <= self.renderDistance and \
                          not self.level.is_wall_at_vector(interBlock):

                        # Check if flag was hit
                        if flagDistanceVert is None and self.level.is_flag_at_vector(interBlock):
                            # If it was, compute distance to the flag intersection
                            flagDistanceVert = interVert.distance_to(fromPos)

                        # Extend the ray
                        interVert += self.rayVerticalHypotenuses[currRay]
                        interBlock = self.rightBlockOfPos(interVert - Vector2(0.1, 0.1)) ####
                        i += 1
                    if i > self.renderDistance:  # Max render distance was exceeded
                        interVert = None
                        distanceVert = None
                    else:
                        # Compute distance to the intersection
                        distanceVert = interVert.distance_to(fromPos)
            elif rayVector.x < 0:
                if leftVerticalLine is None:
                    interVert = None
                    distanceVert = None
                else:
                    # Find intersection with the nearest grid line.
                    interVert = inter_ray_line_vertical(rayVector, leftVerticalLine)

                    # See (*) in a comment above
                    interBlock = self.leftBlockOfPos(interVert - Vector2(0.1, 0.1)) ####
                    i = 0
                    while i <= self.renderDistance and \
                          not self.level.is_wall_at_vector(interBlock):
                        
                        # Check if flag was hit
                        if flagDistanceVert is None and self.level.is_flag_at_vector(interBlock):
                            # If it was, compute distance to the flag intersection
                            flagDistanceVert = interVert.distance_to(fromPos)

                        # Extend the ray
                        interVert += self.rayVerticalHypotenuses[currRay]
                        interBlock = self.leftBlockOfPos(interVert - Vector2(0.1, 0.1)) ####
                        i += 1
                    if i > self.renderDistance:  # Max render distance was exceeded
                        interVert = None
                        distanceVert = None
                    else:
                        # Compute distance to the intersection
                        distanceVert = interVert.distance_to(fromPos)
            else:
                interVert = None
                distanceVert = None
            
            # Horizontal
            flagDistanceHor = None

            if rayVector.y > 0:
                if downHorizontalLine is None:
                    interHor = None
                    distanceHor = None
                else:
                    # Find intersection with the nearest grid line.
                    interHor = inter_ray_line_horizontal(rayVector, downHorizontalLine)

                    # See (*) in a comment above
                    interBlock = self.downBlockOfPos(interHor - Vector2(0.1, 0.1)) ####
                    i = 0
                    while i <= self.renderDistance and \
                          not self.level.is_wall_at_vector(interBlock):

                        # Check if flag was hit
                        if flagDistanceHor is None and self.level.is_flag_at_vector(interBlock):
                            # If it was, compute distance to the flag intersection
                            flagDistanceHor = interHor.distance_to(fromPos)

                        # Extend the ray
                        interHor += self.rayHorizontalHypotenuses[currRay]
                        interBlock = self.downBlockOfPos(interHor - Vector2(0.1, 0.1)) ####
                        i += 1
                    if i > self.renderDistance:  # Max render distance was exceeded
                        interHor = None
                        distanceHor = None
                    else:
                        # Compute distance to the intersection
                        distanceHor = interHor.distance_to(fromPos)
            elif rayVector.y < 0:
                if upHorizontalLine is None:
                    interHor = None
                    distanceHor = None
                else:
                    # Find intersection with the nearest grid line.
                    interHor = inter_ray_line_horizontal(rayVector, upHorizontalLine)

                    # See (*) in a comment above
                    interBlock = self.upBlockOfPos(interHor - Vector2(0.1, 0.1)) ####
                    i = 0
                    while i <= self.renderDistance and \
                          not self.level.is_wall_at_vector(interBlock):
                        
                        # Check if flag was hit
                        if flagDistanceHor is None and self.level.is_flag_at_vector(interBlock):
                            # If it was, compute distance to the flag intersection
                            flagDistanceHor = interHor.distance_to(fromPos)

                        # Extend the ray
                        interHor += self.rayHorizontalHypotenuses[currRay]
                        interBlock = self.upBlockOfPos(interHor - Vector2(0.1, 0.1)) ####
                        i += 1
                    if i > self.renderDistance:  # Max render distance was exceeded
                        interHor = None
                        distanceHor = None
                    else:
                        # Compute distance to the intersection
                        distanceHor = interHor.distance_to(fromPos)
            else:
                interHor = None
                distanceHor = None
            
            # Choose the nearest intersection as the final one
            if distanceVert is None:
                intersection = interHor
                distance = distanceHor
            elif distanceHor is None:
                intersection = interVert
                distance = distanceVert
            else:
                if distanceVert < distanceHor:
                    intersection = interVert
                    distance = distanceVert
                else:
                    intersection = interHor
                    distance = distanceHor
            
            # Flag shouldn't be seen if intersection with a wall is closer
            if not distance is None:
                if (not flagDistanceVert is None) and distance < flagDistanceVert:
                    flagDistanceVert = None
                if (not flagDistanceHor is None) and distance < flagDistanceHor:
                    flagDistanceHor = None

            # Also choose the nearest flag intersection
            if flagDistanceVert is None:
                flagDistance = flagDistanceHor
            elif flagDistanceHor is None:
                flagDistance = flagDistanceVert
            else:
                if flagDistanceVert < flagDistanceHor:
                    flagDistance = flagDistanceVert
                else:
                    flagDistance = flagDistanceHor
            
            resultDistances.append(distance)
            resultIntersections.append(intersection)
            resultFlagDistances.append(flagDistance)

            # Increment
            currRay = self.offset_ray(currRay, 1)

        return resultDistances, resultIntersections, resultFlagDistances

    #
    # Fisheye
    #

    @staticmethod
    def fisheye_coefficients(fovDegrees, fovRays):
        """
        Given parameters of fov, this function returns coefficients that cancel the
        fisheye effect if used when calculating wall height from how far which ray
        traveled.
        """
        result = []

        degreesPerRay = fovDegrees / fovRays
        i = 0
        while i <= fovRays:  # Including the rightmost ray
            angleOffset = degreesPerRay * (i - (fovRays // 2))
            result.append(1 / cos(radians(angleOffset)))
            i += 1

        return result

    #
    # Internal methods of the class
    #
    
    @staticmethod
    def intersect_lines(p1, v1, p2, v2):
        """
        Given two lines defined by point p1 and vector v1 and point p2 and vector
        p2, return their intersection coordinates.

        Takes and returns pygame vectors.
        """
        # Get t - coordinate inside the affine subspace of the first line
        matrix1 = np.array(
            [
                [v1.x, v2.x],
                [v1.y, v2.y]
            ]
        )
        matrix1Extension = np.array(
            [
                p2.x - p1.x,
                p2.y - p1.y
            ]
        )
        t = np.linalg.solve(matrix1, matrix1Extension)[0] 

        # Get absolute coordinates from t and return them
        matrix2 = np.array(
            [
                [p1.x, v1.x],
                [p1.y, v1.y]
            ]
        )
        matrix3 = np.array(
            [
                1,
                t
            ]
        )
        result = np.matmul(matrix2, matrix3)
        return Vector2(result[0], result[1])
    
    def upBlockOfPos(self, pos):
        """
        Returns coordinates of the nearest block up of the given position.
        """
        blockPos = pos // self.blockSize
        return blockPos
    
    def downBlockOfPos(self, pos):
        """
        Returns coordinates of the nearest block down of the given position.
        """
        blockPos = pos // self.blockSize
        blockPos.y += 1
        return blockPos
    
    def rightBlockOfPos(self, pos):
        """
        Returns coordinates of the nearest block to the right of the given position.
        """
        blockPos = pos // self.blockSize
        blockPos.x += 1
        return blockPos

    def leftBlockOfPos(self, pos):
        """
        Returns coordinates of the nearest block to the left of the given position.
        """
        blockPos = pos // self.blockSize
        return blockPos
