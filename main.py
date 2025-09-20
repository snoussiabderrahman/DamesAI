import pygame
from checkers.constants import WIDTH, HEIGHT, SQUARE_SIZE, BLACK
from checkers.game import Game
from minimax.algorithm import NegaMax
from minimax.profiler import AIProfiler
import time

FPS = 60
SEARCH_DEPTH = 5

WIN = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption('Checkers')

def get_row_col_from_mouse(pos):
    x, y = pos
    row = y // SQUARE_SIZE
    col = x // SQUARE_SIZE
    return row, col

def main():
    run = True
    clock = pygame.time.Clock()
    game = Game(WIN)
    killer_moves = {}
    profiler = AIProfiler()

    while run:
        clock.tick(FPS)

        if game.winner(game.turn) != None:
            print(game.winner(game.turn))
            run = False

    
        if game.turn == BLACK:
            # 1. Réinitialisez et démarrez le chronomètre
            profiler.reset()
            profiler.start_timer()

            # 2. Appelez NegaMax en passant l'objet profiler
            value, best_move_data = NegaMax(game.get_board(), SEARCH_DEPTH, BLACK, float("-inf"), float("inf"), game, killer_moves, profiler)
            
            # 3. Arrêtez le chronomètre
            profiler.stop_timer()

            # 4. Affichez les résultats
            profiler.display_results(SEARCH_DEPTH, value, best_move_data)

            # Si un mouvement a été trouvé, exécutez-le
            if best_move_data:
                game.ai_move(best_move_data)
            else:
                print("AI could not find a valid move.")
        

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False

            if event.type == pygame.MOUSEBUTTONDOWN:
                pos = pygame.mouse.get_pos()
                row, col = get_row_col_from_mouse(pos)
                game.select(row, col)
            
        game.update()
        time.sleep(.1)
    
    pygame.quit()

main()
