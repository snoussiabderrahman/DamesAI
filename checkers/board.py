import pygame
from .constants import BROWN, ROWS, CREAM, SQUARE_SIZE, COLS, BLACK
from .piece import Piece
from minimax.algorithm import zobrist_table
from checkers.constants import GREY, CROWN

PIECE_SQUARE_TABLE = [
    # Rangée 0 (Promotion) - Pas de bonus ici car la promotion est gérée par la création d'un roi
    [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0], 
    # Rangée 1 - Très proche de la promotion, forte valeur
    [0.5, 0.0, 0.5, 0.0, 0.5, 0.0, 0.5, 0.0], 
    # Rangée 2 - Bon contrôle et développement
    [0.0, 0.3, 0.0, 0.4, 0.0, 0.4, 0.0, 0.3], 
    # Rangée 3 - Cases centrales importantes
    [0.3, 0.0, 0.2, 0.0, 0.2, 0.0, 0.3, 0.0], 
    # Rangée 4 - Premières cases de développement
    [0.0, 0.1, 0.0, 0.1, 0.0, 0.1, 0.0, 0.1], 
    # Rangée 5 - Ligne de départ, valeur défensive
    [0.1, 0.0, 0.1, 0.0, 0.1, 0.0, 0.1, 0.0], 
    # Rangées 6 & 7 - Profond dans votre propre territoire, moins de valeur
    [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
    [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
]

class Board:
     
    def __init__(self):
        self.board = []
        self.cream_left = self.black_left = 12
        self.cream_kings = self.black_kings = 0
        self.create_board()
        self.zobrist_hash = self.calculate_initial_hash()

    def __repr__(self) -> str:
        return "\n".join(
            [" ".join([piece.__repr__() for piece in row]) for row in self.board]
        )

    def calculate_initial_hash(self):
        """Calcule le hash Zobrist pour la position de départ."""
        h = 0
        for r in range(ROWS):
            for c in range(COLS):
                piece = self.board[r][c]
                if piece != 0:
                    h ^= zobrist_table[(piece.color, piece.king, r, c)]
        return h
    
    # --- FONCTIONS D'AIDE POUR LA MISE À JOUR DU HASH ---
    def update_hash_move(self, piece, old_row, old_col, new_row, new_col):
        """Met à jour le hash pour un simple mouvement."""
        self.zobrist_hash ^= zobrist_table[(piece.color, piece.king, old_row, old_col)] # Retire l'ancienne pos
        self.zobrist_hash ^= zobrist_table[(piece.color, piece.king, new_row, new_col)] # Ajoute la nouvelle pos

    def update_hash_promotion(self, piece):
        """Met à jour le hash quand une pièce change entre pion et dame."""
        self.zobrist_hash ^= zobrist_table[(piece.color, False, piece.row, piece.col)] # XOR out l'état pion
        self.zobrist_hash ^= zobrist_table[(piece.color, True, piece.row, piece.col)]  # XOR in l'état dame

    def update_hash_piece(self, piece):
        """Met à jour le hash pour une pièce ajoutée ou retirée."""
        self.zobrist_hash ^= zobrist_table[(piece.color, piece.king, piece.row, piece.col)]
    
    def draw_squares(self, win):
        win.fill(BROWN)
        for row in range(ROWS):
            for col in range(row % 2, COLS, 2):
                pygame.draw.rect(win, CREAM, (row*SQUARE_SIZE, col *SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE))

    def move(self, piece, row, col):
        self.board[piece.row][piece.col], self.board[row][col] = self.board[row][col], self.board[piece.row][piece.col]
        piece.move(row, col)

        if (row == ROWS - 1 or row == 0) and piece.king == False:
            piece.make_king()
            if piece.color == BLACK:
                self.black_kings += 1
                self.black_left -= 1
            else:
                self.cream_kings += 1 
                self.cream_left -= 1

    def get_piece(self, row, col):
        return self.board[row][col]

    def create_board(self):
        for row in range(ROWS):
            self.board.append([])
            for col in range(COLS):
                if col % 2 == ((row +  1) % 2):
                    if row < 3:
                        self.board[row].append(Piece(row, col, BLACK))
                    elif row > 4:
                        self.board[row].append(Piece(row, col, CREAM))
                    else:
                        self.board[row].append(0)
                else:
                    self.board[row].append(0)
    
    def draw(self, win, animation_data=None):
        """
        La méthode de dessin principale, gère maintenant une liste de pièces à cacher.
        """
        self.draw_squares(win)
        
        animating_piece = None
        visually_removed = []
        if animation_data:
            animating_piece = animation_data['piece']
            visually_removed = animation_data.get('visually_removed', [])

        for row in range(ROWS):
            for col in range(COLS):
                piece = self.board[row][col]
                if piece != 0:
                    # On ne dessine pas la pièce qui est en cours d'animation
                    # NI les pièces qui ont été capturées pendant l'animation
                    if piece == animating_piece or piece in visually_removed:
                        continue
                    piece.draw(win)

        # La pièce animée est toujours dessinée séparément par-dessus le reste
        if animating_piece:
            # On utilise les coordonnées interpolées de l'animation
            pygame.draw.circle(win, GREY, (animation_data['current_x'], animation_data['current_y']), SQUARE_SIZE//2 - 15 + 2)
            pygame.draw.circle(win, animating_piece.color, (animation_data['current_x'], animation_data['current_y']), SQUARE_SIZE//2 - 15)
            if animating_piece.king:
                win.blit(CROWN, (animation_data['current_x'] - CROWN.get_width()//2, animation_data['current_y'] - CROWN.get_height()//2))

    def remove(self, pieces):
        for piece in pieces:
            if piece != 0:
                self.board[piece.row][piece.col] = 0
                if piece.king:
                    if piece.color == CREAM:
                        self.cream_kings -= 1
                    else:
                        self.black_kings -= 1
                else:
                    if piece.color == CREAM:
                        self.cream_left -= 1
                    else:
                        self.black_left -= 1

    def winner(self, color_turn, position_history, moves_since_capture):

        # === RÈGLES DE NULLITÉ ===
        if moves_since_capture >= 40:
            return "Draw by 40-move rule!"
        
        if any(count >= 3 for count in position_history.values()):
            return "Draw by repetition!"

        # --- Conditions de victoire/défaite ---
        pieces = self.get_all_pieces(color_turn)
        
        has_moves = False
        for piece in pieces:
            if self.get_valid_moves(piece):
                has_moves = True
                break
        
        if not has_moves:
            if color_turn == CREAM:
                return "PLAYER black WINS!"
            else:
                return "Player cream WINS!"
        
        return None
    
    def get_valid_moves(self, piece):
        moves = {}
        if piece.king:
            # Pour les rois, on cherche d'abord les sauts possibles.
            jumps = self._find_king_jumps(piece.row, piece.col, piece.color, [])
            
            # Si des sauts existent, ils sont obligatoires et sont les seuls coups valides.
            if jumps:
                return jumps

            # S'il n'y a pas de sauts, alors on cherche les mouvements simples.
            moves.update(self._find_king_simple_moves(piece.row, piece.col))
            return moves
        else:
            # La logique pour les pions reste inchangée.
            left = piece.col - 1
            right = piece.col + 1
            row = piece.row
            if piece.color == CREAM:
                moves.update(self.traverse_left(row - 1, max(row-3, -1), -1, piece.color, left))
                moves.update(self.traverse_right(row - 1, max(row-3, -1), -1, piece.color, right))
            if piece.color == BLACK:
                moves.update(self.traverse_left(row + 1, min(row+3, ROWS), 1, piece.color, left))
                moves.update(self.traverse_right(row + 1, min(row+3, ROWS), 1, piece.color, right))
        
        return moves

    def _find_king_jumps(self, row, col, color, skipped):
        """
        Fonction récursive qui trouve les séquences de sauts pour un roi.
        Retourne maintenant un dictionnaire contenant les pièces sautées ET le chemin.
        """
        jumps = {}
        
        for dr, dc in [(-1, -1), (-1, 1), (1, -1), (1, 1)]:
            opponent_found = None
            
            for i in range(1, ROWS):
                r, c = row + i * dr, col + i * dc

                if not (0 <= r < ROWS and 0 <= c < COLS):
                    break

                current_piece = self.board[r][c]

                if opponent_found:
                    if current_piece == 0:
                        new_skipped = skipped + [opponent_found]
                        # === On transmet le chemin via la récursion ===
                        continuations = self._find_king_jumps(r, c, color, new_skipped)
                        
                        if not continuations:
                            # Cas de base : c'est la fin de la séquence
                            jumps[(r, c)] = {
                                'skipped': new_skipped,
                                'path': [(r, c)] # Le chemin est juste cette case
                            }
                        else:
                            # Il y a d'autres sauts, on ajoute les chemins des continuations
                            for landing_pos, data in continuations.items():
                                # On préfixe le chemin avec notre case d'atterrissage actuelle
                                data['path'].insert(0, (r, c))
                                jumps[landing_pos] = data
                    else:
                        break
                elif current_piece != 0:
                    if current_piece.color == color:
                        break
                    else:
                        if current_piece not in skipped:
                            opponent_found = current_piece
                        else:
                            break
        return jumps

    def _find_king_simple_moves(self, row, col):
        """Trouve les mouvements simples (non-capture) pour un roi."""
        moves = {}
        # Itérer à travers les 4 directions diagonales
        for dr, dc in [(-1, -1), (-1, 1), (1, -1), (1, 1)]:
            # Scanner le long de la diagonale
            for i in range(1, ROWS):
                r, c = row + i * dr, col + i * dc

                if not (0 <= r < ROWS and 0 <= c < COLS):
                    break # Hors du plateau

                current_piece = self.board[r][c]
                if current_piece == 0:
                    moves[(r, c)] = [] # Case vide, mouvement valide
                else:
                    break 
        return moves

    def traverse_left(self, start, stop, step, color, left, skipped=[]):
        moves = {}
        last = []
        for r in range(start, stop, step):
            if left < 0:
                break
            
            current = self.board[r][left]
            if current == 0:
                if skipped and not last:
                    break
                elif skipped:
                    moves[(r, left)] = skipped + last
                    new_skipped = skipped + last
                else:
                    new_skipped = last
                    moves[(r, left)] = last
                
                if last:
                    if step == -1:
                        row = max(r-3, -1)
                    else:
                        row = min(r+3, ROWS)
                    moves.update(self.traverse_left(r+step, row, step, color, left-1,new_skipped))
                    moves.update(self.traverse_right(r+step, row, step, color, left+1,new_skipped))
                break
            elif current.color == color:
                break
            else:
                last = [current]

            left -= 1
        
        return moves

    def traverse_right(self, start, stop, step, color, right, skipped=[]):
        moves = {}
        last = []
        for r in range(start, stop, step):
            if right >= COLS:
                break
            
            current = self.board[r][right]
            if current == 0:
                if skipped and not last:
                    break
                elif skipped:
                    moves[(r,right)] = skipped + last
                    new_skipped = skipped + last
                else:
                    new_skipped = last
                    moves[(r, right)] = last
                
                if last:
                    if step == -1:
                        row = max(r-3, -1)
                    else:
                        row = min(r+3, ROWS)
                    moves.update(self.traverse_left(r+step, row, step, color, right-1,new_skipped))
                    moves.update(self.traverse_right(r+step, row, step, color, right+1,new_skipped))
                break
            elif current.color == color:
                break
            else:
                last = [current]

            right += 1
        
        return moves
   
    def evaluate(self, color):
        king_value = 1.8

        black_score = self.black_left + self.black_kings * king_value
        cream_score = self.cream_left + self.cream_kings * king_value
        
        # Ajout de l'évaluation positionnelle
        for r in range(ROWS):
            for c in range(COLS):
                piece = self.board[r][c]
                if piece != 0 and not piece.king: # On applique ceci uniquement aux pions
                    if piece.color == CREAM:
                        cream_score += PIECE_SQUARE_TABLE[r][c]
                    else:
                        # On inverse la table pour les noirs 
                        black_score += PIECE_SQUARE_TABLE[7 - r][7 - c]
        
        if color == BLACK:
            return black_score - cream_score
        else:
            return cream_score - black_score
        

    def get_all_pieces(self, color):
        pieces = []
        for row in self.board:
            for piece in row:
                if piece != 0 and piece.color == color:
                    pieces.append(piece)
        return pieces

    def get_board(self):
        return self.board

    def make_move(self, piece, end_row, end_col):
        """
        Applique un coup au plateau.
        Retourne les pièces capturées et si une promotion a eu lieu.
        """
        start_row, start_col = piece.row, piece.col
        
        # 1. Déplacer la pièce sur le plateau
        self.board[start_row][start_col] = 0
        self.board[end_row][end_col] = piece

        # === HACHAGE : Met à jour pour le mouvement ===
        self.update_hash_move(piece, start_row, start_col, end_row, end_col)
        piece.move(end_row, end_col)

        # 2. Gérer la promotion en roi
        was_promoted = False
        if (end_row == ROWS - 1 or end_row == 0) and not piece.king:
            # === HACHAGE : Met à jour pour la promotion AVANT de changer l'état ===
            self.update_hash_promotion(piece)
            piece.make_king()
            was_promoted = True
            if piece.color == BLACK:
                self.black_kings += 1
            else:
                self.cream_kings += 1

        return was_promoted

    def undo_move(self, piece, start_row, start_col, was_promoted):
        """Annule un coup pour restaurer l'état précédent du plateau."""
        current_row, current_col = piece.row, piece.col
        
        # 1. Annuler la promotion si nécessaire
        if was_promoted:
            # === HACHAGE : Annule la promotion AVANT de changer l'état ===
            self.update_hash_promotion(piece)
            piece.king = False
            if piece.color == BLACK:
                self.black_kings -= 1
            else:
                self.cream_kings -= 1
                
        # 2. Replacer la pièce à sa position d'origine
        self.board[start_row][start_col] = piece
        self.board[current_row][current_col] = 0

        # === HACHAGE : Annule le mouvement ===
        self.update_hash_move(piece, current_row, current_col, start_row, start_col)
        piece.move(start_row, start_col)

    def remove_and_get_skipped(self, skipped_pieces):
        """
        Retire les pièces capturées du plateau, mais retourne les pièces
        retirées pour pouvoir les restaurer plus tard.
        """
        for piece in skipped_pieces:
            self.update_hash_piece(piece) # === HACHAGE : Met à jour pour la pièce retirée ===
            self.board[piece.row][piece.col] = 0
            # Mettre à jour les comptes
            if piece.king:
                if piece.color == CREAM: self.cream_kings -= 1
                else: self.black_kings -= 1
            else:
                if piece.color == CREAM: self.cream_left -= 1
                else: self.black_left -= 1
        return skipped_pieces

    def restore_skipped(self, skipped_pieces):
        """Restaure les pièces capturées sur le plateau."""
        for piece in skipped_pieces:
            self.update_hash_piece(piece) # === HACHAGE : Un XOR annule un autre XOR ===
            self.board[piece.row][piece.col] = piece
            # Mettre à jour les comptes
            if piece.king:
                if piece.color == CREAM: self.cream_kings += 1
                else: self.black_kings += 1
            else:
                if piece.color == CREAM: self.cream_left += 1
                else: self.black_left += 1
        
        