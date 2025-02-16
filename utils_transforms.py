import numpy as np
from scipy.sparse import csr_matrix
from scipy.sparse.linalg import spsolve
from scipy.sparse.csgraph import dijkstra


from .utils_geometry import *
from .utils_falloff import *



def gaussian_process_transform(V, fixed_vertices, fixed_positions, distances, decay_radius, influence_radius, regularization=0.0001, apply_rigid_rotation=False):
    """
    Apply rigid body transformation and interpolate displacements using Gaussian Process.

    Parameters:
    V (numpy.ndarray): Nx3 array of 3D points.
    fixed_vertices (numpy.ndarray): Indices of fixed vertices (K,).
    fixed_positions (numpy.ndarray): Target positions of the fixed vertices (Kx3).
    distances (numpy.ndarray): Precomputed distances between fixed points and all points (KxN).

    Returns:
    numpy.ndarray: Updated points after applying the rigid body transform and interpolated displacements.
    """
    
    if apply_rigid_rotation:
        #Calculate rigid transform first.
        R, T = get_rigid_transform( V, fixed_vertices, fixed_positions )

        # Step 5: Apply the rigid body transform to all points
        V_transformed = np.dot(R, V.T).T + T

        # Step 6: Compute the displacements of modified points after rigid body transform
        modified_displacements = fixed_positions - V_transformed[fixed_vertices]

    else:
        V_transformed = V.copy()
        modified_displacements = fixed_positions
        R = None
        T = None

    # Step 7: Interpolate displacements using Gaussian Process
    # Use the RBF kernel (Squared Exponential)
    def rbf_kernel(distances, length_scale):
        #return np.exp( -(distances / length_scale)**2 )
        return np.exp( -(distances / length_scale) )

    # Compute kernel matrices
    # K has to be symmetric. Otherwise there is no exact match in the points where the function is defined.
    K = rbf_kernel(distances[:, fixed_vertices], influence_radius)  # Kernel for fixed points
    # Add a regularization term for numerical stability
    K_regularization = regularization * np.eye(K.shape[0])
    K += K_regularization

    K_star = rbf_kernel( distances, influence_radius[:, None] )                # Kernel between all points and fixed points
    decay_weights = rbf_kernel( distances, decay_radius )
    K_star *= decay_weights

    #if normalized:
    #    K_star_lengths = np.linalg.norm(K_star, axis=0)
    #    K_star = K_star / K_star_lengths[None, :]

    # Solve for weights (zero-noise GP assumes K is invertible)
    weights = np.linalg.solve(K, modified_displacements)

    # Interpolate displacements
    interpolated_displacements = np.dot(K_star.T, weights)

    # Step 8: Update all points with interpolated displacements
    V_updated = V_transformed + interpolated_displacements

    V_updated[fixed_vertices] = fixed_positions

    return V_updated, R, T





def inverse_distance_transform( V, fixed_vertices, fixed_positions, distances, decay_radius, influence_radii, power=2, epsilon=1.0e-3, apply_rigid_rotation=False ):
    """
    I believe, this one implements something similar to Radial Basis Functions (RBF) based transform 
    best I understand the concept of RBF except I use geodesic distance in place of euclidean distance.
    """

    #import pdb
    #pdb.set_trace()

    # Indices where the distance is very small.
    below_threshold_indices = np.where(distances < epsilon)
    # Create a mask for all points
    mask = np.full(distances.shape, True)
    mask[below_threshold_indices] = False
    
    if apply_rigid_rotation:
        # Applying rigid transform, i.e. rotaton and translation.
        R, T = get_rigid_transform( V, fixed_vertices, fixed_positions )
        new_positions = np.dot( R, V.T ).T + T

        # Compute displacements for fixed positions.
        start_positions = new_positions[fixed_vertices]
        displacements   = fixed_positions - start_positions

    else:
        new_positions   = V.copy()
        start_positions = V[fixed_vertices]
        displacements   = fixed_positions - start_positions
        R = None
        T = None

    num_points = V.shape[0]

    for vert_idx in range(num_points):
        # Check for exact match
        if np.all( mask[:, vert_idx] ):
            # Apply inverse distance weighting
            weights = 1.0 / (distances[:, vert_idx]/influence_radii + epsilon)**power
            sum_weights = np.sum(weights)
            displacement_per_target = (weights[:, None] * displacements)
            decay_weights = falloff_function( distances[:, vert_idx], decay_radius )
            displacement_per_target *= decay_weights[:, None]
            displacement = np.sum( displacement_per_target, axis=0 ) / sum_weights

        else:
            exact_match_index = np.argmin(distances[:, vert_idx])
            displacement = displacements[exact_match_index]

        new_positions[vert_idx] += displacement

    return new_positions, R, T



def rigid_transform( V, R, T ):
    new_positions = np.dot( R, V.T ).T + T
    return new_positions




def elastic(V, F, distances, fixed_vertices, fixed_positions, iterations, max_importance, min_importance, influence_radii, falloff_func, V_initial=None):
    """
    Executes the As-Rigid-As-Possible (ARAP) optimization.
    
    Parameters:
    - V: np.array of shape (N, 3) containing the vertices of the mesh.
    - F: np.array of shape (M, 3) containing the faces of the mesh.
    - fixed_vertices: np.array of indices of vertices that are fixed.
    - fixed_positions: np.array of shape (num_fixed, 3) containing the positions of the fixed vertices.
    - iterations: int, number of iterations for the optimization process (default is 10).
    
    Returns:
    - V_new: np.array of shape (N, 3) containing the new vertex positions after ARAP optimization.
    """
    # Compute geodesic distances and influences for all vertices.
    importances = compute_normal_importances( V, F, distances, fixed_vertices, max_importance, min_importance, influence_radii, falloff_func )
 
    # Compute cotangent weights
    cotangent_weights = compute_cotangent_weights(V, F)
    connections, max_connections_qty = get_edge_lists(V, F)

    # Initialize variables
    N         = V.shape[0]
    faces_qty = F.shape[0]

    if V_initial is None:
        V_new = V.copy()
    else:
        V_new = V_initial.copy()

    #import pdb
    #pdb.set_trace()

    for idx, abs_idx in enumerate(fixed_vertices):
        v = fixed_positions[idx]
        V_new[abs_idx] = v

    # Set of fixed vertex indices for fast lookup.
    fixed_vertices_set = set( fixed_vertices )

    # Also a dictionary of indices in the array by absolute vertex index for fast lookup.
    fixed_vertex_indices = {}
    for i, idx in enumerate( fixed_vertices ):
        fixed_vertex_indices[idx] = i

    # Do the same for vertex indices. Because there are fixed vertices, when constructing 
    # the optimization equation need to skip fixed indices.
    variable_vertex_indices = {}
    idx = 0
    for i in range(N):
        is_fixed = i in fixed_vertices_set
        if is_fixed:
            continue
        variable_vertex_indices[i] = idx
        idx += 1

    variable_verts_qty = len(variable_vertex_indices)
    fixed_verts_qty    = len(fixed_vertices)

    # Define start positions
    start_positions = np.zeros( (fixed_verts_qty, 3) )
    for idx, abs_idx in enumerate(fixed_vertices):
        v = V[abs_idx]
        start_positions[idx] = v

    # Convertsions from unmodified mesh to the ref. frame where vertex normal 
    # is the first coordinate.
    R_to_principal = get_vertex_bases(V, F )

    # Per-coordinate importance.
    A_scale_i = np.identity( 3 )
    A_scale_j = np.identity( 3 )

    # Iteratively converge.
    for iteration in range(iterations):
        
        # Compute rotations
        R = np.zeros( (N, 3, 3) )
        inv_R = np.zeros( (N, 3, 3) )

        for abs_idx in range(N):
            # All abs vert. indices this vertex is connected to.
            vert_connections = connections[abs_idx]
            connections_qty = len(vert_connections)
            Pi = np.zeros( (connections_qty, 3) )
            Pi_new = np.zeros( (connections_qty, 3) )

            V0     = V[abs_idx]
            V0_new = V_new[abs_idx]
            
            for idx, abs_idx_other in enumerate(vert_connections):
                V1     = V[abs_idx_other]
                V1_new = V_new[abs_idx_other]
                w      = cotangent_weights[(int(abs_idx), (abs_idx_other))]
                dV     = w*(V0 - V1)
                dV_new = w*(V0_new - V1_new)

                Pi[idx] = dV
                Pi_new[idx] = dV_new

            Si = np.dot( Pi.T, Pi_new )
            # Use SVD to find the optimal rotation.
            # It transforms original points to transformed ones the best it can.
            U, _, VT = np.linalg.svd( Si )
            R_new_old = np.dot(U, VT)
            R_old_new = R_new_old.T
            R[abs_idx] = R_old_new
            inv_R[abs_idx] = R_new_old

        # Build linear system with cotangent weights
        #L = csr_matrix( (variable_verts_qty, variable_verts_qty) )
        #B = np.zeros( (variable_verts_qty, 3) )
        
        dims3 = variable_verts_qty*3
        L3 = csr_matrix( (dims3, dims3) )
        B3 = np.zeros( (dims3,) )

        for abs_idx, var_idx in variable_vertex_indices.items():
            # Apply per-vertex importance.
            A_scale_i[0, 0] = float( importances[abs_idx] )

            Pi = V[abs_idx]
            Ri = R[abs_idx]

            R_new_old_i = inv_R[abs_idx]
            R_old_to_principal_i = R_to_principal[abs_idx]
            A_i = np.dot( R_old_to_principal_i, R_new_old_i )
            A_i = np.dot( A_scale_i, A_i )

            #A_i = R_new_old_i
            #A_i = np.identity( 3 )
            #A_i = Ri.T
            AtA_i = np.dot( A_i.T, A_i )


            # current vertex cannot be fixed at its index is taken from 
            # variable vertex indices.
            # However, vertices it is connected to can be fixed.
            vert_connections = connections[abs_idx]
            for abs_idx_other in vert_connections:
                # Apply per-vertex importance.
                A_scale_j[0, 0] = float( importances[abs_idx_other] )

                Pj = V[abs_idx_other]
                Rj = R[abs_idx_other]

                R_new_old_j = inv_R[abs_idx_other]
                R_old_to_principal_j = R_to_principal[abs_idx_other]
                A_j = np.dot( R_old_to_principal_j, R_new_old_j )
                A_j = np.dot( A_scale_j, A_j )
                
                #A_j = R_new_old_j
                #A_j = np.identity( 3 )
                #A_j = Rj.T
                AtA_j = np.dot( A_j.T, A_j )

                # Get cotangent weight for this edge.
                w = cotangent_weights[(int(abs_idx), int(abs_idx_other))]

    
                A_left = w * ( AtA_i + AtA_j )
                A_right = w * ( np.dot(AtA_i, Ri) + np.dot(AtA_j, Rj) )

                # Check if this other vertex is fixed.
                is_fixed = abs_idx_other in fixed_vertices_set
                if is_fixed:
                    # This should be the fixed vertex position.
                    vert_idx = fixed_vertex_indices[abs_idx_other]
                    Pj_fixed   = fixed_positions[vert_idx]
                    #Pj_new = V_new[abs_idx_other]
                    
                    #B[var_idx] += w*Pj_fixed

                    var_idx3 = var_idx*3
                    v = w*Pj_fixed
                    v = np.dot( A_left, Pj_fixed )
                    B3[var_idx3:(var_idx3+3)] += v

                else:
                    var_idx_other = variable_vertex_indices[abs_idx_other]
                    #L[var_idx, var_idx_other] += -w

                    var_idx3 = var_idx*3
                    var_idx_other3 = var_idx_other*3
                    L3[var_idx3:(var_idx3+3), var_idx_other3:(var_idx_other3+3)] -= A_left

                #L[var_idx, var_idx] += w
                #B[var_idx]          += 0.5*w*np.dot( (Ri + Rj), (Pi - Pj) )

                var_idx3 = var_idx*3
                L3[var_idx3:(var_idx3+3), var_idx3:(var_idx3+3)] += A_left

                v = np.dot( A_right, (Pi - Pj) )
                B3[var_idx3:(var_idx3+3)] += v


       
        # Solve the linear system
        #V_some = spsolve(L, B)

        V_some3 = spsolve(L3, B3)

        #import pdb
        #pdb.set_trace()

        # Fill in V_new matrix.
        for abs_idx, var_idx in variable_vertex_indices.items():
            #v = V_some[var_idx]
            #V_new[abs_idx] = v
            var_idx3 = var_idx*3
            V_new[abs_idx][0] = V_some3[var_idx3]
            V_new[abs_idx][1] = V_some3[var_idx3+1]
            V_new[abs_idx][2] = V_some3[var_idx3+2]
        
        # Fixed positions are not touched at all.
        #for idx, abs_idx in enumerate(fixed_vertex_indices):
        #    v = fixed_positions[idx]
        #    V_new[abs_idx] = v

    return V_new








def inverse_distance_weighting_multiple( falloff_func, distances, influence_radii, power=2, epsilon=1e-3):
    num_anchors         = distances.shape[0]
    num_points          = distances.shape[1]
    values              = falloff_func( distances, influence_radii )
    interpolated_values = np.zeros_like( distances )


    below_threshold_indices = np.where(distances < epsilon)
    # Create a mask for all points
    mask = np.full(distances.shape, True)
    mask[below_threshold_indices] = False
    # Get indices of points with value 1 or above by inverting the mask
    above_or_equal_threshold_indices = np.where(mask)

    for i in range(num_points):
        # Check for exact match
        if np.all( mask[:, i] ):
            # Apply inverse distance weighting
            weights = 1.0 / (distances[:, i] + epsilon)**power
            interpolated_values[:, i] = (weights * values[:, i]) / np.sum(weights)

        else:
            exact_match_index = np.argmin(distances[:, i])
            interpolated_values[exact_match_index, i] = 1.0
            print( "wull weight for vertex #", i )
            
    return interpolated_values






def apply_proportional_displacements(V_idt, V_arap, distances, influence_radii, falloff_func ):
    """
    Applies proportional displacements to the mesh vertices based on geodesic distances and influence radii.
    
    Parameters:
    - V: np.array of shape (N, 3) containing the vertices of the mesh.
    - F: np.array of shape (M, 3) containing the faces of the mesh.
    - fixed_vertices: np.array of indices of fixed vertices.
    - fixed_positions: np.array of shape (num_fixed, 3) containing the positions of the fixed vertices.
    - influence_radii: np.array of shape (num_fixed,) containing the influence radii for each fixed vertex.
    
    Returns:
    - V_new: np.array of shape (N, 3) containing the new vertex positions after applying proportional displacements.
    """
    #import pdb
    #pdb.set_trace()
    
    falloff_weights = inverse_distance_weighting_multiple( falloff_func, distances, influence_radii )
    falloff_weights_2 = falloff_weights * falloff_weights
    combined_falloff_weights = falloff_weights.sum(axis=0)

    # Create a copy which is used for dividing the displacements combined.
    combined_falloff_weights_filtered = combined_falloff_weights.copy()
    combined_falloff_weights_filtered[combined_falloff_weights == 0] = 1  # Avoid division by zero
    
    #import pdb
    #pdb.set_trace()

    # Compute alpha for blending between proportional and arap displacements.
    alphas_prop = falloff_weights.max( axis=0 )
    alphas_arap = 1.0 - alphas_prop

    V_new = V_idt * alphas_prop[:, None] + V_arap * alphas_arap[:, None]

    return V_new

def arap_with_proportional_displacements(V, F, fixed_vertices, fixed_positions, iterations=2, influence_radii=None):
    """
    Executes the As-Rigid-As-Possible (ARAP) optimization with proportional displacements.
    
    Parameters:
    - V: np.array of shape (N, 3) containing the vertices of the mesh.
    - F: np.array of shape (M, 3) containing the faces of the mesh.
    - fixed_vertices: np.array of indices of fixed vertices.
    - fixed_positions: np.array of shape (num_fixed, 3) containing the positions of the fixed vertices.
    - iterations: int, number of iterations for the optimization process (default is 10).
    - influence_radii: np.array of shape (num_fixed,) containing the influence radii for each fixed vertex (default is None).
    
    Returns:
    - V_new: np.array of shape (N, 3) containing the new vertex positions after ARAP optimization with proportional displacements.
    """
    if influence_radii is None:
        influence_radii = 2.0 * np.ones(len(fixed_vertices))  # Default radius if none provided
    
    V_idt, distances = inverse_distance_transform( V, F, fixed_vertices, fixed_positions )
    V_arap = arap(V, F, fixed_vertices, fixed_positions, iterations, V_initial=V_idt)
    
    #V_new = V.copy()
    #V_new[fixed_vertices] = fixed_positions
    # Apply Proportional Displacements
    V_new = apply_proportional_displacements( V_idt, V_arap, distances, influence_radii )
    #V_new = V_arap
    
    return V_arap




# Example usage
# V = np.array([...]) # Nx3 array of vertices
# F = np.array([...]) # Mx3 array of faces
# fixed_vertices = np.array([...]) # Indices of fixed vertices
# fixed_positions = np.array([...]) # Corresponding positions for fixed vertices
# influence_radii = np.array([...]) # Influence radii for each fixed vertex
# V_new = arap_with_proportional_displacements(V, F, fixed_vertices, fixed_positions, influence_radii=influence_radii)



















