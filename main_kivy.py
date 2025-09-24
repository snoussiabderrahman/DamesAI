import kivy
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.relativelayout import RelativeLayout
from kivy.uix.widget import Widget
from kivy.graphics import Color, Rectangle, Ellipse
from kivy.uix.image import Image

# Importer votre logique de jeu existante
from checkers.game import Game
from checkers.constants import BROWN, CREAM, BLACK # Et les autres couleurs

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

if __name__ == '__main__':
    DamesApp().run()