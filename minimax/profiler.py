# minimax/profiler.py
import time

class AIProfiler:
    def __init__(self):
        self.nodes_visited = 0
        self.cutoffs = 0
        self.tt_hits = 0  
        self.tt_size = 0
        self.start_time = 0
        self.total_time = 0

    def reset(self):
        """Réinitialise les compteurs pour un nouveau tour de recherche."""
        self.nodes_visited = 0
        self.cutoffs = 0
        self.tt_hits = 0
        self.tt_size = 0
        self.start_time = 0
        self.total_time = 0

    def start_timer(self):
        """Démarre le chronomètre."""
        self.start_time = time.perf_counter()

    def stop_timer(self):
        """Arrête le chronomètre et calcule la durée totale."""
        self.total_time = time.perf_counter() - self.start_time

    def increment_nodes(self):
        """Incrémente le nombre de nœuds (états du plateau) visités."""
        self.nodes_visited += 1

    def increment_cutoffs(self):
        """Incrémente le nombre de coupures alpha-bêta."""
        self.cutoffs += 1
    
    def increment_tt_hits(self):
        """Incrémente le compteur de succès dans la table de transposition."""
        self.tt_hits += 1

    def set_tt_size(self, size):
        """Enregistre la taille finale de la table de transposition."""
        self.tt_size = size

    def display_results(self, depth, best_score, best_move_data): 
        """Affiche les résultats de la recherche dans un tableau bien structuré."""
        
        nodes_per_second = int(self.nodes_visited / self.total_time) if self.total_time > 0 else 0
        cutoff_rate = (self.cutoffs / self.nodes_visited * 100) if self.nodes_visited > 0 else 0

        # Formatter la description du meilleur coup pour l'affichage
        move_str = "N/A"
        if best_move_data:
            piece, (end_row, end_col), skipped = best_move_data
            move_str = f"Piece at ({piece.row},{piece.col}) to ({end_row},{end_col})"
            if skipped:
                move_str += f" capturing {len(skipped)} piece(s)"

        print("\n" + "="*70)
        print(" " * 25 + "AI Search Results")
        print("="*70)
        print(f"{'Parameter':<30} | {'Value'}")
        print("-"*70)
        print(f"{'Search Depth':<30} | {depth}")
        print(f"{'Total Time (s)':<30} | {self.total_time:.4f} s")
        print(f"{'Nodes Visited':<30} | {self.nodes_visited:,}")
        print(f"{'Nodes per Second':<30} | {nodes_per_second:,}")
        print(f"{'Alpha-Beta Cutoffs':<30} | {self.cutoffs:,}")
        print(f"{'Cutoff Rate':<30} | {cutoff_rate:.2f}%")
        print(f"{'Transposition Hits':<30} | {self.tt_hits:,}")
        print(f"{'Transposition Table Size':<30} | {self.tt_size:,}")
        print(f"{'Best Score Found':<30} | {best_score:.4f}")
        print(f"{'Best Move Found':<30} | {move_str}")
        print("="*70 + "\n")