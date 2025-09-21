import pygame
from .constants import CREAM, BLACK, BLUE, SQUARE_SIZE, ROWS, COLS
from checkers.board import Board


class Game:
    def __init__(self, win):
        self._init()
        self.win = win
        # === NOUVEAU : Variables pour gérer l'état de l'animation ===
        self.animation_data = None  # Stockera les infos du coup à animer
        self.animation_speed = 4  # Vitesse de l'animation (plus élevé = plus rapide)
    
    def is_animating(self):
        """Retourne True si une animation est en cours."""
        return self.animation_data is not None

    def update(self):
        """
        La méthode de mise à jour principale. Gère maintenant la logique d'animation.
        """
        # S'il y a une animation en cours, on la met à jour.
        if self.is_animating():
            self._update_animation()
        
        # On dessine le plateau. La méthode draw saura gérer l'animation.
        self.board.draw(self.win, self.animation_data)
        
        # On dessine les coups valides pour le joueur humain.
        if not self.is_animating():
            self.draw_valid_moves(self.valid_moves)
            
        pygame.display.update()

    def _update_animation(self):
        """Fait avancer l'animation d'une étape."""
        data = self.animation_data
        
        # Interpolation linéaire pour un mouvement fluide
        dx = data['target_x'] - data['current_x']
        dy = data['target_y'] - data['current_y']
        
        distance = (dx**2 + dy**2)**0.5
        
        if distance < self.animation_speed:
            # L'animation est terminée
            self._finalize_animation()
        else:
            # On déplace la pièce d'un pas vers sa destination
            data['current_x'] += self.animation_speed * (dx / distance)
            data['current_y'] += self.animation_speed * (dy / distance)

    def _finalize_animation(self):
        """Termine l'animation et applique le coup à l'état du jeu."""
        if not self.animation_data:
            return

        piece = self.animation_data['piece']
        end_row = self.animation_data['end_row']
        end_col = self.animation_data['end_col']
        skipped = self.animation_data['skipped']

        # Applique réellement le mouvement sur le plateau de jeu
        self.board.remove(skipped)
        self.board.move(piece, end_row, end_col)
        self.change_turn()
        
        # Réinitialise l'état de l'animation
        self.animation_data = None

    def ai_move(self, move_data):
        """
        Au lieu d'exécuter le coup, cette méthode LANCE l'animation.
        """
        if move_data is None:
            print("AI has no moves.")
            return

        piece, (end_row, end_col), skipped_pieces = move_data
        
        # Stocke toutes les informations nécessaires pour l'animation
        self.animation_data = {
            'piece': piece,
            'end_row': end_row,
            'end_col': end_col,
            'skipped': skipped_pieces,
            'current_x': piece.x,
            'current_y': piece.y,
            'target_x': end_col * SQUARE_SIZE + SQUARE_SIZE // 2,
            'target_y': end_row * SQUARE_SIZE + SQUARE_SIZE // 2,
        }
    
    def _init(self):
        self.selected = None
        self.board = Board()
        self.turn = CREAM
        self.valid_moves = {}

    def winner(self, color):
        return self.board.winner(color)

    def reset(self):
        self._init()
    
    def _get_all_mandatory_moves_for_turn(self, color):
        """
        Analyse tout le plateau et retourne UNIQUEMENT les coups qui
        respectent la règle de la capture maximale.
        Retourne une liste de descriptions de coups : [(piece, move, skipped), ...].
        """
        all_capture_moves = []
        max_skipped_len = 0

        # 1. Trouver toutes les captures possibles et le nombre maximum de sauts
        for piece in self.board.get_all_pieces(color):
            valid_moves = self.board.get_valid_moves(piece)
            for move, skipped in valid_moves.items():
                if skipped:
                    all_capture_moves.append((piece, move, skipped))
                    if len(skipped) > max_skipped_len:
                        max_skipped_len = len(skipped)
        
        # 2. S'il n'y a aucune capture, retourner une liste vide
        if not all_capture_moves:
            return []

        # 3. Filtrer pour ne garder que les coups qui capturent le maximum de pièces
        final_mandatory_moves = [
            move_info for move_info in all_capture_moves 
            if len(move_info[2]) == max_skipped_len
        ]
        
        return final_mandatory_moves

    def select(self, row, col):
        # Étape 1 : Gérer la tentative de DÉPLACEMENT si une pièce est déjà sélectionnée.
        if self.selected:
            # Tente d'effectuer le mouvement. _move retourne True si c'est réussi.
            if self._move(row, col):
                # Le mouvement a réussi, la fonction change_turn() s'occupera de tout.
                return True
            else:
                # Le mouvement a échoué (clic sur une case invalide).
                # CORRECTION : On désélectionne la pièce et on efface ses mouvements.
                self.selected = None
                self.valid_moves = {}
                # On ne quitte pas ! On continue pour voir si ce nouveau clic
                # correspond à une NOUVELLE sélection de pièce.
        
        # À ce stade, soit aucune pièce n'était sélectionnée, soit une tentative de
        # mouvement a échoué et nous traitons le clic comme une nouvelle sélection.

        # Étape 2 : Gérer la tentative de SÉLECTION d'une nouvelle pièce.
        piece = self.board.get_piece(row, col)

        # On ne peut sélectionner que les pièces de sa propre couleur.
        if piece == 0 or piece.color != self.turn:
            # Le clic est sur une case vide ou une pièce adverse. On s'assure que tout est propre.
            self.selected = None
            self.valid_moves = {}
            return False

        # Le clic est sur une pièce valide du joueur. Appliquons la logique du jeu.
        mandatory_moves = self._get_all_mandatory_moves_for_turn(self.turn)

        if mandatory_moves:
            # Cas 1 : Il y a des captures obligatoires.
            is_piece_mandatory = any(p == piece for p, m, s in mandatory_moves)
            if is_piece_mandatory:
                # Cette pièce PEUT effectuer la capture obligatoire. On la sélectionne.
                self.selected = piece
                self.valid_moves = {m: s for p, m, s in mandatory_moves if p == piece}
                return True
            else:
                # Cette pièce ne peut pas. La sélection est invalide. On efface tout.
                self.selected = None
                self.valid_moves = {}
                return False
        else:
            # Cas 2 : Pas de captures obligatoires.
            # On peut sélectionner n'importe quelle pièce qui a des mouvements.
            possible_moves = self.board.get_valid_moves(piece)
            if possible_moves:
                self.selected = piece
                self.valid_moves = possible_moves
                return True
            else:
                # La pièce n'a aucun mouvement possible. Sélection invalide.
                self.selected = None
                self.valid_moves = {}
                return False

    def check_mandatory_moves(self, color):
        mandatory_moves = {}
        for row in range(ROWS):
            for col in range(COLS):
                piece = self.board.get_piece(row, col)
                if piece != 0 and piece.color == color:
                    valid_moves = self.board.get_valid_moves(piece)
                    for move, skipped in valid_moves.items():
                        if skipped:
                            mandatory_moves[(row, col)] = valid_moves
                            break  
        return mandatory_moves

    def _move(self, row, col):
        piece = self.board.get_piece(row, col)
        if self.selected and piece == 0 and (row, col) in self.valid_moves:
            self.board.move(self.selected, row, col)
            skipped = self.valid_moves[(row, col)]
            if skipped:
                self.board.remove(skipped)
            self.change_turn()
        else:
            return False

        return True

    def draw_valid_moves(self, moves):
        for move in moves:
            row, col = move
            pygame.draw.circle(self.win, BLUE, (col * SQUARE_SIZE + SQUARE_SIZE//2, row * SQUARE_SIZE + SQUARE_SIZE//2), 15)

    def change_turn(self):
        self.valid_moves = {}
        if self.turn == CREAM:
            self.turn = BLACK
        else:
            self.turn = CREAM

    def extract_max_jumps(self, moves):
        max_jumps = max(len(skipped) for skipped in moves.values())  # Find the maximum number of skipped pieces

        # Filter moves that have the maximum skipped pieces
        max_jump_moves = {move: skipped for move, skipped in moves.items() if len(skipped) == max_jumps}

        return max_jump_moves

    def get_board(self):
        return self.board
    

    def add_number_moves(self, color):
        print("color", color)
        if color == CREAM:
            self.board.number_cream_moves = self.board.number_cream_moves + 1
        else:
            self.board.number_black_moves = self.board.number_black_moves + 1

    def init_number_moves(self, color):
        print("init number moves")
        if color == CREAM:
            self.board.number_cream_moves = 0
        else:
            self.board.number_black_moves = 0
    
    def test_skip(moves):
        if isinstance(moves, dict):
            for value in moves.values():
                if isinstance(value, list) and len(value) != 0:
                    return True
        return False
    
    def skip_or_non(self, color):
        mandatory_moves = self.check_mandatory_moves(self.turn)
        if self.selected == color:
            if mandatory_moves:
                self.init_number_moves(color)
            else:
                self.add_number_moves(color)
            

    # Function to store game state
    def get_state(self):
        # Return current game state as a tuple
        board_config = self.get_configuration()  
        current_player = self.turn
        additional_info = (self.board.black_left, self.board.black_kings)  
        return board_config, current_player, additional_info
    
    def get_configuration(self):
        return self.board.get_board()

    

