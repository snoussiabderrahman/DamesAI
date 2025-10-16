from checkers.constants import BLACK, CREAM, ROWS, COLS, LOSS_SCORE, DRAW_SCORE
import random
import time

SEARCH_DEPTH = 10

# --- 1. INITIALISATION DU HACHAGE ZOBRIST ET DES STRUCTURES D'OPTIMISATION ---
zobrist_table = {}
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


class SearchTimeout(Exception):
    """Exception levée quand le temps alloué à la recherche est écoulé."""
    pass


def _check_time(profiler, time_limit):
    """Lève SearchTimeout si le budget de temps est dépassé."""
    if time_limit is not None and profiler.start_time:
        if time.perf_counter() - profiler.start_time > time_limit:
            raise SearchTimeout()
        
def move_to_key(move_data):
    """
    Retourne une clé immuable décrivant un coup :
    (start_row, start_col, end_row, end_col, (skipped positions...))
    Permet de stocker/comparer des "killer moves" indépendamment des
    objets Piece (mutables).
    """
    piece, (end_row, end_col), details = move_data
    start_row, start_col = piece.row, piece.col

    if isinstance(details, dict):
        skipped = details.get("skipped", [])
    else:
        skipped = details

    skipped_coords = tuple((p.row, p.col) for p in skipped) if skipped else ()
    return (start_row, start_col, end_row, end_col, skipped_coords)


def is_capture_move(move_data):
    """True si le coup capture au moins une pièce."""
    details = move_data[2]
    if isinstance(details, dict):
        skipped = details.get("skipped", [])
    else:
        skipped = details
    return bool(skipped)


#------------- FONCTION QUIESCENCE SEARCH -------------------#
def quiescenceSearch(board, alpha, beta, color_player, profiler,
                     time_limit=None):
    """
    Recherche de quiétude qui n'explore que les coups de capture.
    Pattern make/undo utilisé ; propagation du time_limit.
    """
    profiler.increment_nodes()
    _check_time(profiler, time_limit)

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
        _check_time(profiler, time_limit)

        # Décomposition
        piece, (end_row, end_col), skipped_pieces = move_data
        start_row, start_col = piece.row, piece.col

        final_skipped_list = []
        if isinstance(skipped_pieces, dict):
            final_skipped_list = skipped_pieces.get('skipped', [])
        else:
            final_skipped_list = skipped_pieces

        # --- FAIRE LE COUP (MAKE MOVE) ---
        removed = board.remove_and_get_skipped(final_skipped_list)
        was_promoted = board.make_move(piece, end_row, end_col)

        try:
            # Appel récursif (on passe le même objet 'board')
            score = -quiescenceSearch(
                board,
                -beta,
                -alpha,
                CREAM if color_player == BLACK else BLACK,
                profiler,
                time_limit,
            )
        finally:
            # --- DÉFAIRE LE COUP (UNDO MOVE) ---
            board.undo_move(piece, start_row, start_col, was_promoted)
            board.restore_skipped(removed)

        if score >= beta:
            return beta

        if score > alpha:
            alpha = score

    return alpha

def NegaMax(
    position,
    depth,
    color_player,
    alpha,
    beta,
    profiler,
    position_history,
    moves_since_capture,
    time_limit=None,
):
    """
    NegaMax avec alpha-beta, table de transposition et ordering coups.
    """
    _check_time(profiler, time_limit)

    # Règles de nullité
    if any(count >= 3 for count in position_history.values()) or \
       moves_since_capture >= 40:
        return DRAW_SCORE, None

    # Vérifier s'il y a des coups légaux
    has_moves = False
    for piece in position.get_all_pieces(color_player):
        if position.get_valid_moves(piece):
            has_moves = True
            break

    if not has_moves:
        return LOSS_SCORE + (SEARCH_DEPTH - depth), None

    if depth == 0:
        q_eval = quiescenceSearch(
            position, alpha, beta, color_player, profiler, time_limit
        )
        return q_eval, None

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
        if tt_entry["flag"] == "EXACT":
            return tt_entry["score"], tt_entry["best_move"]
        elif tt_entry["flag"] == "LOWERBOUND":
            alpha = max(alpha, tt_entry["score"])
        elif tt_entry["flag"] == "UPPERBOUND":
            beta = min(beta, tt_entry["score"])
        if alpha >= beta:
            return tt_entry["score"], tt_entry["best_move"]

    profiler.increment_nodes()

    # Vérifier victoire/défaite via winner
    if position.winner(color_player, position_history, moves_since_capture) \
       is not None:
        return position.evaluate(color_player), None

    best_move_data = None
    possible_moves = get_possible_moves(position, color_player)

    # --- Ordonnancement des coups (TT best, captures, autres) ---
    tt_best_key = None
    if tt_entry and tt_entry.get("best_move") is not None:
        try:
            tt_best_key = move_to_key(tt_entry["best_move"])
        except Exception:
            tt_best_key = None

    moves_meta = []
    for md in possible_moves:
        try:
            mkey = move_to_key(md)
        except Exception:
            mkey = None
        cap = is_capture_move(md)

        # Ranking: 0=TT best, 1=capture, 2=other
        rank = 2
        if tt_best_key is not None and mkey == tt_best_key:
            rank = 0
        elif cap:
            rank = 1

        moves_meta.append((rank, md, mkey, cap))

    moves_meta.sort(key=lambda x: x[0])

    # --- Boucle principale de recherche ---
    for _, move_data, move_key, _is_capture in moves_meta:
        _check_time(profiler, time_limit)

        piece, (end_row, end_col), skipped_pieces = move_data
        start_row, start_col = piece.row, piece.col

        next_color = CREAM if color_player == BLACK else BLACK
        final_skipped_list = (
            skipped_pieces["skipped"]
            if isinstance(skipped_pieces, dict)
            else skipped_pieces
        )
        new_moves_since_capture = 0 if final_skipped_list else \
                                 moves_since_capture + 1

        # Mise à jour simulée de l'historique (hash)
        next_hash = position.zobrist_hash
        if next_color == BLACK:
            next_hash ^= zobrist_turn_black

        position_history[next_hash] = position_history.get(next_hash, 0) + 1

        # Faire le coup (make)
        removed = position.remove_and_get_skipped(final_skipped_list)
        was_promoted = position.make_move(piece, end_row, end_col)

        try:
            evaluation = -NegaMax(
                position,
                depth - 1,
                next_color,
                -beta,
                -alpha,
                profiler,
                position_history,
                new_moves_since_capture,
                time_limit,
            )[0]
        finally:
            # Défaire le coup (undo)
            position.undo_move(piece, start_row, start_col, was_promoted)
            position.restore_skipped(removed)

            # Annuler la mise à jour de l'historique
            position_history[next_hash] -= 1
            if position_history[next_hash] == 0:
                del position_history[next_hash]

        if evaluation > alpha:
            alpha = evaluation
            best_move_data = move_data

            if alpha >= beta:
                profiler.increment_cutoffs()
                break

    # --- Sauvegarde dans la table de transposition (TT) ---
    if alpha <= alpha_orig:
        flag = "UPPERBOUND"
    elif alpha >= beta:
        flag = "LOWERBOUND"
    else:
        flag = "EXACT"

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
    Génère une liste de tous les coups possibles. Gère la nouvelle structure
    de données pour les sauts du roi.
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
            moves_data.append((piece, move, skipped))  # 'skipped' est une liste
    return moves_data


def get_capture_moves(board, color):
    """
    Retourne uniquement les coups de capture possibles, en respectant la
    capture maximale. Gère les sauts de pion (liste) et de roi (dict).
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

