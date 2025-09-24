from checkers.constants import BLACK, CREAM, ROWS, COLS
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

def NegaMax(position, depth, color_player, alpha, beta, killer_moves, profiler, position_history, moves_since_capture):
    
    alpha_orig = alpha
    current_hash = position.zobrist_hash
    if color_player == BLACK:
        current_hash ^= zobrist_turn_black
    
    tt_entry = transposition_table.get(current_hash)
    if (
        tt_entry
        and tt_entry["depth"] >= depth
        and tt_entry["position_repr"] == position.__repr__()
    ):
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

    # On passe les nouvelles infos à la fonction winner
    if position.winner(color_player, position_history, moves_since_capture) is not None:
        return position.evaluate(color_player), None

    if depth == 0:
        q_eval = quiescenceSearch(position, alpha, beta, color_player, profiler)
        return q_eval, None
    
    best_move_data = None
    possible_moves = get_possible_moves(position, color_player)
    
    # --- Boucle de recherche ---
    for move_data in possible_moves:
        # La variable est bien 'skipped_pieces' ici
        piece, (end_row, end_col), skipped_pieces = move_data
        start_row, start_col = piece.row, piece.col
        
        # --- MISE À JOUR DE L'HISTORIQUE SIMULÉ ---
        # On met à jour l'historique et le compteur pour l'appel récursif
        next_color = CREAM if color_player == BLACK else BLACK
        
        final_skipped_list = skipped_pieces['skipped'] if isinstance(skipped_pieces, dict) else skipped_pieces
        
        new_moves_since_capture = 0 if final_skipped_list else moves_since_capture + 1
        
        # On met à jour le hash pour l'historique
        next_hash = position.zobrist_hash
        if next_color == BLACK:
            next_hash ^= zobrist_turn_black
        
        position_history[next_hash] = position_history.get(next_hash, 0) + 1
        
        # --- FAIRE LE COUP (MAKE MOVE) ---
        removed = position.remove_and_get_skipped(final_skipped_list)
        was_promoted = position.make_move(piece, end_row, end_col)
        
        # Appel récursif avec l'historique mis à jour
        evaluation = -NegaMax(position, depth - 1, next_color, -beta, -alpha, killer_moves, profiler, position_history, new_moves_since_capture)[0]
        
        # --- DÉFAIRE LE COUP (UNDO MOVE) ---
        position.undo_move(piece, start_row, start_col, was_promoted)
        position.restore_skipped(removed)

        # On annule la mise à jour de l'historique
        position_history[next_hash] -= 1
        if position_history[next_hash] == 0:
            del position_history[next_hash]

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
        "score": alpha,
        "depth": depth,
        "flag": flag,
        "best_move": best_move_data,
        "position_repr": position.__repr__(),
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
                moves_data.append((piece, move, details))
        return moves_data
    
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
            skipped_list = []
            if isinstance(details, dict):
                skipped_list = details.get('skipped', [])
            else:
                skipped_list = details

            if skipped_list: 
                piece_captures[move] = details 
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
            skipped_list = details['skipped'] if isinstance(details, dict) else details
            if len(skipped_list) == max_skipped_len:
                max_len_moves[move] = details 
        
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

