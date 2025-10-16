import pygame
from .constants import CREAM, BLACK, BLUE, SQUARE_SIZE, ROWS, COLS
from checkers.board import Board
from minimax.algorithm import zobrist_turn_black
from copy import deepcopy

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
        self.position_history = {} # Dictionnaire pour compter les répétitions de hash
        self.moves_since_capture = 0
        self.draws = 0
        self.player_color = CREAM
        self.last_ai_depth = 0
        self.last_ai_score = 0.0
        self.last_ai_time = 0.0
        self.move_counter = 0 # Compteur de demi-coups total
        self.last_ai_plies_to_win = 0 # Nombre de demi-coups calculé par l'IA
        self.calculation_move_counter = -1 # Le moment où le calcul a été fait
        self.game_state_history = [] # Historique des états du jeu pour l'annulation des coups
    
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
        
        # N'afficher les coups que si c'est au tour du joueur humain
        if not self.is_animating() and not self.ai_is_thinking and self.turn == self.player_color:
            self.draw_valid_moves(self.valid_moves)

    # === Pour changer la couleur du joueur ===
    def set_player_color(self, color):
        """Définit la couleur du joueur et réinitialise la partie."""
        # Si le joueur clique sur la couleur qu'il a déjà, on ne fait rien.
        # Cela évite de réinitialiser la partie accidentellement.
        if self.player_color == color:
            return
        
        self.player_color = color
        self.black_wins, self.cream_wins = self.cream_wins, self.black_wins
        self.reset() # Redémarre une nouvelle partie avec les bons paramètres
            
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
        """Termine l'animation et met à jour l'état du jeu ET l'historique."""
        if not self.animation_data: return

        # === Sauvegarder l'état AVANT d'effectuer le coup ===
        # On sauvegarde les données essentielles qui définissent l'état actuel.
        current_state = {
            'board': deepcopy(self.board),
            'turn': self.turn,
            'moves_since_capture': self.moves_since_capture,
            'position_history': self.position_history.copy(),
            'move_counter': self.move_counter,
            # On ne sauvegarde pas les stats de l'IA, elles ne font pas partie de l'état du jeu
        }
        self.game_state_history.append(current_state)

        piece = self.animation_data['piece']
        final_row = int(self.animation_data['target_y'] // SQUARE_SIZE)
        final_col = int(self.animation_data['current_x'] // SQUARE_SIZE)
        
        # On utilise la liste des pièces visuellement retirées
        removed_pieces = self.animation_data.get('visually_removed', [])
        
        # 1. Retirer les pièces (cette fonction met à jour le hash)
        if removed_pieces:
            self.board.remove_and_get_skipped(removed_pieces)
            self.moves_since_capture = 0
        else:
            self.moves_since_capture += 1
            
        # 2. Déplacer la pièce (cette fonction met à jour le hash et gère la promotion)
        self.board.make_move(piece, final_row, final_col)
        
        self.change_turn()
        self.move_counter += 1  # Incrémenter le compteur de demi-coups
        
        # Mettre à jour l'historique des positions
        current_hash = self.board.zobrist_hash
        if self.turn == BLACK:
            current_hash ^= zobrist_turn_black
        
        self.position_history[current_hash] = self.position_history.get(current_hash, 0) + 1
        
        self.animation_data = None
    
    def _init(self):
        self.selected = None
        self.board = Board()
        self.turn = CREAM
        self.valid_moves = {}
        self.game_over = False
        self.winner_message = ""
        self.position_history = {}
        self.moves_since_capture = 0
        self.last_ai_depth = 0
        self.last_ai_score = 0.0
        self.last_ai_time = 0.0
        self.move_counter = 0
        self.last_ai_plies_to_win = 0
        self.calculation_move_counter = -1
        self.game_state_history = []
    
    def update_winner(self):
        """Vérifie s'il y a un gagnant et met à jour l'état du jeu."""
        winner = self.board.winner(self.turn, self.position_history, self.moves_since_capture)
        if winner is not None:
            self.game_over = True
            self.winner_message = winner
            if "black" in winner.lower():
                self.black_wins += 1
            elif "cream" in winner.lower():
                self.cream_wins += 1
            elif "draw" in winner.lower():
                self.draws += 1
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
        respectent la règle de la capture maximale. (Version finale et corrigée)
        """
        all_capture_moves = []
        max_skipped_len = 0

        # Étape 1 : Collecter toutes les captures et trouver la VRAIE longueur maximale
        for piece in self.board.get_all_pieces(color):
            valid_moves = self.board.get_valid_moves(piece)
            for move, details in valid_moves.items():

                # --- Extraire la VRAIE liste des pièces sautées ---
                skipped_list = []
                if isinstance(details, dict):
                    skipped_list = details.get('skipped', [])
                elif isinstance(details, list) and details:
                    skipped_list = details

                if skipped_list: # Si c'est bien une capture
                    all_capture_moves.append((piece, move, details))
                    # On utilise la longueur de la VRAIE liste pour trouver le max
                    if len(skipped_list) > max_skipped_len:
                        max_skipped_len = len(skipped_list)
        
        if not all_capture_moves:
            return []

        # Étape 2 : Filtrer pour ne garder que les coups de la VRAIE longueur maximale
        final_mandatory_moves = []
        for p, m, details in all_capture_moves:
            # On extrait à nouveau la VRAIE liste pour la comparaison
            skipped_list = details.get('skipped', []) if isinstance(details, dict) else details
            if len(skipped_list) == max_skipped_len:
                final_mandatory_moves.append((p, m, details))
        
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

    def get_board(self):
        return self.board
    
    def get_configuration(self):
        return self.board.get_board()
    
    # === La logique pour annuler un coup ===
    def undo_move(self):
        """
        Annule le dernier coup du joueur ET la réponse de l'IA.
        Restaure le jeu à l'état d'avant le dernier coup du joueur.
        """
        # Le joueur ne peut cliquer sur "Undo" que lorsque c'est son tour.
        # Cela signifie qu'un coup du joueur et un coup de l'IA ont eu lieu.
        # Nous avons donc besoin d'au moins 2 états dans l'historique.
        if len(self.game_state_history) < 2:
            print("Undo failed: Not enough history to undo a full turn.")
            return

        # 1. Annuler la réponse de l'IA (on retire l'état de la pile, mais on ne l'utilise pas)
        self.game_state_history.pop()
        
        # 2. Annuler le coup du joueur (on retire l'état et on le restaure)
        state_to_restore = self.game_state_history.pop()
        
        self.board = state_to_restore['board']
        self.turn = state_to_restore['turn']
        self.moves_since_capture = state_to_restore['moves_since_capture']
        self.position_history = state_to_restore['position_history']
        self.move_counter = state_to_restore['move_counter']

        # Réinitialiser les états d'interaction et de fin de partie
        self.selected = None
        self.valid_moves = {}
        self.game_over = False
        self.winner_message = ""
        # On efface les dernières stats de l'IA car elles ne sont plus pertinentes
        self.last_ai_score = 0.0
        self.last_ai_depth = 0
        self.last_ai_time = 0.0
        
