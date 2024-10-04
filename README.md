# DamesAI
checkers game  against AI

== Règles ==
------------------------------------------------------------------------------
* Taille du plateau: 64 cases (8 x 8) ;
* Nombre de pions : 24 (2 x 12) ;
* Orientation du plateau: la grande diagonale relie la gauche de chaque joueur ;
* Cases utilisées : cases sombres ;
* Joueur qui commence : Blancs ;
* Prise autorisée des pions :

   1-Diagonales avant seulement ;
  
   2-Les rafles sont limitées à trois prises ;
  
   3-Un pion ne peut pas prendre une dame ;
  
* Dame : Ne se déplace que d'une case vers l'avant ou l'arrière ;
* Contrainte de prise : prise majoritaire obligatoire ;
* Prise qualitative :

   1-Entre deux rafles de valeurs équivalente, il faut si possible effectuer la rafle avec une dame plutôt qu'un pion ;
  
   2-Une dame ayant le choix entre deux rafles comprenant le même nombre de pièces, doit choisir celle qui comprend le plus de dames ;
  
   3-Une dame ayant le choix entre deux rafles comprenant le même nombre de dames et de pions doit choisir entre celles qui permettent de capturer une dame adverse le plus rapidement ;
  
* Souffler : interdit depuis 1936.
