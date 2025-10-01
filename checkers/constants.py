# checkers/constants.py

import pygame
import os
import sys

pygame.font.init()

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    return os.path.join(base_path, relative_path)

# === Dimensions de la fenêtre et de la barre latérale ===
SIDEBAR_WIDTH = 300
BOARD_WIDTH = 700
WIDTH, HEIGHT = BOARD_WIDTH + SIDEBAR_WIDTH, BOARD_WIDTH  # Nouvelle largeur : 1000x700
SEPARATOR_WIDTH = 4
# ===================================================================

# === Scores pour les états terminaux du jeu ===
WIN_SCORE = 10000
LOSS_SCORE = -10000
DRAW_SCORE = 0

ROWS, COLS = 8, 8
SQUARE_SIZE = BOARD_WIDTH // COLS # Le carré est basé sur la taille du plateau, pas de la fenêtre

# rgb
CREAM = (255, 253, 208)
BLACK = (0, 0, 0)
BROWN = (150, 77, 55)
BLUE = (0, 0, 255)
GREY = (128, 128, 128)
WHITE = (255, 255, 255)
RED = (200, 0, 0)
GREEN = (0, 200, 0)
DARK_GREY = (40, 40, 40)
AI_GREEN = (34, 177, 76)
AI_BLUE = (112, 146, 190)
AI_GREY = (180, 180, 180)

# Polices pour le texte
FONT_MENU = pygame.font.SysFont("comicsans", 70)
FONT_SIDEBAR_TITLE = pygame.font.SysFont("comicsans", 30)
FONT_SIDEBAR_BODY = pygame.font.SysFont("comicsans", 20)
FONT_COORDS = pygame.font.SysFont("sans", 20)
FONT_COPYRIGHT = pygame.font.SysFont("sans", 14)
FONT_AI_STATS_LABEL = pygame.font.SysFont("consolas", 20, bold=True)
FONT_AI_STATS_VALUE = pygame.font.SysFont("consolas", 20)
# ==================================

CROWN_PATH = resource_path('assets/crown.png')
CROWN = pygame.transform.scale(pygame.image.load(CROWN_PATH), (44, 25))

# Chargez l'image de fond du menu
BACKGROUND_PATH = resource_path('assets/background.jpg')
MENU_BACKGROUND = pygame.transform.scale(pygame.image.load(BACKGROUND_PATH), (WIDTH, HEIGHT))
# =====================