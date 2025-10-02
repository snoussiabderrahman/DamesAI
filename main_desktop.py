# main.py

import pygame
from checkers.constants import *
from checkers.game import Game
from minimax.algorithm import NegaMax, transposition_table, SEARCH_DEPTH
from minimax.profiler import AIProfiler
import sys
import threading
from copy import deepcopy

# --- Configuration de la fenêtre et des polices ---
pygame.display.set_caption('DamesAI')
WIN = pygame.display.set_mode((WIDTH, HEIGHT))

FPS = 60


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

    # === Section pour l'analyse de l'IA  ===
    ai_analysis_y_start = 0
    
    # Position de départ pour les étiquettes et les barres
    label_x = BOARD_WIDTH + 20
    bar_x = BOARD_WIDTH + 100
    value_x = BOARD_WIDTH + 130
    bar_size = (16, 14)

    # 1. Profondeur (Depth)
    y_depth = ai_analysis_y_start + 20
    draw_text(surface, "DEPTH", FONT_AI_STATS_LABEL, AI_GREEN, label_x, y_depth)
    pygame.draw.rect(surface, AI_GREEN, (bar_x, y_depth, bar_size[0], bar_size[1]))
    draw_text(surface, str(game.last_ai_depth), FONT_AI_STATS_VALUE, AI_GREEN, value_x, y_depth)

    # 2. Score
    y_score = y_depth + 20
    draw_text(surface, "SCORE", FONT_AI_STATS_LABEL, AI_BLUE, label_x, y_score)
    pygame.draw.rect(surface, AI_BLUE, (bar_x, y_score, bar_size[0], bar_size[1]))
    
    score_text = ""
    score_val = game.last_ai_score

    # On vérifie si le score est un score de victoire/défaite certain
    if score_val > WIN_SCORE / 2:
        # Calcul du nombre de demi-coups écoulés depuis l'analyse
        plies_elapsed = game.move_counter - game.calculation_move_counter
        # Calcul du nombre de demi-coups restants
        current_plies = game.last_ai_plies_to_win - plies_elapsed
        
        score_text = f"win in {current_plies}"

    elif score_val < LOSS_SCORE / 2:
        plies_elapsed = game.move_counter - game.calculation_move_counter
        current_plies = game.last_ai_plies_to_win - plies_elapsed

        score_text = f"loss in {current_plies}"
    else:
        # Sinon, c'est un score heuristique normal
        score_text = f"{score_val:.2f}"
    
    draw_text(surface, score_text, FONT_AI_STATS_VALUE, AI_BLUE, value_x, y_score)
    # ----------------------------------------------------------------

    # 3. Temps (Time)
    y_time = y_score + 20
    draw_text(surface, "TIME", FONT_AI_STATS_LABEL, AI_GREY, label_x, y_time)
    pygame.draw.rect(surface, AI_GREY, (bar_x, y_time, bar_size[0], bar_size[1]))
    time_s = float(game.last_ai_time)
    draw_text(surface, f"{time_s:.2f}s", FONT_AI_STATS_VALUE, AI_GREY, value_x, y_time)
    # =======================================================================

    # Scores (maintenant dynamiques en fonction du choix du joueur)
    you_color_str = "Cream" if game.player_color == CREAM else "Black"
    ai_color_str = "Black" if game.player_color == CREAM else "Cream"
    y_you = 120
    draw_text(surface, 
              f"{you_color_str} (You): {game.cream_wins if you_color_str == 'Cream' else game.black_wins}", 
              FONT_SIDEBAR_BODY, CREAM if you_color_str == "Cream" else BLACK, BOARD_WIDTH + 150, y_you, center=True)
    y_ai = y_you + 30
    draw_text(surface, 
              f"{ai_color_str} (AI): {game.black_wins if ai_color_str == 'Black' else game.cream_wins}", 
              FONT_SIDEBAR_BODY, BLACK if ai_color_str == "Black" else CREAM, BOARD_WIDTH + 150, y_ai, center=True)
    y_draw = y_ai + 30
    draw_text(surface, f"Draws: {game.draws}", FONT_SIDEBAR_BODY, WHITE, BOARD_WIDTH + 150, y_draw, center=True)

    # === Bouton "Undo Move" ===
    y_undo = y_draw + 45
    undo_btn_rect = pygame.Rect(BOARD_WIDTH + 50, y_undo, SIDEBAR_WIDTH - 100, 40)
    
    # Le bouton est actif si c'est au tour du joueur, que le jeu n'est pas fini,
    # qu'aucune animation n'est en cours, et qu'il y a un coup à annuler.
    is_undo_possible = (game.turn == game.player_color and 
                        not game.game_over and 
                        not game.is_animating() and 
                        len(game.game_state_history) > 1)
                        
    undo_bg_color = GREEN if is_undo_possible else GREY
    draw_button(surface, undo_btn_rect, "Undo Move", FONT_SIDEBAR_BODY, undo_bg_color, BLACK)
    # ===================================================================

    # === Section pour le choix de la couleur ===
    draw_text(surface, "Play As:", FONT_SIDEBAR_TITLE, WHITE, BOARD_WIDTH + 150, 300, center=True)

    # Bouton de choix "Cream"
    cream_choice_rect = pygame.Rect(BOARD_WIDTH + 25, 340, 120, 40)
    cream_bg = GREEN if game.player_color == CREAM else GREY
    draw_button(surface, cream_choice_rect, "Cream", FONT_SIDEBAR_BODY, cream_bg, CREAM)

    # Bouton de choix "Black"
    black_choice_rect = pygame.Rect(BOARD_WIDTH + SIDEBAR_WIDTH - 145, 340, 120, 40)
    black_bg = GREEN if game.player_color == BLACK else GREY
    draw_button(surface, black_choice_rect, "Black", FONT_SIDEBAR_BODY, black_bg, BLACK)

    # Affichage du gagnant / message de l'IA
    if game.game_over:
        draw_text(surface, "Game Over!", FONT_SIDEBAR_TITLE, RED, BOARD_WIDTH + 150, 425, center=True)
        draw_text(surface, game.winner_message, FONT_SIDEBAR_BODY, CREAM, BOARD_WIDTH + 150, 475, center=True)
    elif game.ai_is_thinking:
        draw_text(surface, "AI is thinking...", FONT_SIDEBAR_BODY, CREAM, BOARD_WIDTH + 150, 450, center=True)

    # Boutons du bas
    restart_btn_rect = pygame.Rect(BOARD_WIDTH + 50, HEIGHT - 170, SIDEBAR_WIDTH - 100, 50)
    draw_button(surface, restart_btn_rect, "Restart", FONT_SIDEBAR_BODY, GREEN, BLACK)
    menu_btn_rect = pygame.Rect(BOARD_WIDTH + 50, HEIGHT - 100, SIDEBAR_WIDTH - 100, 50)
    draw_button(surface, menu_btn_rect, "Back to Menu", FONT_SIDEBAR_BODY, GREY, BLACK)
    
    return restart_btn_rect, menu_btn_rect, cream_choice_rect, black_choice_rect, undo_btn_rect


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
def run_ai_calculation(board_to_search, ai_color, killer_moves, profiler, result_container, position_history, moves_since_capture):
    """
    Cette fonction sera exécutée dans un thread séparé sur une COPIE du plateau.
    """
    #profiler.reset()
    #profiler.start_timer()
    transposition_table.clear()
    
    # Lancer la recherche NegaMax
    value, best_move_data = NegaMax(board_to_search, SEARCH_DEPTH, ai_color, float("-inf"), float("inf"), killer_moves, profiler, position_history, moves_since_capture)
    
    #profiler.stop_timer()
    #profiler.set_tt_size(len(transposition_table))
    #profiler.display_results(SEARCH_DEPTH, value, best_move_data)
    result_container.append((value, best_move_data))

# --- Boucle Principale ---
def main():
    run = True
    clock = pygame.time.Clock()
    game_state = "MAIN_MENU"  # États possibles: MAIN_MENU, RULES, PLAYING
    
    # Initialisation du jeu et de l'IA
    game = Game(WIN)
    profiler = AIProfiler()
    killer_moves = {}

    # === Variables pour gérer le thread de l'IA ===
    ai_thread = None
    ai_result = []

    # Définition des rectangles des boutons du menu
    start_btn = pygame.Rect(WIDTH//2 - 150, 250, 300, 70)
    rules_btn = pygame.Rect(WIDTH//2 - 150, 350, 300, 70)
    exit_btn = pygame.Rect(WIDTH//2 - 150, 450, 300, 70)
    back_btn = pygame.Rect(WIDTH//2 - 100, HEIGHT - 120, 200, 60)
    restart_btn, menu_btn, cream_choice_btn, black_choice_btn, undo_btn = [pygame.Rect(0,0,0,0)] * 5

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
                    elif cream_choice_btn.collidepoint(mouse_pos):
                        game.set_player_color(CREAM)
                    elif black_choice_btn.collidepoint(mouse_pos):
                        game.set_player_color(BLACK)

                    # === Gérer le clic sur le bouton Undo ===
                    elif undo_btn.collidepoint(mouse_pos):
                        # On vérifie à nouveau que l'action est possible
                        if (game.turn == game.player_color and 
                            not game.game_over and 
                            not game.is_animating() and 
                            len(game.game_state_history) > 0):
                            game.undo_move()
                    elif not game.is_animating() and not game.game_over:
                        row = mouse_pos[1] // SQUARE_SIZE
                        col = mouse_pos[0] // SQUARE_SIZE
                        if col < 8: # S'assurer que le clic est sur le plateau
                            game.select(row, col)

        # === LOGIQUE DE JEU NON-BLOQUANTE POUR L'IA ===
        # Déterminer la couleur de l'IA
        ai_color = BLACK if game.player_color == CREAM else CREAM

        # L'IA joue si c'est son tour
        if game_state == "PLAYING" and game.turn == ai_color and not game.is_animating() and not game.game_over:
            if ai_thread is None:
                game.ai_is_thinking = True
                ai_result = []
                board_copy = deepcopy(game.get_board())
                
                profiler.reset()
                profiler.start_timer()
                
                ai_thread = threading.Thread(target=run_ai_calculation, args=(
                    board_copy, ai_color, killer_moves, profiler, ai_result, 
                    game.position_history.copy(), game.moves_since_capture
                ))
                ai_thread.start()
            
            elif not ai_thread.is_alive():
                game.ai_is_thinking = False

                # === Arrêter le profiler et stocker les résultats ===
                profiler.stop_timer()
                profiler.set_tt_size(len(transposition_table))

                if ai_result:
                    # On récupère le score ET le coup
                    value, best_move_data = ai_result[0]
                    
                    game.last_ai_depth = SEARCH_DEPTH
                    game.last_ai_score = value # On garde le score brut pour la logique
                    game.last_ai_time = profiler.total_time
                    
                    # Si c'est un score de victoire, on stocke les plies et le moment
                    if value > WIN_SCORE / 2:
                        game.last_ai_plies_to_win = WIN_SCORE - value
                        game.calculation_move_counter = game.move_counter
                    elif value < LOSS_SCORE / 2:
                        game.last_ai_plies_to_win = value - LOSS_SCORE
                        game.calculation_move_counter = game.move_counter

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
            # REMPLACEZ "Votre Nom Prénom" par votre vrai nom !
            copyright_text = "© 2025 Votre SNOUSSI ABDERRAHMANE. All rights reserved."
            draw_text(WIN, copyright_text, FONT_COPYRIGHT, WHITE, WIDTH//2, HEIGHT - 20, center=True)
        elif game_state == "RULES":
            WIN.fill(BROWN)
            draw_text(WIN, "Rules of Spanish Checkers", FONT_MENU, CREAM, WIDTH//2, 80, center=True)
            draw_text(WIN, "- Capture is mandatory.", FONT_SIDEBAR_BODY, WHITE, 100, 200)
            draw_text(WIN, "- You must take the path that captures the MOST pieces.", FONT_SIDEBAR_BODY, WHITE, 100, 250)
            draw_text(WIN, "- Kings (Damas) can move and capture across long diagonals.", FONT_SIDEBAR_BODY, WHITE, 100, 300)
            draw_button(WIN, back_btn, "Back to Menu", FONT_SIDEBAR_BODY, GREY, BLACK)
        elif game_state == "PLAYING":
            WIN.fill(BROWN)
            game.update() 

            ## Dessiner le plateau et les pièces
            restart_btn, menu_btn, cream_choice_btn, black_choice_btn, undo_btn = draw_sidebar(WIN, game)
            draw_board_coordinates(WIN)
            
            # Vérifier la condition de victoire
            if not game.game_over and not game.is_animating():
                game.update_winner()

        pygame.display.update()

    pygame.quit()
    sys.exit()

main()