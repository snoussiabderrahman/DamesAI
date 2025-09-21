import pygame
from .constants import BROWN, ROWS, CREAM, SQUARE_SIZE, COLS, BLACK
from .piece import Piece
from minimax.algorithm import zobrist_table, zobrist_turn_black

class Board:
     
    def __init__(self):
        self.board = []
        self.cream_left = self.black_left = 12
        self.cream_kings = self.black_kings = 0
        self.create_board()
        # === Calculer le hash de la position initiale ===
        self.zobrist_hash = self.calculate_initial_hash()
    
    def calculate_initial_hash(self):
        """Calcule le hash Zobrist pour la position de départ."""
        h = 0
        for r in range(ROWS):
            for c in range(COLS):
                piece = self.board[r][c]
                if piece != 0:
                    h ^= zobrist_table[(piece.color, piece.king, r, c)]
        return h
    
    # --- NOUVELLES FONCTIONS D'AIDE POUR LA MISE À JOUR DU HASH ---

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
    
    def draw(self, win):
        self.draw_squares(win)
        for row in range(ROWS):
            for col in range(COLS):
                piece = self.board[row][col]
                if piece != 0:
                    piece.draw(win)

    def print_board(self):
        for row in range(ROWS):
            for col in range(COLS):
                print(self.board[row][col])

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

    def winner(self, color):
        if self.black_left == 0 and self.black_kings == 1 and self.cream_left == 0 and self.cream_kings == 1:
            return "Equal"
        
        pieces = self.get_all_pieces(color)
        for piece in pieces:
            moves = self.get_valid_moves(piece)
            if moves:
                return None
        if color == CREAM:
            return "PLAYER black WINS!"
        else:
            return "Player cream WINS!"
        
    
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
        Fonction récursive qui ne trouve QUE les séquences de sauts pour un roi.
        Elle ne retourne que les points d'atterrissage finaux de chaque séquence.
        """
        jumps = {}
        
        # Itérer à travers les 4 directions diagonales
        for dr, dc in [(-1, -1), (-1, 1), (1, -1), (1, 1)]:
            opponent_found = None
            
            # Scanner le long d'une diagonale
            for i in range(1, ROWS):
                r, c = row + i * dr, col + i * dc

                if not (0 <= r < ROWS and 0 <= c < COLS):
                    break # Hors du plateau

                current_piece = self.board[r][c]

                if opponent_found:
                    # Si on a déjà sauté une pièce, on cherche maintenant une case vide
                    if current_piece == 0:
                        # Case d'atterrissage trouvée. Maintenant, cherchez des sauts supplémentaires à partir d'ici.
                        new_skipped = skipped + [opponent_found]
                        continuations = self._find_king_jumps(r, c, color, new_skipped)
                        
                        if not continuations:
                            # Si pas d'autres sauts, c'est un point d'atterrissage final.
                            jumps[(r, c)] = new_skipped
                        else:
                            # S'il y a d'autres sauts, les vrais points finaux sont ceux des continuations.
                            jumps.update(continuations)
                    else:
                        # La case est bloquée, on ne peut pas atterrir ici.
                        break
                elif current_piece != 0:
                    if current_piece.color == color:
                        break # Bloqué par sa propre pièce
                    else:
                        # C'est une pièce adverse qu'on peut sauter.
                        if current_piece not in skipped:
                            opponent_found = current_piece
                        else:
                            break # Déjà sauté cette pièce, on ne peut pas la sauter à nouveau.

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
                    break # Le chemin est bloqué par une pièce
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
        if color == BLACK:
            return self.black_left - self.cream_left +  (self.black_kings - self.cream_kings)/12
        else:
            return self.cream_left - self.black_left +  (self.cream_kings - self.black_kings)/12

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
            self.board[piece.row][piece.col] = piece
            # Mettre à jour les comptes
            if piece.king:
                if piece.color == CREAM: self.cream_kings += 1
                else: self.black_kings += 1
            else:
                if piece.color == CREAM: self.cream_left += 1
                else: self.black_left += 1
        
        