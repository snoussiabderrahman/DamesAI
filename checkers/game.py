import pygame
from .constants import CREAM, BLACK, BLUE, SQUARE_SIZE, ROWS, COLS
from checkers.board import Board


class Game:
    def __init__(self, win):
        self._init()
        self.win = win
        self.animation_data = None  # Stockera les infos du coup à animer
        self.animation_speed = 15  # Vitesse de l'animation (plus élevé = plus rapide)
        self.black_wins = 0
        self.cream_wins = 0
        self.game_over = False
        self.winner_message = ""
        self.ai_is_thinking = False
    
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
            
    # === FONCTION CENTRALE POUR TOUTES LES ANIMATIONS ===
    def start_move_animation(self, piece, end_row, end_col, move_details):
        """
        Prépare et lance l'animation pour n'importe quel coup (IA ou joueur).
        """
        path = []
        final_skipped_list = []

        if isinstance(move_details, dict):
            final_skipped_list = move_details.get('skipped', [])
        elif isinstance(move_details, list):
            final_skipped_list = move_details

        if isinstance(move_details, dict) and 'path' in move_details:
            # Cas du roi : le chemin est pré-calculé
            for i, (r, c) in enumerate(move_details['path']):
                path.append({
                    'target_row': r, 'target_col': c,
                    'skipped_piece': final_skipped_list[i] if i < len(final_skipped_list) else None
                })
        elif final_skipped_list:
            # Cas du pion : on calcule le chemin
            current_pos = (piece.row, piece.col)
            for skipped_p in final_skipped_list:
                land_row = skipped_p.row + (skipped_p.row - current_pos[0])
                land_col = skipped_p.col + (skipped_p.col - current_pos[1])
                path.append({
                    'target_row': land_row, 'target_col': land_col,
                    'skipped_piece': skipped_p
                })
                current_pos = (land_row, land_col)
        else:
            # Mouvement simple
            path.append({'target_row': end_row, 'target_col': end_col, 'skipped_piece': None})

        self.animation_data = {
            'piece': piece,
            'path': path,
            'current_x': piece.x,
            'current_y': piece.y,
            'target_x': None,
            'target_y': None,
            'visually_removed': []
        }
        
        self._start_next_animation_leg()

    def ai_move(self, move_data):
        """
        Fonction déclencheur pour l'IA. Traduit les données de la copie de l'IA
        et appelle la fonction d'animation centrale.
        """
        if move_data is None: return

        piece_from_copy, (end_row, end_col), move_details_from_copy = move_data
        
        # Traduction des objets de la copie vers le plateau principal
        start_row, start_col = piece_from_copy.row, piece_from_copy.col
        piece_on_main_board = self.board.get_piece(start_row, start_col)
        
        if piece_on_main_board == 0: return

        # Traduire les pièces sautées
        final_move_details = move_details_from_copy
        if isinstance(move_details_from_copy, dict):
            skipped_list_main = []
            for p_copy in move_details_from_copy.get('skipped', []):
                p_main = self.board.get_piece(p_copy.row, p_copy.col)
                if p_main != 0: skipped_list_main.append(p_main)
            final_move_details['skipped'] = skipped_list_main
        elif isinstance(move_details_from_copy, list):
            skipped_list_main = []
            for p_copy in move_details_from_copy:
                p_main = self.board.get_piece(p_copy.row, p_copy.col)
                if p_main != 0: skipped_list_main.append(p_main)
            final_move_details = skipped_list_main
            
        # Appel à la fonction d'animation centrale avec des objets "sûrs"
        self.start_move_animation(piece_on_main_board, end_row, end_col, final_move_details)
    
    def _start_next_animation_leg(self):
        """Prépare la prochaine étape de l'animation à partir du chemin."""
        if self.animation_data and self.animation_data['path']:
            # On prend la prochaine étape de la file d'attente
            next_leg = self.animation_data['path'].pop(0)
            
            # On définit la nouvelle cible
            self.animation_data['target_x'] = next_leg['target_col'] * SQUARE_SIZE + SQUARE_SIZE // 2
            self.animation_data['target_y'] = next_leg['target_row'] * SQUARE_SIZE + SQUARE_SIZE // 2
            
            # On cache la pièce qui vient d'être sautée
            if next_leg['skipped_piece']:
                self.animation_data['visually_removed'].append(next_leg['skipped_piece'])
            return True
        return False

    def _update_animation(self):
        """Fait avancer l'animation d'une étape vers la cible ACTUELLE."""
        data = self.animation_data
        if not data or data.get('target_x') is None:
            return

        dx = data['target_x'] - data['current_x']
        dy = data['target_y'] - data['current_y']
        distance = (dx**2 + dy**2)**0.5
        
        if distance < self.animation_speed * 2: # Une marge pour éviter de vibrer
            # L'étape actuelle est terminée
            data['current_x'] = data['target_x']
            data['current_y'] = data['target_y']
            
            # Y a-t-il une autre étape dans le chemin ?
            if not self._start_next_animation_leg():
                # Non, le chemin est vide. L'animation est complètement terminée.
                self._finalize_animation()
        else:
            # On déplace la pièce d'un pas vers sa cible
            data['current_x'] += self.animation_speed * (dx / distance)
            data['current_y'] += self.animation_speed * (dy / distance)

    def _finalize_animation(self):
        """Termine l'animation et applique le coup final à l'état du jeu."""
        if not self.animation_data:
            return
            
        piece = self.animation_data['piece']
        # La position finale est celle de la dernière cible
        final_row = int(self.animation_data['target_y'] // SQUARE_SIZE)
        final_col = int(self.animation_data['current_x'] // SQUARE_SIZE)
        
        # Applique réellement les changements à l'état du plateau
        self.board.remove(self.animation_data['visually_removed'])
        self.board.move(piece, final_row, final_col)
        self.change_turn()
        
        # Réinitialise l'état de l'animation
        self.animation_data = None
    
    def _init(self):
        self.selected = None
        self.board = Board()
        self.turn = CREAM
        self.valid_moves = {}

        self.game_over = False
        self.winner_message = ""
    
    def update_winner(self):
        """Vérifie s'il y a un gagnant et met à jour l'état du jeu."""
        winner = self.board.winner(self.turn)
        if winner is not None:
            self.game_over = True
            self.winner_message = winner
            if "black" in winner.lower():
                self.black_wins += 1
            elif "cream" in winner.lower():
                self.cream_wins += 1
            return True
        return False

    def winner(self, color):
        return self.board.winner(color)

    def reset(self):
        """Réinitialise la partie, mais conserve les scores."""
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
            if self._move(row, col):
                return True
            else:
                # Le mouvement a échoué. On désélectionne la pièce et on efface ses mouvements.
                self.selected = None
                self.valid_moves = {}
                # On continue pour voir si ce nouveau clic correspond à une NOUVELLE sélection.
        
        # Étape 2 : Gérer la tentative de SÉLECTION d'une nouvelle pièce.
        piece = self.board.get_piece(row, col)

        if piece == 0 or piece.color != self.turn:
            self.selected = None
            self.valid_moves = {}
            return False

        # --- LOGIQUE DE FILTRAGE GLOBAL (LA PLUS IMPORTANTE) ---
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
                print("Invalid move: another piece must perform a longer capture.")
                self.selected = None
                self.valid_moves = {}
                return False
        else:
            # Cas 2 : Pas de captures obligatoires.
            possible_moves = self.board.get_valid_moves(piece)
            if possible_moves:
                self.selected = piece
                self.valid_moves = possible_moves
                return True
            else:
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
        """
        Fonction déclencheur pour le joueur. Au lieu de déplacer la pièce,
        elle appelle maintenant la fonction d'animation centrale.
        """
        piece_on_board = self.board.get_piece(row, col)
        if self.selected and piece_on_board == 0 and (row, col) in self.valid_moves:
            
            move_details = self.valid_moves[(row, col)]
            
            # Appel à la fonction d'animation centrale
            self.start_move_animation(self.selected, row, col, move_details)
            
            # Important : on désélectionne la pièce car le coup est "engagé"
            self.selected = None
            self.valid_moves = {}
            
            return True # Le déclenchement de l'animation a réussi
        
        return False # Le clic n'était pas un coup valide

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

