from checkers.constants import BLACK, CREAM, ROWS, COLS
import pygame
import random

# --- 1. INITIALISATION DU HACHAGE ZOBRIST ET DES STRUCTURES D'OPTIMISATION ---

# Table de nombres aléatoires pour le hachage
zobrist_table = {}
# Clés pour chaque type de pièce à chaque position
for row in range(ROWS):
    for col in range(COLS):
        for piece_color in [BLACK, CREAM]:
            # Clé pour un pion (man)
            zobrist_table[(piece_color, False, row, col)] = random.getrandbits(64)
            # Clé pour une dame (king)
            zobrist_table[(piece_color, True, row, col)] = random.getrandbits(64)

# Clé unique pour indiquer que c'est au tour du joueur NOIR (BLACK) de jouer
zobrist_turn_black = random.getrandbits(64)

# La Table de Transposition (TT) qui stockera les résultats
transposition_table = {}

#------------- FONCTION QUIESCENCE SEARCH -------------------#
# minimax/algorithm.py

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

    capture_moves_dict = get_capture_moves(board, color_player)
    
    capture_moves_list = []
    for piece, moves in capture_moves_dict.items():
        for move, details in moves.items():
            capture_moves_list.append((piece, move, details))
    
    for move_data in capture_moves_list:
        # La variable est 'skipped_pieces' ici, car elle est décomposée de move_data
        piece, (end_row, end_col), skipped_pieces = move_data
        start_row, start_col = piece.row, piece.col

        # === CORRECTION : Extraire la liste des pièces sautées (comme dans NegaMax) ===
        final_skipped_list = []
        if isinstance(skipped_pieces, dict):
            # Si c'est un dictionnaire (saut de roi), on prend la liste depuis la clé 'skipped'
            final_skipped_list = skipped_pieces['skipped']
        else:
            # Sinon, c'est déjà la bonne liste (saut de pion)
            final_skipped_list = skipped_pieces
        # ===========================================================================

        # --- FAIRE LE COUP (MAKE MOVE) ---
        # On utilise maintenant la liste nettoyée 'final_skipped_list'
        removed = board.remove_and_get_skipped(final_skipped_list)
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

def NegaMax(position, depth, color_player, alpha, beta, killer_moves, profiler):
    # --- Début de la fonction (recherche TT, etc.) ---
    alpha_orig = alpha
    current_hash = position.zobrist_hash
    if color_player == BLACK:
        current_hash ^= zobrist_turn_black
    
    tt_entry = transposition_table.get(current_hash)
    if tt_entry and tt_entry['depth'] >= depth:
        profiler.increment_tt_hits()
        if tt_entry['flag'] == 'EXACT':
            return tt_entry['score'], tt_entry['best_move']
        elif tt_entry['flag'] == 'LOWERBOUND':
            alpha = max(alpha, tt_entry['score'])
        elif tt_entry['flag'] == 'UPPERBOUND':
            beta = min(beta, tt_entry['score'])
        if alpha >= beta:
            return tt_entry['score'], tt_entry['best_move']

    profiler.increment_nodes()

    if position.winner(color_player) is not None:
        return position.evaluate(color_player), None

    if depth == 0:
        q_eval = quiescenceSearch(position, alpha, beta, color_player, profiler)
        return q_eval, None
    
    best_move_data = None
    possible_moves = get_possible_moves(position, color_player)
    
    # --- Boucle de recherche ---
    for move_data in possible_moves:
        # La variable est bien 'skipped_pieces' ici, comme dans votre code.
        piece, (end_row, end_col), skipped_pieces = move_data
        start_row, start_col = piece.row, piece.col

        # === CORRECTION AVEC LE BON NOM DE VARIABLE ===
        # On vérifie la variable 'skipped_pieces'
        final_skipped_list = []
        if isinstance(skipped_pieces, dict):
            # Si c'est un dictionnaire, on prend la liste depuis la clé 'skipped'
            final_skipped_list = skipped_pieces['skipped']
        else:
            # Sinon, c'est déjà la bonne liste (pour les pions ou les coups simples)
            final_skipped_list = skipped_pieces
        # =================================================

        # --- FAIRE LE COUP (MAKE MOVE) ---
        # On utilise maintenant la liste nettoyée 'final_skipped_list'
        removed = position.remove_and_get_skipped(final_skipped_list)
        was_promoted = position.make_move(piece, end_row, end_col)
        
        # Appel récursif
        evaluation = -NegaMax(position, depth - 1, CREAM if color_player == BLACK else BLACK, -beta, -alpha, killer_moves, profiler)[0]
        
        # --- DÉFAIRE LE COUP (UNDO MOVE) ---
        position.undo_move(piece, start_row, start_col, was_promoted)
        position.restore_skipped(removed)
        
        if evaluation > alpha:
            alpha = evaluation
            best_move_data = move_data
            
            if alpha >= beta:
                profiler.increment_cutoffs()
                break
    
    # --- Fin de la fonction (sauvegarde TT) ---
    flag = ''
    if alpha <= alpha_orig:
        flag = 'UPPERBOUND'
    elif alpha >= beta:
        flag = 'LOWERBOUND'
    else:
        flag = 'EXACT'

    transposition_table[current_hash] = {
        'score': alpha, 'depth': depth, 'flag': flag, 'best_move': best_move_data
    }
    
    return alpha, best_move_data

def get_possible_moves(board, color):
    """
    Génère une liste de tous les coups possibles. Gère maintenant la nouvelle
    structure de données pour les sauts du roi.
    """
    moves_data = []
    capture_moves = get_capture_moves(board, color)

    if capture_moves:
        for piece, moves in capture_moves.items():
            for move, details in moves.items():
                # === MODIFICATION : 'details' est maintenant la structure complète ===
                moves_data.append((piece, move, details))
        return moves_data

    # La logique pour les mouvements simples reste la même
    for piece in board.get_all_pieces(color):
        valid_moves = board.get_valid_moves(piece)
        for move, skipped in valid_moves.items():
            moves_data.append((piece, move, skipped)) # Ici, 'skipped' est une liste vide
            
    return moves_data

def get_capture_moves(board, color):
    """
    Retourne uniquement les coups de capture possibles, en respectant la capture maximale.
    Cette version gère correctement les sauts de pion (liste) et de roi (dictionnaire).
    """
    capture_moves = {}
    max_skipped_len = 0

    # Étape 1 : Collecter toutes les captures possibles
    for piece in board.get_all_pieces(color):
        valid_moves = board.get_valid_moves(piece)
        piece_captures = {}
        for move, details in valid_moves.items():
            # 'details' est soit une LISTE (pion) soit un DICTIONNAIRE (roi)
            
            # --- NOUVELLE LOGIQUE POUR TROUVER LA LISTE DES PIÈCES SAUTÉES ---
            skipped_list = []
            if isinstance(details, dict):
                skipped_list = details.get('skipped', [])
            else:
                skipped_list = details

            if skipped_list: # S'assurer que c'est bien une capture
                piece_captures[move] = details # On stocke la structure de données ORIGINALE
                if len(skipped_list) > max_skipped_len:
                    max_skipped_len = len(skipped_list)
        
        if piece_captures:
            capture_moves[piece] = piece_captures
    
    if not capture_moves:
        return {}

    # Étape 2 : Filtrer pour ne garder que les captures de longueur maximale
    final_captures = {}
    for piece, moves in capture_moves.items():
        max_len_moves = {}
        for move, details in moves.items():
            # --- NOUVELLE LOGIQUE POUR VÉRIFIER LA LONGUEUR ---
            skipped_list = details['skipped'] if isinstance(details, dict) else details
            if len(skipped_list) == max_skipped_len:
                max_len_moves[move] = details # On garde la structure ORIGINALE
        
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



