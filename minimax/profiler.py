# minimax/profiler.py
import time

class AIProfiler:
    def __init__(self):
        self.nodes_visited = 0
        self.cutoffs = 0
        self.tt_hits = 0  # Pour une future implémentation de la table de transposition
        self.start_time = 0
        self.total_time = 0

    def reset(self):
        """Réinitialise les compteurs pour un nouveau tour de recherche."""
        self.nodes_visited = 0
        self.cutoffs = 0
        self.tt_hits = 0
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

    def display_results(self, depth, best_score):
        """Affiche les résultats de la recherche dans un tableau bien structuré."""
        
        # Calcule les nœuds par seconde pour mesurer la vitesse pure de la recherche.
        nodes_per_second = int(self.nodes_visited / self.total_time) if self.total_time > 0 else 0

        print("\n" + "="*50)
        print(" " * 18 + "AI Search Results")
        print("="*50)
        print(f"{'Parameter':<25} | {'Value'}")
        print("-"*50)
        print(f"{'Search Depth':<25} | {depth}")
        print(f"{'Total Time (s)':<25} | {self.total_time:.4f} s")
        print(f"{'Nodes Visited':<25} | {self.nodes_visited:,}")
        print(f"{'Nodes per Second':<25} | {nodes_per_second:,}")
        print(f"{'Alpha-Beta Cutoffs':<25} | {self.cutoffs:,}")
        print(f"{'Transposition Hits':<25} | {self.tt_hits:,} (non implémenté)")
        print(f"{'Best Score Found':<25} | {best_score:.4f}")
        print("="*50 + "\n")