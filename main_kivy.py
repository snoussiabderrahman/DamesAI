import kivy
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.relativelayout import RelativeLayout
from kivy.uix.widget import Widget
from kivy.graphics import Color, Rectangle, Ellipse
from kivy.uix.image import Image
from kivy.clock import mainthread
import threading
from copy import deepcopy
from minimax.algorithm import NegaMax, transposition_table

# Importer votre logique de jeu existante
from checkers.game import Game
from checkers.constants import BROWN, CREAM, BLACK 

SEARCH_DEPTH = 8

# Créer un widget pour représenter une case du plateau
class SquareWidget(RelativeLayout):
    def __init__(self, row, col, **kwargs):
        super().__init__(**kwargs)
        self.row = row
        self.col = col
        self.is_dark = (row + col) % 2 != 0
        
        with self.canvas.before:
            Color(*(BROWN if self.is_dark else CREAM))
            self.rect = Rectangle(size=self.size, pos=self.pos)
        
        self.bind(size=self._update_rect, pos=self._update_rect)

    def _update_rect(self, instance, value):
        self.rect.pos = instance.pos
        self.rect.size = instance.size
    
    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            # Appeler une fonction dans l'application principale
            App.get_running_app().handle_square_click(self.row, self.col)
            return True
        return super().on_touch_down(touch)

# Le widget racine de notre application
class RootWidget(BoxLayout):
    pass

class DamesApp(App):
    def build(self):
        # Initialiser votre moteur de jeu
        self.game = Game(None) # On passe None car on n'a plus besoin de 'win'
        self.root = RootWidget()
        
        # Créer et ajouter les 8x8 cases au GridLayout
        board_layout = self.root.ids.board_layout
        for row in range(8):
            for col in range(8):
                square = SquareWidget(row=row, col=col)
                board_layout.add_widget(square)

        self.update_board_ui()
        return self.root

    def update_board_ui(self):
        board_layout = self.root.ids.board_layout
        # 'board_layout.children' est en ordre inverse, donc on l'inverse
        square_widgets = reversed(board_layout.children) 
        
        for i, square in enumerate(square_widgets):
            row, col = i // 8, i % 8
            piece = self.game.board.get_piece(row, col)
            
            square.clear_widgets() # Enlever l'ancienne pièce
            
            if piece != 0:
                # Dessiner la pièce (cercle)
                piece_widget = Widget(size_hint=(0.7, 0.7), pos_hint={'center_x': 0.5, 'center_y': 0.5})
                with piece_widget.canvas:
                    Color(*(piece.color)) # Utiliser la couleur de la pièce
                    Ellipse(size=piece_widget.size, pos=piece_widget.pos)
                square.add_widget(piece_widget)

                # Ajouter la couronne si c'est un roi
                if piece.king:
                    crown_widget = Image(source='assets/crown.png', size_hint=(0.5, 0.5), pos_hint={'center_x': 0.5, 'center_y': 0.5})
                    square.add_widget(crown_widget)

    def handle_square_click(self, row, col):
        # C'est ici que vous appelez votre logique de jeu existante
        self.game.select(row, col)
        # Après chaque action, mettez à jour l'interface
        self.update_board_ui() 
        # Mettez aussi à jour les labels de la sidebar
    
        self.update_sidebar_ui()
    def check_for_ai_move(self):
        # Cette fonction sera appelée régulièrement pour lancer l'IA
        ai_color = BLACK if self.game.player_color == CREAM else CREAM
        if self.game.turn == ai_color and not self.ai_is_thinking:
            self.ai_is_thinking = True
            self.update_sidebar_ui()
            
            # Lancer le calcul dans un thread
            board_copy = deepcopy(self.game.get_board())
            # ...
            threading.Thread(target=self.run_ai_calculation, args=(...)).start()
    
    # --- Fonction wrapper pour le calcul de l'IA ---
    def run_ai_calculation(board_to_search, ai_color, killer_moves, profiler, result_container, position_history, moves_since_capture):
        """
        Cette fonction sera exécutée dans un thread séparé sur une COPIE du plateau.
        """
        #profiler.reset()
        #profiler.start_timer()
        transposition_table.clear()
        
        # Lancer la recherche NegaMax
        value, best_move_data = NegaMax(board_to_search, SEARCH_DEPTH, ai_color, float("-inf"), float("inf"), killer_moves, profiler, position_history, moves_since_capture)
        
        #profiler.stop_timer()
        #profiler.set_tt_size(len(transposition_table))
        #profiler.display_results(SEARCH_DEPTH, value, best_move_data)
        result_container.append(best_move_data)
    
    @mainthread
    def on_ai_calculation_complete(self, best_move_data):
        # Cette fonction est garantie de s'exécuter sur le thread principal de Kivy
        self.ai_is_thinking = False
        if best_move_data:
            self.game.ai_move(best_move_data) # Ceci va lancer l'animation
        
        # On met à jour l'UI après le coup
        self.update_board_ui()
        self.update_sidebar_ui()

if __name__ == '__main__':
    DamesApp().run()