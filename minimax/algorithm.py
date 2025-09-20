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

#------------- FONCTION QUIESCENCE SEARCH -------------------#
# minimax/algorithm.py

# ... (les autres fonctions comme get_possible_moves, get_capture_moves, etc., restent les mêmes) ...

def quiescenceSearch(board, alpha, beta, color_player, profiler):
    """
    Recherche de quiétude qui utilise maintenant le pattern Make/Undo.
    Elle n'explore que les coups de capture.
    """
    profiler.increment_nodes()

    stand_pat_eval = board.evaluate(color_player)

    if stand_pat_eval >= beta:
        return beta

    if alpha < stand_pat_eval:
        alpha = stand_pat_eval

    # --- NOUVELLE LOGIQUE POUR OBTENIR ET PARCOURIR LES COUPS ---
    # 1. Obtenir les coups de capture possibles
    capture_moves_dict = get_capture_moves(board, color_player)
    
    # 2. Transformer le dictionnaire en une liste plate de descriptions de coups
    capture_moves_list = []
    for piece, moves in capture_moves_dict.items():
        for move, skipped in moves.items():
            capture_moves_list.append((piece, move, skipped))
    
    # 3. Parcourir les descriptions de coups (comme dans NegaMax)
    for move_data in capture_moves_list:
        piece, (end_row, end_col), skipped_pieces = move_data
        start_row, start_col = piece.row, piece.col

        # --- FAIRE LE COUP (MAKE MOVE) ---
        removed = board.remove_and_get_skipped(skipped_pieces)
        was_promoted = board.make_move(piece, end_row, end_col)
        
        # Appel récursif (on passe le même objet 'board')
        score = -quiescenceSearch(board, -beta, -alpha, CREAM if color_player == BLACK else BLACK, profiler)
        
        # --- DÉFAIRE LE COUP (UNDO MOVE) ---
        board.undo_move(piece, start_row, start_col, was_promoted)
        board.restore_skipped(removed)
        
        if score >= beta:
            return beta
        
        if score > alpha:
            alpha = score
            
    return alpha

def NegaMax(position, depth, color_player, alpha, beta, game, killer_moves, profiler):
    profiler.increment_nodes()

    if position.winner(game.turn) is not None:
        return position.evaluate(color_player), None

    if depth == 0:
        # === CORRECTION : On passe le profiler à la Q-Search ===
        q_eval = quiescenceSearch(position, alpha, beta, color_player, profiler)
        return q_eval, None
    
    best_move_data = None
    possible_moves = get_possible_moves(position, color_player)
    
    # (Logique de tri des mouvements)

    for move_data in possible_moves:
        piece, (end_row, end_col), skipped_pieces = move_data
        start_row, start_col = piece.row, piece.col

        # --- FAIRE LE COUP (MAKE MOVE) ---
        removed = position.remove_and_get_skipped(skipped_pieces)
        was_promoted = position.make_move(piece, end_row, end_col)
        
        # Appel récursif
        evaluation = -NegaMax(position, depth - 1, CREAM if color_player == BLACK else BLACK, -beta, -alpha, game, killer_moves, profiler)[0]
        
        # --- DÉFAIRE LE COUP (UNDO MOVE) ---
        position.undo_move(piece, start_row, start_col, was_promoted)
        position.restore_skipped(removed)
        
        if evaluation > alpha:
            alpha = evaluation
            best_move_data = move_data
            
            if alpha >= beta:
                profiler.increment_cutoffs()
                # (Logique Killer moves)
                break
    
    return alpha, best_move_data

def get_possible_moves(board, color):
    """
    Génère une liste de tous les coups possibles pour une couleur donnée.
    Ne retourne pas de nouveaux plateaux, mais des tuples décrivant les coups.
    Format du tuple : (piece, (end_row, end_col), skipped_pieces)
    """
    moves_data = []
    
    # D'abord, vérifier s'il y a des captures obligatoires
    capture_moves = get_capture_moves(board, color)
    if capture_moves:
        # Si des captures existent, ce sont les seuls coups autorisés
        for piece, moves in capture_moves.items():
            for move, skipped in moves.items():
                moves_data.append((piece, move, skipped))
        return moves_data

    # S'il n'y a pas de captures, générer les mouvements simples
    for piece in board.get_all_pieces(color):
        valid_moves = board.get_valid_moves(piece)
        for move, skipped in valid_moves.items():
            # Dans ce cas, 'skipped' sera une liste vide
            moves_data.append((piece, move, skipped))
            
    return moves_data

def get_capture_moves(board, color):
    """
    Retourne uniquement les coups de capture possibles, groupés par pièce.
    Ceci est essentiel pour la règle de la prise obligatoire.
    """
    capture_moves = {}
    max_skipped_len = 0

    for piece in board.get_all_pieces(color):
        valid_moves = board.get_valid_moves(piece)
        piece_captures = {}
        for move, skipped in valid_moves.items():
            if skipped:
                piece_captures[move] = skipped
                if len(skipped) > max_skipped_len:
                    max_skipped_len = len(skipped)
        
        if piece_captures:
            capture_moves[piece] = piece_captures
    
    if not capture_moves:
        return {}

    # Filtrer pour ne garder que les coups qui capturent le maximum de pièces
    final_captures = {}
    for piece, moves in capture_moves.items():
        max_len_moves = {move: skipped for move, skipped in moves.items() if len(skipped) == max_skipped_len}
        if max_len_moves:
            final_captures[piece] = max_len_moves
            
    return final_captures

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

