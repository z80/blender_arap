import numpy as np
from scipy.sparse import csr_matrix
from scipy.sparse.linalg import spsolve
from scipy.sparse.csgraph import dijkstra

from .utils_distance   import *
from .utils_transforms import *
from .utils_geometry   import *
from .utils_falloff    import *

VERY_FAR_DISTANCE = 1.0e10

def smooth_transform( V, F, fixed_data, use_algorithm, step_2, normal_importance, num_iterations, step_3, apply_rigid_transform, decay_radius, gp_radius, gp_regularization, id_power, id_epsilon ):

    qty = len( fixed_data )
    fixed_positions  = np.zeros( (qty, 3) )
    fixed_vertices   = []
    distance_metrics = []
    influence_radii  = np.ones( (qty,) ) * gp_radius

    for idx, vert in enumerate(fixed_data):
        index  = vert.get( "index", 0 )
        pos    = vert.get( "pos", np.zeros( (3,) ) )
        metric = vert.get( "metric", "geodesic" )
        radius = vert.get( "radius", gp_radius )

        fixed_vertices.append( index )
        fixed_positions[idx] = pos
        distance_metrics.append( metric )
        influence_radii[idx] = radius

    # Compute distances from anchor points to all vertices.
    distances = compute_distances( V, F, fixed_vertices, distance_metrics )

    # Only pick reachable vertices.
    # They are re-packed so that transform algorithms should work as usual.
    unreachable_V, unreachable_indices, \
    reachable_V, reachable_F, reachable_distances, reachable_indices \
                            = extract_reachable_vertices(V, F, fixed_vertices, fixed_positions, distances)

    # Modify reachable distances so that it doesn't contain negative numbers.
    negative_inds = np.where( reachable_distances < 0.0 )
    reachable_distances[negative_inds] = VERY_FAR_DISTANCE

    # Apply the inverse distance transform first.
    if use_algorithm == 'inverse_dist':
        modified_reachable_V, R, T = inverse_distance_transform( reachable_V, fixed_vertices, fixed_positions, reachable_distances, decay_radius, influence_radii, id_power, id_epsilon, apply_rigid_transform )
    elif use_algorithm == 'gaussian_proc':
        #modified_reachable_V, R, T = gaussian_process_transform( reachable_V, fixed_vertices, fixed_positions, reachable_distances, mean_radius, normalized=normalized_gp )
        modified_reachable_V, R, T = gaussian_process_transform( reachable_V, fixed_vertices, fixed_positions, reachable_distances, decay_radius, influence_radii, gp_regularization, apply_rigid_transform )
    
    # This is an initial approximaion for elastic transform.
    V_idt = modified_reachable_V.copy()

    # Apply rigid transform to unreachable vertices.
    # That's the best we can do for them.
    modified_unreachable_V = rigid_transform( unreachable_V, R, T )

    
    # If we should run the elastic transform, do that.
    if step_2 and (V_idt is not None):
        #import pdb
        #pdb.set_trace()

        # V, F, distances, fixed_vertices, fixed_positions, iterations, max_importance, min_importance, influence_radii, falloff_func, V_initial=None
        V_arap = elastic( reachable_V, reachable_F, reachable_distances, fixed_vertices, fixed_positions, num_iterations, normal_importance, 1.0, influence_radii, falloff_function, V_idt )
        modified_reachable_V = V_arap

        if step_3:
            modified_reachable_V = apply_proportional_displacements( V_idt, V_arap, reachable_distances, influence_radii, falloff_function )

    # Recombine transforms back together.
    V_new = V.copy()
    V_new[unreachable_indices] = modified_unreachable_V
    V_new[reachable_indices]   = modified_reachable_V

    return V_new



















