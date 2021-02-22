from math import radians, tan

import pygame

from player import Player
from raycasting import Raycasting


class Game:
    """
    Represents state of the game. Initializes pygame and all necessary variables and
    constants on object creation.
    """

    def __init__(self, level, winSize, totalRays, fovDegrees, targetFps):
        self.level = level
        self.winSize = winSize
        self.fovDegrees = fovDegrees
        self.targetFps = targetFps

        self.moveSpeed = 1  # Player move speed in units
        self.turnSpeed = 4  # Camera turn speed in number of rays
        self.blockSize = 64  # Walls will be blockSize x blockSize x blockSize units big
        self.projectionWidth = 12  # How big should the screen be inside the game world
        self.ceilColor = (32, 32, 128)
        self.wallColor = (128, 128, 128)
        self.floorColor = (48, 48, 48)
        self.flagColor = (128, 128, 0)
        self.minimapPlayerColor = (255, 0, 0)
        self.minimapSizeDiv = 4     # Draw minimap this number times smaller
        self.minimapPlayerSize = 4  # How many pixels wide should the player dot be
        self.darkDistance = 10 * self.blockSize  # The distance after which walls become absolutely dark

        self.raycasting = None
        self.screen = None
        self.minimap = None
        self.fovRays = None
        self.pixelsPerRay = None
        self.player = None
        self.winScreen = None

        # Initialize raycasting logic
        self.raycasting = Raycasting(totalRays, self.blockSize, self.level)

        # Initialize pygame
        pygame.init()
        pygame.display.set_caption("Raycasting labyrint")
        self.screen = pygame.display.set_mode(self.winSize)

        # Prepare minimap
        minimapSize = self.level.get_size() * self.blockSize // self.minimapSizeDiv
        self.minimap = pygame.Surface((minimapSize.x, minimapSize.y))

        # Compute fov related stuff
        self.fovRays = self.raycasting.degrees_to_ray_number(self.fovDegrees)
        self.pixelsPerRay = winSize[0] // (totalRays // (360 // self.fovDegrees))

        # Compute distance between player and the projection plane (also fov stuff)
        self.distanceToProjection = int((self.projectionWidth) /
                                        (tan(radians(self.fovDegrees / 2))))
        
        # Prepare fisheye correction
        self.fisheyeCoefficients = self.raycasting.fisheye_coefficients(
            self.fovDegrees,
            self.fovRays
        )

        # Create player object
        startPos = self.level.get_start_block() * self.blockSize
        startPos[0] = startPos.x + (self.blockSize // 2)  # Center vertically
        startPos[1] = startPos.y + (self.blockSize // 2)  # Center horizontally
        self.player = Player(startPos, 0, self.raycasting, self.fovRays)

        # Create win screen
        self.winScreen = pygame.Surface(winSize, flags=pygame.SRCALPHA)
        self.winScreen.fill(
            (
                self.floorColor[0],
                self.floorColor[1],
                self.floorColor[2],
                128  # Specify win screen opacity
            )
        )
        # TODO
    
    def run(self):
        """
        Main game loop.
        """
        clock = pygame.time.Clock()
        keepGoing = True
        win = False  # Is set to True player reaches the flag

        while keepGoing:
            # Handle events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    keepGoing = False
            
            # Player and camera movement
            pressedKeys = pygame.key.get_pressed()

            if pressedKeys[pygame.K_w]:
                self.player.move_forward(self.moveSpeed)
            if pressedKeys[pygame.K_s]:
                self.player.move_backward(self.moveSpeed)
            if pressedKeys[pygame.K_a]:
                self.player.move_left(self.moveSpeed)
            if pressedKeys[pygame.K_d]:
                self.player.move_right(self.moveSpeed)

            if pressedKeys[pygame.K_j]:
                self.player.turn(-self.turnSpeed)
            if pressedKeys[pygame.K_l]:
                self.player.turn(self.turnSpeed)

            # End the game if 'Q' is pressed
            if pressedKeys[pygame.K_q]:
                keepGoing = False
            
            # Check if flag was reached
            if (not win) and self.player.get_pos() // self.blockSize == self.level.get_flag_block():
                win = True

            # Draw floor and ceiling
            self.screen.fill(self.floorColor)
            ceilRect = pygame.Rect(0, 0, self.winSize[0], self.winSize[1] // 2)  # TODO Precompute
            pygame.draw.rect(self.screen, self.ceilColor, ceilRect)

            # Render walls
            distances, intersections, flagDistances = self.raycasting.cast_rays(  # Cast rays
                self.player.get_left_ray(),
                self.player.get_right_ray(),
                self.player.get_pos()
            )
            for i, distance in enumerate(distances):
                if not distance is None:
                    #
                    # Draw a column coresponding to each cast ray
                    #

                    # distance -= 16 ### TODO

                    currPixel = i * self.pixelsPerRay

                    # Compute height of the column
                    if -1.0 < distance < 1.0:
                        height = self.winSize[1]
                    else:
                        height = self.winSize[1] / distance * self.distanceToProjection
                    
                    # Apply fisheye correction
                    height *= self.fisheyeCoefficients[i]

                    # Compute color of the column
                    colorCoeficient = distance / self.darkDistance
                    if colorCoeficient > 1.0:
                        colorCoeficient = 1.0
                    red = self.wallColor[0] * (1.0 - colorCoeficient) + \
                          self.ceilColor[0] * colorCoeficient
                    green = self.wallColor[1] * (1.0 - colorCoeficient) + \
                            self.ceilColor[1] * colorCoeficient
                    blue = self.wallColor[2] * (1.0 - colorCoeficient) + \
                           self.ceilColor[2] * colorCoeficient
                    color = (red, green, blue)

                    # Draw the column
                    column = pygame.Rect(currPixel, self.winSize[1] // 2 - (height // 2),
                                       self.pixelsPerRay, height)
                    pygame.draw.rect(self.screen, color, column)
            
            # Render flag
            for i, distance in enumerate(flagDistances):
                if not distance is None:
                    currPixel = i * self.pixelsPerRay

                    # Compute height of the column
                    if -0.1 < distance < 0.1:
                        height = self.winSize[1]
                    else:
                        height = self.winSize[1] / distance * self.distanceToProjection / 5
                        # (we divide by 5 because flag is supposed to be shorter than a wall)
                        # TODO set this elsewhere
                    
                    # Apply fisheye correction
                    height *= self.fisheyeCoefficients[i]

                    # Compute color of the column
                    colorCoeficient = distance / self.darkDistance
                    if colorCoeficient > 1.0:
                        colorCoeficient = 1.0
                    red = self.flagColor[0] * (1.0 - colorCoeficient) + \
                          self.ceilColor[0] * colorCoeficient
                    green = self.flagColor[1] * (1.0 - colorCoeficient) + \
                            self.ceilColor[1] * colorCoeficient
                    blue = self.flagColor[2] * (1.0 - colorCoeficient) + \
                           self.ceilColor[2] * colorCoeficient
                    color = (red, green, blue)

                    # Draw the column
                    column = pygame.Rect(currPixel, self.winSize[1] // 2 - (height // 2),
                                       self.pixelsPerRay, height)
                    pygame.draw.rect(self.screen, color, column)

            # Draw walls on minimap
            self.minimap.fill(self.floorColor)
            for x, wall_column in enumerate(self.level.get_walls()):
                for y, wall in enumerate(wall_column):
                    if wall:
                        rectSize = self.blockSize // self.minimapSizeDiv
                        rectX = x * rectSize
                        rectY = y * rectSize
                        rect = pygame.Rect(rectX, rectY, rectSize, rectSize)
                        pygame.draw.rect(self.minimap, self.wallColor, rect)
            
            # Draw flag on minimap
            x, y = self.level.get_flag_block()
            rectSize = self.blockSize // self.minimapSizeDiv
            rectX = x * rectSize
            rectY = y * rectSize
            rect = pygame.Rect(rectX, rectY, rectSize, rectSize)
            pygame.draw.rect(self.minimap, self.flagColor, rect)
            
            # Draw player on minimap
            rectX = self.player.get_pos().x // self.minimapSizeDiv
            rectY = self.player.get_pos().y // self.minimapSizeDiv
            rectX -= self.minimapPlayerSize // 2
            rectY -= self.minimapPlayerSize // 2
            rect = pygame.Rect(rectX, rectY, self.minimapPlayerSize, self.minimapPlayerSize)
            pygame.draw.rect(self.minimap, self.minimapPlayerColor, rect)

            # Draw intersections (of rays that have been cast) on minimap
            for intersection in intersections:
                if not intersection is None:
                    rectX = intersection.x // self.minimapSizeDiv
                    rectY = intersection.y // self.minimapSizeDiv
                    rect = pygame.Rect(rectX, rectY, 1, 1)
                    pygame.draw.rect(self.minimap, self.minimapPlayerColor, rect)
            
            # Blit minimap onto window
            #self.screen.blit(self.minimap, (0, 0))

            # Blit win screen if player already won
            if win:
                self.screen.blit(self.winScreen, (0, 0))
    
            # Finish drawing
            pygame.display.flip()
            clock.tick(self.targetFps)
