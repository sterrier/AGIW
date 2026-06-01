Un projet de vague d'impulsion doit respecter l'architecture des répertoires, à savoir un répertoire dit de projet (noté proj_dir) qui contient :
- le répertoire AVAC : il contient le code de calcul des avalanches
- le répertoire Topo : il contient l'ensemble des fichiers topographiques nécessaires au calcul
- le répertoire Vagues : il comprend l'ensemble des scripts nécessaires au calcul des vagues
Les fichiers de paramètres sont des fichiers yaml (configuration_AVAC.yaml, AVAC_parameters et impulse_configuration.yaml). Ces fichiers sont générés par les cahiers jupyter : AVAC.ipynb, Waves_preprocess.ipynb et Waves_postprocess.ipynb). Tout se fait à l'aide de ces cahiers jupyter. La seule exception est la création d'animations 3D avec pyvista qui, pour l'heure, se fait en ligne de commande.

# Prérequis :
- python > 3.0
- clawpack > 5.9
- AVAC > 4.3
Les codes clawpack et AVAC font appel à des bibliothèques à charger indépendamment.

Tous les paramètres sont passés à geoclaw sous forme de fichiers de configuration yaml qu'il faut remplir dans les cahiers jupyther (dictionnaires). Une fois que les fichiers de configuration ont été exportés à partir des cahiers jupyter, il est toujours possible de modifier directement impulse_configuration.yaml et AVAC_configuration.yaml dans un éditeur de texte sans repasser par les cahiers jupyter.

# Procédures de calcul :
1. Faire le calcul des avalanches dans le répertoire AVAC. Tout se gère à partir de AVAC.ipynb. Il faut impérativement placer un fichier de topographie de type raster et un shape fournissant les zones de départ dans le dossier /Topo. Puis remplir les dictionnaires de paramètres et aller de cellule en cellule pour générer les conditions initiales et le fichier topo compatible avec AVAC. Il est possible de faire une animation en exécutant le script pyvista_postprocess.py (voir infra).
2. Se placer dans le répertoire du projet et lancer Waves_preprocess.ipynb. Il faut en général un shapefile (polyline) qui renseigne sur le contour du lac. Cela est nécessaire pour l'initialisation de la hauteur d'eau dans la retenue. Les paramètres sont dans les différents dictionnaires topo_files, lake, computation, dict_gauges. Il faut notamment définir le domaine de calcul [xmin, xmax, ymin, ymax]. Ce cahier lit les simulations d'AVAC et les transforme en conditions aux limites pour le calcul de vagues. Ces conditions sont écrites dans le répertoire CL sous la forme de fichiers texte npy (un fichier par bord [est, ouest, nord, sud] du domaine de calcul et par unité de temps).
3. Se placer dans le répertoire Vagues et exécuter les cellules de Waves_postprocess.ipynb. Ce cahier lance l'exécution et lit les résultats, qui sont reportés sous forme de cartes, profils en long et animation Il est possible de faire une animation en exécutant le script pyvista_postprocess.py.


# Fonctionnement de pyvista_postprocess.py
Le script ouvre une fenêtre Qt et permet de visualiser en 3D le résultat d'une simulation. Il y a des paramètes par défaut, ce qui fait que l'exécution "python pyvista_postprocess.py" dans la commande de prompt (en se plaçant soit dans Vagues soit dans AVAC doit être suffisante à créer la fenêtre Qt et visualiser la simulation. Pour faire défiler la simulation, il faut appuyer sur les flèches du clavier (droite/gauche) ou bien les touches (k et j). Les flèches haut/bas agrandit ou rapetisse la vue 3D. Avec la souris on peut modifier l'angle de perspective et zoomer. Pour créer une animation, il faut appuyer sur m (cela lance l'animation au temps affiché dans le fenêtre). On peut se reporter aux lignes 230 à 259 pour voir les options. Par exemple, pour changer la coloration (colormap), on exécute : ""python pyvista_postprocess.py -m 'coolwarm' 'viridis' "

