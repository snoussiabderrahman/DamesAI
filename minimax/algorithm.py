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


def alphabeta_with_hash(position, depth, color_player, alpha, beta, game):
    hash_key = calculate_zobrist_hash(position)

    # Vérifiez si la position a déjà été évaluée
    if hash_key in transposition_table:
        print("is existe")
        return transposition_table[hash_key] # Retournez l'évaluation précédemment stockée

    if depth == 0 or position.winner(game.turn) != None:
        return position.evaluate(color_player), position

    best_move = None
    for move in position.get_all_moves(position, color_player):
        evaluation = -alphabeta_with_hash(move, depth-1, CREAM if color_player == BLACK else BLACK, -beta, -alpha, game)[0]
        if evaluation > alpha:
            best_move = move
            alpha = evaluation
            if alpha >= beta:
                break  # Coupez l'arbre

    # Stockez l'évaluation dans la table de transposition
    transposition_table[hash_key] = (alpha, best_move)
    '''
    # Vous pourriez ici ajouter une logique pour gérer la taille de la table
    if len(transposition_table) > HASH_SIZE:
        # Éliminer une entrée, par exemple, la première ajoutée (pour simplifier)
        transposition_table.pop(next(iter(transposition_table)))
    '''
    return alpha, best_move 



# Alpha-béta avec ordonnancement *********************************************************

history_table = {}  # Dictionnaire pour stocker les évaluations des mouvements

def update_history(move, depth):
    if move not in history_table:
        history_table[move] = 0
    # Plus le coup est profond dans l'arbre, plus il est important
    history_table[move] += 2 ** depth  


def createsCaptureOpportunity(board, piece):
    """
    Vérifie si après un mouvement, une capture est imminente.
    """
    # Chercher tous les mouvements valides pour cette pièce
    valid_moves = board.get_all_moves(board, piece)
    
    # Si un des prochains mouvements permet une capture, cela crée une opportunité tactique
    for move, skip in valid_moves.items():
        if skip:  # Si un mouvement mène à une capture
            return True
    return False

# Récupérer les coups de capture uniquement pour Quiescence Search
def get_capture_moves(board, color):
    capture_moves = {}
    
    for piece in board.get_all_pieces(color):
        valid_moves = board.get_valid_moves(piece)
        for move, skip in valid_moves.items():
            if skip:  
                temp_board = deepcopy(board)
                temp_piece = temp_board.get_piece(piece.row, piece.col)
                new_board = board.simulate_move(temp_piece, move, temp_board, skip)
                capture_moves[new_board] = skip

    return capture_moves

def isTacticalMove(board, move, piece):
    """
    Vérifie si le coup est tactique.
    Un coup est tactique s'il implique une capture, une promotion ou une menace directe.
    """
    if not piece.is_pawn():
        return True

    # Vérifier les menaces de captures directes après ce coup
    if createsCaptureOpportunity(board, piece):
        return True  # Menace de capture future

    return False  # Sinon, ce n'est pas un coup tactique


# Fonction de Quiescence Search
def quiescenceSearch(board, alpha, beta, color_player, game):
    # Évaluer la position actuelle
    standPat = board.evaluate(color_player)

    # Beta cutoff
    if standPat >= beta:
        return beta

    # Mettre à jour alpha si l'évaluation est meilleure
    if standPat > alpha:
        alpha = standPat

    # Rechercher les coups tactiques uniquement (captures ou menaces)
    for piece in board.get_all_pieces(color_player):
        valid_moves = board.get_valid_moves(piece)
        for move, skip in valid_moves.items():
            if isTacticalMove(board, move, piece):
                # Simuler le coup
                new_board = deepcopy(board)
                new_board.move(piece, move[0], move[1])
                if skip:
                    new_board.remove(skip)
                
                # Recherche récursive
                score = -quiescenceSearch(new_board, -beta, -alpha, CREAM if color_player == BLACK else BLACK, game)

                # Beta cutoff
                if score >= beta:
                    return beta
                if score > alpha:
                    alpha = score

    return alpha

'''
#*********** Negamax with killer moves , ordering moves and quiescence search optimizations  ***********#
def NegaMax(position, depth, color_player, alpha, beta, game, killer_moves):

    if depth == 0:
        return quiescenceSearch(position, color_player, alpha, beta, game), position

    if position.winner(game.turn) is not None:  # Si le jeu est terminé
        return position.evaluate(color_player), position

    best_move = None
    moves = get_all_moves(position, color_player)

    # Triage des mouvements avec Killer Moves
    if depth in killer_moves:
        killer_move = killer_moves[depth]
        if killer_move in moves:
            moves.remove(killer_move)
            moves.insert(0, killer_move)  # Place le killer move en premier

    for move in moves:
        evaluation = -NegaMax(move, depth-1, CREAM if color_player == BLACK else BLACK, -beta, -alpha, game, killer_moves)[0]

        if evaluation > alpha:
            best_move = move
            alpha = evaluation

            if alpha >= beta:
                update_history(best_move, depth)
                break  # Coupure alpha-beta

    # Enregistrer le meilleur mouvement dans la table des killer moves
    if depth not in killer_moves:
        killer_moves[depth] = best_move
    else:
        if best_move != killer_moves[depth]:
            killer_moves[depth] = best_move

    return alpha, best_move
'''
#*********** Negamax with killer moves and ordering moves optimizations  ***********#
def NegaMax(position, depth, color_player, alpha, beta, game, killer_moves):

    if depth == 0 or position.winner(game.turn) is not None:
        return position.evaluate(color_player), position
    
    best_move = None
    moves = get_all_moves(position, color_player)

    # Triage des mouvements avec Killer Moves
    if depth in killer_moves:
        killer_move = killer_moves[depth]
        if killer_move in moves:
            moves.remove(killer_move)
            moves.insert(0, killer_move)  # Place le killer move en premier

    for move in moves:
        evaluation = -NegaMax(move, depth-1, CREAM if color_player == BLACK else BLACK, -beta, -alpha, game, killer_moves)[0]
        
        if evaluation > alpha:
            best_move = move
            alpha = evaluation
            
            if alpha >= beta:
                update_history(best_move, depth)  
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

