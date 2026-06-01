def check_domain_in_topo(lake, topo_xmin, topo_xmax, topo_ymin, topo_ymax):
    """
    Vérifie que le domaine lac est entièrement contenu dans l'étendue de la topo.
    Lève une ValueError détaillée si ce n'est pas le cas.
    Arguments :
    - lake : dictionnaire avec les indications sur les caractéristiques du lac
    - topo_xmin, topo_xmax, topo_ymin, topo_ymax : extension du domaine de calcul
    """
    topo = {'xmin': topo_xmin, 'xmax': topo_xmax, 'ymin': topo_ymin, 'ymax': topo_ymax}
    
    checks = {
        'xmin': lake['xmin'] >= topo['xmin'],
        'xmax': lake['xmax'] <= topo['xmax'],
        'ymin': lake['ymin'] >= topo['ymin'],
        'ymax': lake['ymax'] <= topo['ymax'],
    }
    
    errors = [
        f"  lake['{k}'] = {lake[k]:>10.1f}  hors de [{topo['xmin' if 'x' in k else 'ymin']:.1f}, {topo['xmax' if 'x' in k else 'ymax']:.1f}]"
        for k, ok in checks.items() if not ok
    ]
    
    if errors:
        raise ValueError(
            f"Domaine lac incompatible avec la topo ({lake['topography']}) :\n"
            + "\n".join(errors)
            + f"\n\nDomaine lac  : x=[{lake['xmin']}, {lake['xmax']}]  y=[{lake['ymin']}, {lake['ymax']}]"
            + f"\nEtendue topo : x=[{topo['xmin']}, {topo['xmax']}]  y=[{topo['ymin']}, {topo['ymax']}]"
        )
    
    print(f"Le domaine de calcul des vagues est entièrement contenu dans le fichier {lake['topography']}.")

def format_m(x, decimals=1):
    """espace fine insécable"""
    return f"{x:_.{decimals}f}".replace("_", "\u202f")   

def create_mask(proj_dir,topo_dir,topo_files,lake,erase=True,Language='French',mask_cell_size=None):
    """
    Create a mask by clipping the topo file
    Input:
        * proj_dir: string, name of the project directory
        * topo_dir: string, name of the topographic file directory
        * topo_files: dictionary, locates the topo files and gives the no-data code
        * lake: dictionary, provides all the info about the lake
        * mask_cell_size: float, optional. Cell size of the mask raster. If None, uses the topo
          file cell size. Must match the computation grid cell size so that GeoClaw's ForceDry
          mechanism can evaluate the mask correctly at each cell center (GeoClaw interpolates
          binary masks poorly when resolutions differ).
    Output:
        * a raster file with 0 for points inside the lake (wet) and 1 outside the lake (dry).
          This file can be read by geoclaw
    Note that if erase = False, then the dummy file 'masque.asc' is conserved and is compatible with Qgis
    """
    import subprocess
    from module_avac import reading_raster_file_features, reading_raster_file, export_claw_dem
    xmin, xmax, ymin, ymax, nbx, nby, cell_size, \
        dictionary_extent, failure, remarks, grid_type = reading_raster_file_features(topo_dir / lake['topography'])
    if mask_cell_size is not None:
        cell_size = mask_cell_size
    # adresses
    shp       = topo_dir / topo_files["mask_shp"]  # shapefile with the mask surrounding the lake
    out_tif   = proj_dir / "Topo" / "masque.tif"   # dummy file
    out_asc   = topo_dir / "masque_qgis.asc"       # dummy file that can be erased or saved (Qgis compatible)
    path_mask = topo_dir /'mask.asc'               # name of the mask, geoclaw compatible (not Qgis compatible)
    import subprocess
    # creating the mask raster file 'masque.tif'
    subprocess.run([
        "gdal_rasterize",
        "-burn", "0",    # intérieur du polygone → 0 (lac)
        "-init", "1",    # fond → 1 (zones sèches)
        "-at",           # ALL_TOUCHED : inclut les pixels sur le contour
        "-te", f"{xmin}", f"{ymin}", f"{xmax}", f"{ymax}",
        "-tr", str(cell_size), str(cell_size),
        "-ot", "Byte",
        "-of", "GTiff",
        str(shp),
        str(out_tif),
    ], check=True)
    # converting to ESRI raster file
    subprocess.run([
        "gdal_translate",
        "-of", "AAIGrid",
        str(out_tif),
        str(out_asc),
    ], check=True)

    # Export to geoclaw raster file that can be read by geoclaw
    mask_r = reading_raster_file(str(out_asc))
    export_claw_dem(mask_r.x.min(),mask_r.x.max(),mask_r.y.min(),mask_r.y.max(),mask_r.Z.shape[1],mask_r.Z.shape[0],
                    mask_r.Z,name_file =str(path_mask) ,boolean = True, Language = Language )
    # Erasing the dummy files
    if erase: 
        out_asc.unlink()
    else:
        if Language == 'French':
            print("J'ai gardé le fichier temporaire masque.asc (comptatible qgis).")
        else:
            print("I kept the temporary file (qgis compatible) file masque.asc")
    out_tif.unlink()
    if Language == 'French': 
        print(f"Masque créé : {path_mask}")
    else:
        print(f"Mask created: {path_mask}")

def reload_wave(dossier=None):
    """
    Reloads the module module_waves in a robust way... so if changes are made in this file, it is possible to reload the module.

    Input:
        * folder : str, optional. Path to the folder containing the module

    Output:
        * module or None. The reloaded module or None in case of error

    """
    import importlib
    import os
    import sys
    # Chemin explicite
    if dossier is None:
        module_dir = os.getcwd()
    else:
        module_dir = dossier
    
    module_path = os.path.join(module_dir, 'module_waves.py')
    
    # Vérification de l'existence du fichier
    if not os.path.exists(module_path):
        print(f"Error: {module_path} does not exist...")
        return None
    
    try:
        # Add folder to system path
        if module_dir not in sys.path:
            sys.path.insert(0, module_dir)
        
        # Méthode 1: if module has not been imported
        if 'module_waves' not in sys.modules:
            spec = importlib.util.spec_from_file_location("module_waves", module_path)
            module = importlib.util.module_from_spec(spec)
            sys.modules["module_waves"] = module
            spec.loader.exec_module(module)
            print("Module imported for the first time.")
        
        # Méthode 2: if module exists, reload it
        else:
            # Supprimer complètement le module du cache
            if 'module_waves' in sys.modules:
                del sys.modules['module_waves']
            
            # Nettoyer aussi les sous-modules si ils existent
            modules_to_remove = [name for name in sys.modules.keys() 
                               if name.startswith('module_waves.')]
            for module_name in modules_to_remove:
                del sys.modules[module_name]
            
            # Reimporter complètement
            spec = importlib.util.spec_from_file_location("module_waves", module_path)
            module = importlib.util.module_from_spec(spec)
            sys.modules["module_waves"] = module
            spec.loader.exec_module(module)
            print("Module reloaded successfully.")
        
        # Mettre à jour les globals() du notebook
        globals()['module_waves'] = sys.modules['module_waves']
        
        return sys.modules['module_waves']
        
    except Exception as e:
        print(f"ERROR when loading the module: {e}")
        return None
    
def create_boundary_conditions(proj_dir,lake,BC_dir,damping = 0.3):
    """Create the boundary condition files"""
    from yaml import safe_load
    import numpy as np
    from clawpack.visclaw import gridtools
    from clawpack.pyclaw.solution import Solution
    from pathlib import Path
    # définition des dossiers
    avac_output_dir = proj_dir/f"AVAC/_output"
    avac_dir        = proj_dir / "AVAC"
    # chargement du fichier de configuration AVAC
    with open(avac_dir / "AVAC_configuration.yaml") as file:
        config = safe_load(file)
        avac_output = config["output"]
    ntimes          = len(list(avac_output_dir.glob("fort.q*")))
    print(f"J'ai trouvé {ntimes} fichiers de simulation AVAC dans {avac_output_dir}")
    print(f"Format des données de simulations : {avac_output["output_format"]}")

    xmin, xmax = lake['xmin'],  lake['xmax'] 
    ymin, ymax = lake['ymin'],  lake['ymax'] 

    # boundaries of the lake domain
    
    boundaries = ("bottom", "right", "top", "left")
    n = 100
    x = np.hstack((
        np.linspace(xmin, xmax, n, endpoint=True),  # South
        np.full(n, xmax),  # East
        np.linspace(xmax, xmin, n, endpoint=True),  # North
        np.full(n, xmin),  # West
    ))
    y = np.hstack((
        np.full(n, ymin),
        np.linspace(ymin, ymax, n),
        np.full(n, ymax),
        np.linspace(ymax, ymin, n)
    ))

    dist1 = x.max()-x.min()
    dist2 = dist1 + y.max()-y.min()
    dist3 = dist2 + dist1
    dist4 = dist3 + dist2 - dist1
    dist = np.cumsum(np.sqrt(np.diff(x)**2 + np.diff(y)**2))
    dist = np.hstack((0, dist, 2*dist[-1]-dist[-2]))

    def extract(i, outdir=avac_output_dir):
        frame_sol = Solution(i, path=outdir, file_format=avac_output["output_format"])
        q = gridtools.grid_output_2d(
            frame_sol,
            lambda q: q,
            x, y,
            levels = "all",
            return_ma=True
        )
        return q, frame_sol.t

    def write(outdir=BC_dir):
        Path(outdir).mkdir(exist_ok=True)
        for b in boundaries:
            for f in outdir.glob(f"{b}*.npy"):
                f.unlink()
        times = []
        q_list = {'bottom':[], 'right':[], 'top':[], 'left':[]}
        flux_list = {'bottom':[], 'right':[], 'top':[], 'left':[]}
        dy = (ymax-ymin)/(n-1)
        dx = (xmax-xmin)/(n-1)
        for ti in range(ntimes):
            print(f"Sauvegarde du fichier {ti+1:>{4}}/{ntimes}...", end="\r")
            q, t = extract(ti)
            times.append(t)
            h, hu, hv, eta = q
            d_ell_dict = {'bottom':dx, 'right':dy, 'top':dx, 'left':dy}
            normal_dict = {'bottom':[0,-1], 'right':[1,0], 'top':[0,1], 'left':[-1,0]}
            for bi, boundary in enumerate(boundaries):
                s = slice(bi*n, (bi+1)*n)
                data = np.column_stack((x[s], y[s], h[s], hu[s], hv[s]))
                path = outdir / f"{boundary}_{ti:0>{4}}.npy"
                np.savetxt(path, data, comments="")
                dl = d_ell_dict[boundary]
                normal = normal_dict[boundary]
                Q = ((data.T[3].data **2+data.T[4].data **2)**0.5).sum()*dl *damping
                Q_proj = ((data.T[3].data *normal[0]+data.T[4].data * normal[1]) ).sum()*dl *damping
                q_list[boundary].append(Q)
                flux_list[boundary].append(Q_proj)
        np.savetxt(outdir / "times.txt", times)
        print()
        return q_list, flux_list, times
    
    
    q_list, flux_list, times = write()
    print(f"J'ai généré les conditions aux limites entre les temps  t = {times[0]} s et t = {times[-1]}.")
    return q_list, flux_list, times