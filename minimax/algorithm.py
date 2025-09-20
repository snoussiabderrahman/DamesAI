from copy import deepcopy
import random
from checkers.constants import BLACK, CREAM, ROWS, COLS
import pygame

PIECE_TYPES = ['pawn', 'king']  # Types de pièces
NUM_PIECES = len(PIECE_TYPES) * 2  # Nombre de types de pièces (pour CREAM et BLACK)
HASH_SIZE = 2 ** 20  # Taille de la table de transposition

# Zobrist Hashing
zobrist_table = {}
for piece in ['black_pawn', 'black_king', 'cream_pawn', 'cream_king']:
    for row in range(ROWS):
        for col in range(COLS):
            zobrist_table[(piece, row, col)] = random.getrandbits(64)

# Transposition table
transposition_table = {}

def calculate_zobrist_hash(board):
    hash_key = 0
    for row in range(ROWS):
        for col in range(COLS):
            piece = board.get_piece(row, col)
            if piece != 0:
                piece_type = 'pawn' if piece.is_pawn() else 'king'  # Assurez-vous d'avoir une méthode pour vérifier le type de pièce
                color = 'black' if piece.color == BLACK else 'cream'
                piece_identifier = f"{color}_{piece_type}"
                hash_key ^= zobrist_table[(piece_identifier, row, col)]
    return hash_key

history_table = {}  # Dictionnaire pour stocker les évaluations des mouvements

def update_history(move, depth):
    if move not in history_table:
        history_table[move] = 0
    # Plus le coup est profond dans l'arbre, plus il est important
    history_table[move] += 2 ** depth  

# Récupérer les coups de capture uniquement pour Quiescence Search
def get_capture_moves(board, color):
    capture_moves = {}
    
    for piece in board.get_all_pieces(color):
        valid_moves = board.get_valid_moves(piece)
        for move, skip in valid_moves.items():
            if skip: # C'est un coup de capture
                temp_board = deepcopy(board)
                temp_piece = temp_board.get_piece(piece.row, piece.col)
                # simulate_move a été dépréciée car elle est dans la boucle de get_all_moves
                new_board = simulate_move(temp_piece, move, temp_board, skip)
                capture_moves[new_board] = skip

    # Assure que même dans la Q-search, on respecte la prise maximale obligatoire
    return extract_max_jumps(capture_moves)

#------------- FONCTION QUIESCENCE SEARCH -------------------#
def quiescenceSearch(board, alpha, beta, color_player):
    # Évalue la position actuelle "sans rien faire" (stand-pat)
    stand_pat_eval = board.evaluate(color_player)

    # Si l'évaluation actuelle est déjà meilleure que beta, on peut couper.
    # L'adversaire a déjà un meilleur coup ailleurs.
    if stand_pat_eval >= beta:
        return beta

    # Met à jour alpha avec la meilleure évaluation trouvée jusqu'ici.
    if alpha < stand_pat_eval:
        alpha = stand_pat_eval

    # On ne génère QUE les coups de capture pour cette position.
    capture_moves = get_capture_moves(board, color_player)

    # On applique la règle de la prise maximale aussi dans la Q-Search
    capture_moves = extract_max_jumps(capture_moves)

    for move_board in capture_moves.keys():
        # On fait un appel récursif pour la position après la capture
        score = -quiescenceSearch(move_board, -beta, -alpha, CREAM if color_player == BLACK else BLACK)

        # Si le score est meilleur que beta, on a trouvé une réfutation et on peut couper.
        if score >= beta:
            return beta
        
        # Si on a trouvé un meilleur coup, on met à jour alpha.
        if score > alpha:
            alpha = score

    return alpha

#*********** Negamax with killer moves and ordering moves optimizations  ***********#
def NegaMax(position, depth, color_player, alpha, beta, game, killer_moves, profiler):

    # === PROFILER: Incrémente le nombre de nœuds visités ===
    profiler.increment_nodes()

    if position.winner(game.turn) is not None:
        return position.evaluate(color_player), position # Le jeu est fini, retourne l'évaluation

    if depth == 0:
        # La recherche principale est terminée, on lance la recherche de quiétude
        # pour s'assurer que la position est "calme".
        q_eval = quiescenceSearch(position, alpha, beta, color_player)
        return q_eval, position
    
    best_move = None
    moves = get_all_moves(position, color_player)

    moves_list = list(get_all_moves(position, color_player).keys())
    # Sort moves based on history score in descending order
    moves_list.sort(key=lambda move: history_table.get(move, 0), reverse=True)

    # Prioritize the killer move by moving it to the front
    if depth in killer_moves:
        killer_move = killer_moves[depth]
        if killer_move in moves_list:
            moves_list.remove(killer_move)
            moves_list.insert(0, killer_move)

    for move in moves:
        evaluation = -NegaMax(move, depth-1, CREAM if color_player == BLACK else BLACK, -beta, -alpha, game, killer_moves, profiler)[0]
        
        if evaluation > alpha:
            best_move = move
            alpha = evaluation
            
            if alpha >= beta:
                #update_history(best_move, depth)  
                # Add a check to ensure best_move is not None
                # === PROFILER: Incrémente le compteur de coupures ===
                profiler.increment_cutoffs()
                if best_move is not None:
                    if depth not in killer_moves:
                        killer_moves[depth] = best_move
                    # (logic to store one or two killers)
                break  # Coupez l'arbre

    # Enregistrer le meilleur mouvement dans la table des killer moves
    if depth not in killer_moves:
        killer_moves[depth] = best_move
    else:
        if best_move != killer_moves[depth]:
            killer_moves[depth] = best_move

    return alpha, best_move


def get_all_moves(board, color):
    moves = {}

    for piece in board.get_all_pieces(color):
        valid_moves = board.get_valid_moves(piece)
        #print(valid_moves)
        for move, skip in valid_moves.items():
            temp_board = deepcopy(board)
            temp_piece = temp_board.get_piece(piece.row, piece.col)
            #print(temp_board)
            new_board = simulate_move(temp_piece, move, temp_board, skip)
            #print(skip)
            moves[new_board] = skip
    #print(moves)
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

def simulate_move(piece, move, board, skip):
    #print(board)
    board.move(piece, move[0], move[1])
    if skip:
        board.remove(skip)
    
    return board

