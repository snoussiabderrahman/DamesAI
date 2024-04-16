from copy import deepcopy
import pygame

CREAM = (255, 253, 208)
BLACK = (0, 0,0)

def minimax(position, depth, max_player, game):
    if depth == 0 or position.winner(game.turn) != None:
        return position.evaluate(), position
    
    if max_player:
        maxEval = float('-inf')
        best_move = None
        for move in get_all_moves(position, BLACK, game):
            evaluation = minimax(move, depth-1, False, game)[0]
            maxEval = max(maxEval, evaluation)
            if maxEval == evaluation:
                best_move = move
        
        return maxEval, best_move
    else:
        minEval = float('inf')
        best_move = None
        for move in get_all_moves(position, CREAM, game):
            evaluation = minimax(move, depth-1, True, game)[0]
            minEval = min(minEval, evaluation)
            if minEval == evaluation:
                best_move = move
        
        return minEval, best_move

def alphabeta(position, depth, color_player, alpha, beta, game):
    if depth == 0 or position.winner(game.turn) != None:
        return position.evaluate(color_player), position
    
    best_move = None
    for move in get_all_moves(position, BLACK if color_player == BLACK else CREAM, game):
        evaluation = -alphabeta(move, depth-1, CREAM if color_player == BLACK else BLACK, -beta, -alpha, game)[0]
        if evaluation > alpha:
            best_move = move
            alpha = evaluation
            if alpha >= beta:
                return beta, best_move

    return alpha, best_move
 

def simulate_move(piece, move, board, game, skip):
    board.move(piece, move[0], move[1])
    if skip:
        board.remove(skip)

    return board

def get_all_moves(board, color, game):
    moves = {}

    for piece in board.get_all_pieces(color):
        valid_moves = board.get_valid_moves(piece)
        for move, skip in valid_moves.items():
            temp_board = deepcopy(board)
            temp_piece = temp_board.get_piece(piece.row, piece.col)
            new_board = simulate_move(temp_piece, move, temp_board, game, skip)
            moves[new_board] = skip
    
    moves = extract_max_jumps(moves)

    return moves

def extract_max_jumps(moves):
    if moves:
        max_jumps = max(len(skipped) for skipped in moves.values())  
        max_jump_moves = {move: skipped for move, skipped in moves.items() if len(skipped) == max_jumps}
        return max_jump_moves
    else:
        return {}



def draw_moves(game, board, piece):
    valid_moves = board.get_valid_moves(piece)
    board.draw(game.win)
    pygame.draw.circle(game.win, (0,255,0), (piece.x, piece.y), 50, 5)
    game.draw_valid_moves(valid_moves.keys())
    pygame.display.update()
    #pygame.time.delay(100)




