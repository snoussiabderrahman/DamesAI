import pygame
from checkers.constants import WIDTH, HEIGHT, SQUARE_SIZE, BLACK
from checkers.game import Game
from minimax.algorithm import NegaMax
import time

FPS = 60

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
    while run:
        clock.tick(FPS)

        if game.winner(game.turn) != None:
            print(game.winner(game.turn))
            run = False
        
    
        if game.turn == BLACK:
            value, new_board = NegaMax(game.get_board(), 6, BLACK,float("-inf"), float("inf"), game, killer_moves)
            game.ai_move(new_board)
        

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
