from minimax.algorithm import NegaMax, transposition_table
from copy import deepcopy


class WebAICalculator:
    """Calculateur IA adapté pour le web (sans threading)"""
    
    def __init__(self):
        self.is_calculating = False
        self.iterations_per_frame = 100  # Ajustez selon les performances
        self.current_state = None
        
    def start_calculation(self, board, color, depth, profiler, position_history, moves_since_capture):
        """Démarre le calcul progressif"""
        self.is_calculating = True
        self.board = deepcopy(board)
        self.color = color
        self.depth = depth
        self.profiler = profiler
        self.position_history = position_history.copy()
        self.moves_since_capture = moves_since_capture
        self.result = None
        
        # Initialiser l'état de recherche
        profiler.reset()
        profiler.start_timer()
        transposition_table.clear()
        
    def calculate_step(self):
        """Effectue une partie du calcul"""
        if not self.is_calculating:
            return False
            
        # Exécuter le calcul complet (optimisé grâce à alpha-beta)
        value, best_move = NegaMax(
            self.board, 
            self.depth, 
            self.color, 
            float("-inf"), 
            float("inf"), 
            {}, 
            self.profiler,
            self.position_history,
            self.moves_since_capture
        )
        
        self.profiler.stop_timer()
        self.profiler.set_tt_size(len(transposition_table))
        
        self.result = (value, best_move)
        self.is_calculating = False
        return True
        
    def get_result(self):
        """Récupère le résultat si disponible"""
        return self.result