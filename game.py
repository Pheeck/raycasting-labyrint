from math import radians, tan, ceil
from random import random

import pygame

from player import Player
from raycasting import Raycasting


#
# Constants
#

# Normalized for RAYS=600, FPS=60
NORMALIZED_MOVE = 1.0  # Player move speed in units for RAYS=600, FPS=60
NORMALIZED_TURN = 4    # Camera turn speed in number of rays for RAYS

NORMALIZED_CATACLYSM = 2.0  # Speed of win animation

BLOCK_SIZE = 64        # Walls will be blockSize x blockSize x blockSize units big
PROJECTION_WIDTH = 12  # How big should the screen be inside the game world

FLAG_HEIGHT_DIV = 5    # Flag will be this number times shorter than wall

CEIL_COLOR = (32, 32, 128)
WALL_COLOR = (128, 128, 128)
FLOOR_COLOR = (48, 48, 48)
FLAG_COLOR = (128, 128, 0)
MINIMAP_COLOR = (255, 0, 0)
TEXT_COLOR = (255, 255, 255)
WIN_SCREEN_OPACITY = 172  # 255 is maximum

MINIMAP_SIZE_DIV = 4     # Draw minimap this number times smaller than real units
MINIMAP_PLAYER_SIZE = 4  # How many pixels wide should the player dot be

RENDER_DISTANCE = 10 * BLOCK_SIZE  # The distance after which walls become absolutely dark


#
# Classes
#

class Game:
    """
    Represents state of the game. Initializes pygame and all necessary variables and
    constants on object creation.
    """

    def __init__(self, level, windowSize, totalRays, fovDegrees, targetFps):
        self.level = level
        self.windowSize = windowSize
        self.fovDegrees = fovDegrees
        self.targetFps = targetFps

        self.moveSpeed = NORMALIZED_MOVE * (60 / targetFps)
        self.turnSpeed = NORMALIZED_TURN * (60 / targetFps) * (totalRays / 600)
        self.cataclysmSpeed = NORMALIZED_CATACLYSM * 0.00001 * (60 / targetFps)

        self.raycasting = None
        self.screen = None
        self.font = None
        self.minimap = None
        self.fovRays = None
        self.pixelsPerRay = None
        self.distanceToProjection = None
        self.player = None
        self.winScreen = None

        # Initialize raycasting logic
        self.raycasting = Raycasting(totalRays, BLOCK_SIZE, self.level)

        # Initialize pygame
        pygame.init()
        pygame.display.set_caption("Raycasting labyrint")
        self.screen = pygame.display.set_mode(self.windowSize)

        # Prepare font rendering
        pygame.font.init()
        self.font = pygame.font.SysFont("Sans Serif", 30)

        # Prepare minimap
        minimapSize = self.level.get_size() * BLOCK_SIZE // MINIMAP_SIZE_DIV
        self.minimap = pygame.Surface((minimapSize.x, minimapSize.y))

        # Compute fov related stuff
        self.fovRays = self.raycasting.degrees_to_ray_number(self.fovDegrees)
        self.pixelsPerRay = windowSize[0] // (totalRays // (360 // self.fovDegrees))

        # Compute distance between player and the projection plane (also fov stuff)
        self.distanceToProjection = int((PROJECTION_WIDTH) /
                                        (tan(radians(self.fovDegrees / 2))))
        
        # Prepare fisheye correction
        self.fisheyeCoefficients = self.raycasting.fisheye_coefficients(
            self.fovDegrees,
            self.fovRays
        )

        # Create player object
        startPos = self.level.get_start_block() * BLOCK_SIZE
        startPos[0] = startPos.x + (BLOCK_SIZE // 2)  # Center vertically
        startPos[1] = startPos.y + (BLOCK_SIZE // 2)  # Center horizontally
        self.player = Player(startPos, 0, self.raycasting, self.fovRays)

        # Create win screen
        self.winScreen = pygame.Surface(windowSize, flags=pygame.SRCALPHA)
        self.winScreen.fill(
            (
                CEIL_COLOR[0],
                CEIL_COLOR[1],
                CEIL_COLOR[2],
                WIN_SCREEN_OPACITY
            )
        )
        youWon = self.font.render("You won!", False, TEXT_COLOR)
        pressQ = self.font.render("Press 'Q' to quit.", False, TEXT_COLOR)
        self.winScreen.blit(youWon, (8, 8))
        self.winScreen.blit(pressQ, (8, 40))
    
    def run(self):
        """
        Main game loop.
        """

        clock = pygame.time.Clock()
        keepGoing = True

        playerHasMoved = False
        timerOn = False
        timer = 0.0

        win = False      # Set to True when player reaches the flag
        drawMinimap = False

        cataclysm = 0.0  # Win screen animation time
        cataclysmedRays = [0] * self.raycasting.get_total_rays()

        while keepGoing:
            #
            # Events and user input
            #

            # Handle events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    keepGoing = False
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_q:  # If 'q' was pressed down
                        # Quit game
                        keepGoing = False
                    if event.key == pygame.K_m:  # If 'm' was pressed down
                        # Toggle minimap
                        drawMinimap = not drawMinimap
            
            # Player and camera movement
            pressedKeys = pygame.key.get_pressed()

            self.moveSpeed *= 1.0 - cataclysm

            if pressedKeys[pygame.K_w]:
                self.player.move_forward(self.moveSpeed)

                if not playerHasMoved:
                    playerHasMoved = True
                    timerOn = True
            if pressedKeys[pygame.K_s]:
                self.player.move_backward(self.moveSpeed)
                
                if not playerHasMoved:
                    playerHasMoved = True
                    timerOn = True
            if pressedKeys[pygame.K_a]:
                self.player.move_left(self.moveSpeed)
                
                if not playerHasMoved:
                    playerHasMoved = True
                    timerOn = True
            if pressedKeys[pygame.K_d]:
                self.player.move_right(self.moveSpeed)
                
                if not playerHasMoved:
                    playerHasMoved = True
                    timerOn = True

            if pressedKeys[pygame.K_j]:
                self.player.turn(-self.turnSpeed)
            if pressedKeys[pygame.K_l]:
                self.player.turn(self.turnSpeed)

            #
            # Win stuff
            #
            
            # Check if flag was reached
            if (not win) and self.player.get_pos() // BLOCK_SIZE == self.level.get_flag_block():
                win = True
                timerOn = False

                self.moveSpeed /= 2.0
                self.turnSpeed //= 2
            
            # Animate cataclysm
            i = 0
            while i < len(cataclysmedRays):
                if cataclysmedRays[i] < 3:
                    if random() < cataclysm:
                        cataclysmedRays[i] = 1
                    if random() < cataclysm:
                        cataclysmedRays[i] = 2
                    if random() < cataclysm:
                        cataclysmedRays[i] = 3
                i += 1

            if win:
                if cataclysm < 1.0:
                    cataclysm += self.cataclysmSpeed
                else:
                    cataclysm = 1.0
            
            #
            # Rendering
            #

            # Draw floor and ceiling
            self.screen.fill(FLOOR_COLOR)
            ceilRect = pygame.Rect(0, 0, self.windowSize[0], self.windowSize[1] // 2)
            pygame.draw.rect(self.screen, CEIL_COLOR, ceilRect)

            # Render walls
            distances, intersections, flagDistances = self.raycasting.cast_rays(  # Cast rays
                self.player.get_left_ray(),
                self.player.get_right_ray(),
                self.player.get_pos(),
                messUpRays=cataclysmedRays
            )
            for i, distance in enumerate(distances):
                if not distance is None:
                    #
                    # Draw a column coresponding to each cast ray
                    #

                    currPixel = i * self.pixelsPerRay

                    # Compute height of the column
                    if -1.0 < distance < 1.0:
                        height = self.windowSize[1]
                    else:
                        height = self.windowSize[1] / distance * self.distanceToProjection
                    
                    # Apply fisheye correction
                    height *= self.fisheyeCoefficients[i]

                    # Compute color of the column
                    colorCoeficient = distance / RENDER_DISTANCE
                    if colorCoeficient > 1.0:
                        colorCoeficient = 1.0
                    red = WALL_COLOR[0] * (1.0 - colorCoeficient) + \
                          CEIL_COLOR[0] * colorCoeficient
                    green = WALL_COLOR[1] * (1.0 - colorCoeficient) + \
                            CEIL_COLOR[1] * colorCoeficient
                    blue = WALL_COLOR[2] * (1.0 - colorCoeficient) + \
                           CEIL_COLOR[2] * colorCoeficient
                    color = (red, green, blue)

                    # Draw the column
                    column = pygame.Rect(currPixel, self.windowSize[1] // 2 - (height // 2),
                                       self.pixelsPerRay, height)
                    pygame.draw.rect(self.screen, color, column)
            
            # Render flag
            for i, distance in enumerate(flagDistances):
                if not distance is None:
                    currPixel = i * self.pixelsPerRay

                    # Compute height of the column
                    if -0.1 < distance < 0.1:
                        height = self.windowSize[1]
                    else:
                        height = self.windowSize[1] / distance * self.distanceToProjection / FLAG_HEIGHT_DIV
                    
                    # Apply fisheye correction
                    height *= self.fisheyeCoefficients[i]

                    # Compute color of the column
                    colorCoeficient = distance / RENDER_DISTANCE
                    if colorCoeficient > 1.0:
                        colorCoeficient = 1.0
                    red = FLAG_COLOR[0] * (1.0 - colorCoeficient) + \
                          CEIL_COLOR[0] * colorCoeficient
                    green = FLAG_COLOR[1] * (1.0 - colorCoeficient) + \
                            CEIL_COLOR[1] * colorCoeficient
                    blue = FLAG_COLOR[2] * (1.0 - colorCoeficient) + \
                           CEIL_COLOR[2] * colorCoeficient
                    color = (red, green, blue)

                    # Draw the column
                    column = pygame.Rect(currPixel, self.windowSize[1] // 2 - (height // 2),
                                       self.pixelsPerRay, height)
                    pygame.draw.rect(self.screen, color, column)

            #
            # Draw UI
            #

            # Minimap
            if drawMinimap:
                # Draw walls on minimap
                self.minimap.fill(FLOOR_COLOR)
                for x, wall_column in enumerate(self.level.get_walls()):
                    for y, wall in enumerate(wall_column):
                        if wall:
                            rectSize = BLOCK_SIZE // MINIMAP_SIZE_DIV
                            rectX = x * rectSize
                            rectY = y * rectSize
                            rect = pygame.Rect(rectX, rectY, rectSize, rectSize)
                            pygame.draw.rect(self.minimap, WALL_COLOR, rect)
                
                # Draw flag on minimap
                x, y = self.level.get_flag_block()
                rectSize = BLOCK_SIZE // MINIMAP_SIZE_DIV
                rectX = x * rectSize
                rectY = y * rectSize
                rect = pygame.Rect(rectX, rectY, rectSize, rectSize)
                pygame.draw.rect(self.minimap, FLAG_COLOR, rect)
                
                # Draw player on minimap
                rectX = self.player.get_pos().x // MINIMAP_SIZE_DIV
                rectY = self.player.get_pos().y // MINIMAP_SIZE_DIV
                rectX -= MINIMAP_PLAYER_SIZE // 2
                rectY -= MINIMAP_PLAYER_SIZE // 2
                rect = pygame.Rect(rectX, rectY, MINIMAP_PLAYER_SIZE, MINIMAP_PLAYER_SIZE)
                pygame.draw.rect(self.minimap, MINIMAP_COLOR, rect)

                # Draw intersections (of rays that have been cast) on minimap
                for intersection in intersections:
                    if not intersection is None:
                        rectX = intersection.x // MINIMAP_SIZE_DIV
                        rectY = intersection.y // MINIMAP_SIZE_DIV
                        rect = pygame.Rect(rectX, rectY, 1, 1)
                        pygame.draw.rect(self.minimap, MINIMAP_COLOR, rect)
                
                # Blit minimap onto window
                self.screen.blit(self.minimap, (0, 0))

            # Fps
            fpsCount = ceil(clock.get_fps())
            fpsText = "fps: %d" % (fpsCount)
            color = TEXT_COLOR if fpsCount > (self.targetFps - 10) else MINIMAP_COLOR
            fpsSurface = self.font.render(fpsText, False, color)
            self.screen.blit(fpsSurface, (self.windowSize[0] - (7 * 10) - 8, 8))

            # Win screen
            if win:
                self.screen.blit(self.winScreen, (0, 0))
            
            # Timer
            timeText  = "time: %.2f s" % (timer / 1000)
            timeSurface = self.font.render(timeText, False, TEXT_COLOR)
            self.screen.blit(timeSurface, (self.windowSize[0] - (12 * 10) - 8, self.windowSize[1] - 16 - 8))
    
            #
            # Finish drawing 
            #

            pygame.display.flip()

            #
            # Time
            #

            if timerOn:
                timer += clock.get_time()
            
            clock.tick(self.targetFps)
