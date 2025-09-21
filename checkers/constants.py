import pygame
import os
import sys

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    return os.path.join(base_path, relative_path)

WIDTH, HEIGHT = 700, 700
ROWS, COLS = 8, 8
SQUARE_SIZE = WIDTH//COLS

# rgb
CREAM = (255, 253, 208)
BLACK = (0, 0,0)
BROWN = (150, 77, 55)
BLUE = (0, 0, 255)
GREY = (128,128,128)

CROWN_PATH = resource_path('assets/crown.png')
CROWN = pygame.transform.scale(pygame.image.load(CROWN_PATH), (44, 25))
