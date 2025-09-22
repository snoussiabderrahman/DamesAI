# checkers/constants.py

import pygame
import os
import sys

# Initialiser pygame.font au début est une bonne pratique
pygame.font.init()

def resource_path(relative_path):
    # ... (cette fonction ne change pas) ...
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    return os.path.join(base_path, relative_path)

# === MODIFICATIONS : Dimensions de la fenêtre et de la barre latérale ===
SIDEBAR_WIDTH = 300
BOARD_WIDTH = 700
WIDTH, HEIGHT = BOARD_WIDTH + SIDEBAR_WIDTH, BOARD_WIDTH  # Nouvelle largeur : 1000x700
SEPARATOR_WIDTH = 4
# ===================================================================

ROWS, COLS = 8, 8
SQUARE_SIZE = BOARD_WIDTH // COLS # Le carré est basé sur la taille du plateau, pas de la fenêtre

# === NOUVELLES COULEURS ET POLICES ===
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

# Polices pour le texte
FONT_MENU = pygame.font.SysFont("comicsans", 70)
FONT_SIDEBAR_TITLE = pygame.font.SysFont("comicsans", 40)
FONT_SIDEBAR_BODY = pygame.font.SysFont("comicsans", 30)
FONT_COORDS = pygame.font.SysFont("sans", 20)
# ==================================

# === NOUVEAUX ASSETS ===
CROWN_PATH = resource_path('assets/crown.png')
CROWN = pygame.transform.scale(pygame.image.load(CROWN_PATH), (44, 25))

# Chargez l'image de fond du menu
BACKGROUND_PATH = resource_path('assets/background.jpg')
MENU_BACKGROUND = pygame.transform.scale(pygame.image.load(BACKGROUND_PATH), (WIDTH, HEIGHT))
# =====================