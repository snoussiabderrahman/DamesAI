# main.py

import pygame
from checkers.constants import *
from checkers.game import Game
from minimax.algorithm import NegaMax, transposition_table
from minimax.profiler import AIProfiler
import sys
import threading
from copy import deepcopy

# --- Configuration de la fenêtre et des polices ---
pygame.display.set_caption('DamesAI')
WIN = pygame.display.set_mode((WIDTH, HEIGHT))

FPS = 60
SEARCH_DEPTH = 10

# --- Fonctions d'aide pour le dessin ---
def draw_text(surface, text, font, color, x, y, center=False):
    """Fonction générique pour dessiner du texte."""
    text_surface = font.render(text, True, color)
    text_rect = text_surface.get_rect()
    if center:
        text_rect.center = (x, y)
    else:
        text_rect.topleft = (x, y)
    surface.blit(text_surface, text_rect)

def draw_button(surface, rect, text, font, color_bg, color_text):
    """Dessine un bouton simple."""
    pygame.draw.rect(surface, color_bg, rect, border_radius=10)
    draw_text(surface, text, font, color_text, rect.centerx, rect.centery, center=True)

def draw_sidebar(surface, game):
    """Dessine la barre latérale avec les scores et les boutons."""
    sidebar_rect = pygame.Rect(BOARD_WIDTH, 0, SIDEBAR_WIDTH, HEIGHT)
    pygame.draw.rect(surface, BROWN, sidebar_rect)

    separator_rect = pygame.Rect(BOARD_WIDTH - SEPARATOR_WIDTH, 0, SEPARATOR_WIDTH, HEIGHT)
    pygame.draw.rect(surface, DARK_GREY, separator_rect)

    # Titre du score
    draw_text(surface, "Score", FONT_SIDEBAR_TITLE, CREAM, BOARD_WIDTH + 150, 50, center=True)

    # Scores
    draw_text(surface, f"Cream (You): {game.cream_wins}", FONT_SIDEBAR_BODY, WHITE, BOARD_WIDTH + 150, 120, center=True)
    draw_text(surface, f"Black (AI): {game.black_wins}", FONT_SIDEBAR_BODY, WHITE, BOARD_WIDTH + 150, 170, center=True)

    # Affichage du gagnant / message de l'IA
    if game.game_over:
        draw_text(surface, "Game Over!", FONT_SIDEBAR_TITLE, RED, BOARD_WIDTH + 150, 300, center=True)
        draw_text(surface, game.winner_message, FONT_SIDEBAR_BODY, CREAM, BOARD_WIDTH + 150, 350, center=True)
    elif game.ai_is_thinking:
        draw_text(surface, "AI is thinking...", FONT_SIDEBAR_BODY, CREAM, BOARD_WIDTH + 150, 450, center=True)

    # On déplace le bouton Restart un peu plus haut
    restart_btn_rect = pygame.Rect(BOARD_WIDTH + 50, HEIGHT - 170, SIDEBAR_WIDTH - 100, 50)
    draw_button(surface, restart_btn_rect, "Restart", FONT_SIDEBAR_BODY, GREEN, BLACK)

    # On ajoute le bouton "Back to Menu" en dessous
    menu_btn_rect = pygame.Rect(BOARD_WIDTH + 50, HEIGHT - 100, SIDEBAR_WIDTH - 100, 50)
    draw_button(surface, menu_btn_rect, "Back to Menu", FONT_SIDEBAR_BODY, GREY, BLACK)
    
    return restart_btn_rect, menu_btn_rect


def draw_board_coordinates(surface):
    """
    Dessine les coordonnées (a-h, 1-8) autour du plateau.
    Version mise à jour pour un alignement dans les coins.
    """
    # Une petite marge pour ne pas coller le texte aux bords
    padding = 5 
    for i in range(8):
        # --- Nombres (1-8) : dans le coin SUPÉRIEUR GAUCHE de chaque case de la première colonne ---
        # On calcule la coordonnée Y en haut de la case `i` + un petit padding
        y_coord = (i * SQUARE_SIZE) + padding
        # L'argument `center=False` est crucial, il aligne le texte par son coin supérieur gauche
        draw_text(surface, str(8 - i), FONT_COORDS, DARK_GREY, padding, y_coord, center=False)
        
        # --- Lettres (a-h) : dans le coin INFÉRIEUR GAUCHE de chaque case de la dernière rangée ---
        # On calcule la coordonnée X à gauche de la case `i` + un petit padding
        x_coord = (i * SQUARE_SIZE) + padding
        # La coordonnée Y est calculée à partir du bas de l'écran MOINS la hauteur de la police
        # pour que le bas du texte soit aligné avec le bas du plateau.
        y_coord_bottom = HEIGHT - FONT_COORDS.get_height() - padding
        draw_text(surface, chr(ord('a') + i), FONT_COORDS, DARK_GREY, x_coord, y_coord_bottom, center=False)

# --- Fonction wrapper pour le calcul de l'IA ---
def run_ai_calculation(board_to_search, killer_moves, profiler, result_container):
    """
    Cette fonction sera exécutée dans un thread séparé sur une COPIE du plateau.
    """
    profiler.reset()
    profiler.start_timer()
    
    transposition_table.clear()
    
    # On utilise 'board_to_search' et on a retiré 'game' (qui était None)
    value, best_move_data = NegaMax(board_to_search, SEARCH_DEPTH, BLACK, float("-inf"), float("inf"), killer_moves, profiler)
    # =======================================================================
    
    profiler.stop_timer()
    profiler.set_tt_size(len(transposition_table))
    profiler.display_results(SEARCH_DEPTH, value, best_move_data)
    
    result_container.append(best_move_data)

# --- Boucle Principale ---
def main():
    run = True
    clock = pygame.time.Clock()
    game_state = "MAIN_MENU"  # États possibles: MAIN_MENU, RULES, PLAYING
    
    # Initialisation du jeu et de l'IA
    game = Game(WIN)
    profiler = AIProfiler()
    killer_moves = {}

    # === NOUVEAU : Variables pour gérer le thread de l'IA ===
    ai_thread = None
    ai_result = []

    # Définition des rectangles des boutons du menu
    start_btn = pygame.Rect(WIDTH//2 - 150, 250, 300, 70)
    rules_btn = pygame.Rect(WIDTH//2 - 150, 350, 300, 70)
    exit_btn = pygame.Rect(WIDTH//2 - 150, 450, 300, 70)
    back_btn = pygame.Rect(WIDTH//2 - 100, HEIGHT - 120, 200, 60)
    restart_btn = pygame.Rect(0,0,0,0) # Sera défini dans la boucle

    while run:
        clock.tick(FPS)
        mouse_pos = pygame.mouse.get_pos()

        # Gestion des événements
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False

            if event.type == pygame.MOUSEBUTTONDOWN:
                if game_state == "MAIN_MENU":
                    if start_btn.collidepoint(mouse_pos):
                        game_state = "PLAYING"
                        game.reset()
                    if rules_btn.collidepoint(mouse_pos):
                        game_state = "RULES"
                    if exit_btn.collidepoint(mouse_pos):
                        run = False
                elif game_state == "RULES":
                    if back_btn.collidepoint(mouse_pos):
                        game_state = "MAIN_MENU"
                elif game_state == "PLAYING":
                    if restart_btn.collidepoint(mouse_pos):
                        game.reset()
                    elif menu_btn.collidepoint(mouse_pos):
                        game_state = "MAIN_MENU"
                    elif not game.is_animating() and not game.game_over:
                        row = mouse_pos[1] // SQUARE_SIZE
                        col = mouse_pos[0] // SQUARE_SIZE
                        if col < 8: # S'assurer que le clic est sur le plateau
                            game.select(row, col)

        # === NOUVELLE LOGIQUE DE JEU NON-BLOQUANTE POUR L'IA ===
        if game_state == "PLAYING" and game.turn == BLACK and not game.is_animating() and not game.game_over:
            if ai_thread is None:
                game.ai_is_thinking = True
                ai_result = []
                
                # === S'assurer de copier le PLATEAU, pas le JEU ===
                board_copy = deepcopy(game.get_board())

                # On passe la COPIE DU PLATEAU au thread
                ai_thread = threading.Thread(target=run_ai_calculation, args=(board_copy, killer_moves, profiler, ai_result))
                ai_thread.start()
            elif not ai_thread.is_alive():
                game.ai_is_thinking = False
                if ai_result:
                    best_move_data = ai_result[0]
                    game.ai_move(best_move_data)
                else: # L'IA n'a pas de coup
                    game.update_winner()
                ai_thread = None # Réinitialiser le thread pour le prochain tour
        
        # Logique de dessin
        if game_state == "MAIN_MENU":
            WIN.blit(MENU_BACKGROUND, (0, 0))
            draw_text(WIN, "DamesAI", FONT_MENU, WHITE, WIDTH//2, 100, center=True)
            draw_button(WIN, start_btn, "Start Game", FONT_SIDEBAR_TITLE, GREEN, BLACK)
            draw_button(WIN, rules_btn, "Rules", FONT_SIDEBAR_TITLE, BLUE, WHITE)
            draw_button(WIN, exit_btn, "Exit", FONT_SIDEBAR_TITLE, RED, WHITE)
        elif game_state == "RULES":
            WIN.fill(BROWN)
            draw_text(WIN, "Rules of Spanish Checkers", FONT_MENU, CREAM, WIDTH//2, 80, center=True)
            draw_text(WIN, "- Capture is mandatory.", FONT_SIDEBAR_BODY, WHITE, 100, 200)
            draw_text(WIN, "- You must take the path that captures the MOST pieces.", FONT_SIDEBAR_BODY, WHITE, 100, 250)
            draw_text(WIN, "- Kings (Damas) can move and capture across long diagonals.", FONT_SIDEBAR_BODY, WHITE, 100, 300)
            draw_button(WIN, back_btn, "Back to Menu", FONT_SIDEBAR_BODY, GREY, BLACK)
        elif game_state == "PLAYING":
            WIN.fill(BROWN)
            game.update() # Gère l'animation et le dessin du plateau
            restart_btn, menu_btn = draw_sidebar(WIN, game)
            draw_board_coordinates(WIN)
            
            # Vérifier la condition de victoire
            if not game.game_over and not game.is_animating():
                game.update_winner()

        pygame.display.update()

    pygame.quit()
    sys.exit()

if __name__ == '__main__':
    main()