# Plotting the initial condition
# fonctions d'extraction
fn_eta      = lambda q: q[3,:,:]                     # eta = z_b +h
fn_sol      = lambda q: q[3,:,:] - q[0,:,:]          # z_b
fn_h        = lambda q: q[0,:,:]                     # h
fn_husquare = lambda q: q[1,:,:]**2+q[2,:,:]**2      # h²(u²+v²)
fn_extraire = lambda q: array((fn_sol(q),fn_eta(q))) # (z_b, eta)
fn_hu       = lambda q: q[1,:,:]                     # hu
fn_hv       = lambda q: q[2,:,:]                     # hv
fn_u =  lambda q: np.where(q[0,:,:]>0, (q[1,:,:]/q[0,:,:]), 0)  # u
fn_v =  lambda q: np.where(q[0,:,:]>0, (q[2,:,:]/q[0,:,:]), 0)  # v

figure(figsize=(10,6))
 
pcolormesh(X_grille, Y_grille, sol_0 ,cmap = 'viridis',norm=colors.Normalize(vmax=zmin,vmin=zmax) )
clim(-0.5,0.5)
contour(X_grille, Y_grille, eta_0, colors='r')


eta_masque = ma.masked_where(hauteur_0 < 0.001, eta_0)
clim(-0.5,0.5)
colorbar()
pcolorcells(X_grille, Y_grille, eta_masque, cmap=colors.ListedColormap(['white', 'skyblue']) )
contour(X_grille, Y_grille, hauteur_0, colors='w')
gca().set_aspect(1)
title('Domaine de calcul et lac');


ax1.plot(temps_in, -flux_masse_est,label='CL')
# ax1.set_xlabel(r"$t$ [s]")
# ax1.set_ylabel(r"$\dot M$ [m$^2$/s]")
# plt.text(0.9, 0.9, 'est',
#      horizontalalignment='center',
#      verticalalignment='center',
#      transform = ax1.transAxes)
 
## fig 2 ##
ax2.plot(temps_in, flux_masse_ouest,label='CL')
# ax2.set_xlabel(r"$t$ [s]")
# ax2.set_ylabel(r"$\dot M$ [m$^2$/s]")
# plt.text(0.9, 0.9, 'ouest',
#      horizontalalignment='center',
#      verticalalignment='center',
#      transform = ax2.transAxes)

## fig 3 ##
ax3.plot(temps_in, flux_masse_sud,label='CL')
# ax3.set_xlabel(r"$t$ [s]")
# ax3.set_ylabel(r"$\dot M$ [m$^2$/s]")
# plt.text(0.9, 0.9, 'sud',
#      horizontalalignment='center',
#      verticalalignment='center',
#      transform = ax3.transAxes)

## fig 4 ##
ax4.plot(temps_in, flux_masse_nord,label='CL')
# ax4.set_xlabel(r"$t$ [s]")
# ax4.set_ylabel(r"$\dot M$ [m$^2$/s]")
# plt.text(0.9, 0.9, 'nord',
#      horizontalalignment='center',
#      verticalalignment='center',
#      transform = ax4.transAxes)

seuil_h     = 0.01   # minimum hauteur d'eau
seuil_vague = 0.0002  # bruit AMR typiquement < 1-2 cm

for i in range(NbSim):
    vague_masque[i]    = vague[i]
    hauteur_masque[i]  = hauteur[i]
    bruit = (hauteur[i] < seuil_h) #| (np.abs(vague[i]) < seuil_vague)
    hauteur_masque[i][bruit] = np.nan
    vague_masque[i][bruit]   = np.nan

import matplotlib.colors as mcolors

def make_coolwarm_transparent(vmax, dead_zone=0.05):
    """
    coolwarm avec une zone transparente entre -dead_zone et +dead_zone.
    dead_zone exprimé en fraction de vmax (ex: 0.05 = 5 cm si vmax=1 m).
    """
    cmap_base = plt.cm.coolwarm
    n = 256
    colors_arr = cmap_base(np.linspace(0, 1, n))
    # indices correspondant à la zone morte
    i_low  = int(n * (0.5 - dead_zone / 2))
    i_high = int(n * (0.5 + dead_zone / 2))
    colors_arr[i_low:i_high, 3] = 0   # alpha = 0 → transparent
    return mcolors.LinearSegmentedColormap.from_list("coolwarm_t", colors_arr)


def make_wave_animation_variante(frames, vague_masque, topo_zoom, lake, x0, y0,
                        step = 20, contour_interval=5,
                        vmax=0.5, fps=5, figsize=(10, 8)):
    """
    Animation vue de dessus de la vague (eta - eta_0).
    
    Paramètres
    ----------
    frames       : liste des Solution clawpack
    vague_masque : array (NbSim, ny, nx) pré-calculé (valeurs NaN hors eau)
    topo_zoom    : objet retourné par reading_raster_file (topo recadrée sur le lac)
    lake         : dict avec xmin, xmax, ymin, ymax, water_level
    x0, y0       : coin SW de topo_zoom (retournés par plot_topo)
    vmax         : amplitude max de la colorbar (symétrique ±vmax)
    fps          : images par seconde
    figsize      : taille de la figure
    """
    xmin, xmax = lake['xmin'], lake['xmax']
    ymin, ymax = lake['ymin'], lake['ymax']
    vmax = max([vague[i].max() for i in range(NbSim)] )
    vmin = min([vague[i].min() for i in range(NbSim)] )

    # --- figure de base (fond topo) ---
    fig, ax, x0, y0 = plot_topo(topo_zoom, contour_interval= contour_interval, step=step,
                                 figsize_width=figsize[0])
    ax.set_xlim(xmin - x0  , xmax - x0  )
    ax.set_ylim(ymin - y0  , ymax - y0  )

    # --- artiste imshow (initialisé sur la première frame) ---
    # im = ax.imshow(vague_masque[0], origin='lower',
    #                extent=[xmin - x0, xmax - x0, ymin - y0, ymax - y0],
    #                cmap='viridis',vmin=-vmax, vmax=vmax, alpha=0.95) #,
    # fond fixe : lac initial en bleu
    # dans make_wave_animation, remplacer le bloc colormap par :

    bounds = [-2, -1, 0., 0.5, 1, 2, 3]
    cmap = mpl.colors.ListedColormap([[.9,.9,1],[.6,.6,1],[.3,.3,1],
                                       [0,0,1],[1,.8,.8],[1,.6,.6]])
    cmap.set_under(color=(0,0,0,0))   # transparent si h < seuil
    norm = mpl.colors.BoundaryNorm(bounds, cmap.N)
 

    # im = ax.imshow(vague_masque[3], origin='lower',
    #         extent=[xmin-x0, xmax-x0, ymin-y0, ymax-y0],
    #         cmap=cmap, norm = norm ,alpha = 0.85)

    # Fond fixe : lac initial en bleu
    cmap_lac = ListedColormap([(0, 0, 0, 0),(0.3, 0.6, 1.0, 0.85)])
    ax.imshow((hauteur_0 >= 0.01).astype(float), origin='lower',
            extent=[xmin-x0, xmax-x0, ymin-y0, ymax-y0],
            cmap=cmap_lac, vmin=0, vmax=1, zorder=2)

    # Vague animée avec zone morte transparente
    cmap_vague = make_coolwarm_transparent(vmax, dead_zone=0.05)
    im = ax.imshow(vague_masque[0], origin='lower',
                extent=[xmin-x0, xmax-x0, ymin-y0, ymax-y0],
                cmap=cmap_vague, vmin=-vmax, vmax=vmax,
                alpha=0.9, zorder=3)


 
    fig.colorbar(im, ax=ax, shrink=0.6, label=r'$\eta - \eta_0$ (m)')

    title_text = ax.set_title(rf"$t = {frames[0].t:.1f}$ s")

    # --- fonction de mise à jour ---
    def update(i):
        im.set_data(vague_masque[i])
        # par-dessus : vague animée
        
        title_text.set_text(rf"$t = {frames[i].t:.1f}$ s")
        return im, title_text

    anim = animation.FuncAnimation(fig, update, frames=len(frames),
                                   interval=1000 // fps, blit=True)
    plt.close(fig)   # évite l'affichage statique en plus
    return anim

anim = make_wave_animation_variante(frames, vague_masque, topo_zoom, lake, x0, y0 )
HTML(anim.to_jshtml())
