from tbsoc.entrypoints.loadall import load_all_data
from tbsoc.lib.soc_mat import get_Hsoc
from tbsoc.lib.cal_tools import hr2hk
from tbsoc.entrypoints.fitsoc import build_soc_basis_matrices, find_best_alignment
from tbsoc.lib.write_hr import write_hr
import numpy as np
import jax.numpy as jnp
import os

class DataManager:
    def __init__(self):
        self.data_dict = None
        self.config_hash = None
        self.hk_tb_jax = None
        self.soc_basis_jax = None
        self.kpath_flat = None # Could be useful for plotting x-axis
        
    def load_if_needed(self, config_dict):
        # simple caching based on file paths
        # In real app, might want to check file mtimes
        current_hash = str(config_dict)
        if self.data_dict is not None and self.config_hash == current_hash:
            return

        print("DataManager: Loading data...")
        # Reset state to prevent mixing data from different folders
        self.hk_tb_jax = None
        self.soc_basis_jax = None
        self.fit_indices = None
        self.best_offset = 0 # Reset alignment too
        
        self.data_dict = load_all_data(**config_dict)
        self.config_hash = current_hash
        
        # Pre-calculate similar to fitsoc
        self._precalculate(config_dict)
        print("DataManager: Data loaded and pre-calculated.")

    def _precalculate(self, config_dict):
        # We need to be careful about matching lengths here too
        # If config_dict comes from previous session, it might have wrong lambdas
        input_lambdas = config_dict.get('lambdas', [])
        expected_len = len(self.orb_labels)
        
        if len(input_lambdas) != expected_len:
             print(f"DataManager Warning: Input lambdas length {len(input_lambdas)} != expected {expected_len}. Using zeros.")
             initial_full_lambdas = np.zeros(expected_len)
        else:
             initial_full_lambdas = np.array(input_lambdas)
        
        fit_indices = np.where(initial_full_lambdas != 0)[0]
        
        if len(fit_indices) == 0:
             # Just build TB
             self.soc_basis = np.array([])
        else:
             self.soc_basis = build_soc_basis_matrices(
                initial_full_lambdas, fit_indices, 
                self.data_dict['orbitals'], self.data_dict['orb_type'], 
                self.data_dict['orb_num'], self.data_dict['Msoc']
            )

        self.hk_tb = hr2hk(
            self.data_dict['hop_spinor'], self.data_dict['Rlatt'], 
            self.data_dict['kpath'], self.data_dict['num_wan']
        )
        
        self.hk_tb_jax = jnp.array(self.hk_tb)
        self.soc_basis_jax = jnp.array(self.soc_basis)
        self.fit_indices = fit_indices

        # --- Automatic Alignment (Same as plotsoc) ---
        # Calculate initial bands to find alignment
        if len(fit_indices) > 0:
            current_params = initial_full_lambdas[fit_indices]
            h_soc = jnp.tensordot(current_params, self.soc_basis_jax, axes=1)
            h_total = self.hk_tb_jax + h_soc
        else:
            h_total = self.hk_tb_jax
            
        eigvals = np.array(jnp.linalg.eigvalsh(h_total)) # (n_k, n_wan)
        
        vasp_bands = self.data_dict['vasp_bands']
        n_wan = eigvals.shape[1]
        n_dft = vasp_bands.shape[1]
        n_k = vasp_bands.shape[0]
        
        print("DataManager: Aligning bands...")
        best_offset, min_mse = find_best_alignment(eigvals, vasp_bands, n_wan, n_dft, n_k)
        self.best_offset = best_offset
        
        # Store alignment details for plotting
        self.n_dft = n_dft
        self.n_wan = n_wan
        self.n_compare = min(n_wan, n_dft - best_offset)
        
        dft_target_window = vasp_bands[:, best_offset : best_offset + self.n_compare]
        self.dft_window_mean = np.mean(dft_target_window)
        
        print(f"DataManager: Alignment Found. Offset: {best_offset}, Overlap: {self.n_compare}")


    @property
    def orb_labels(self):
        return self.data_dict.get('orb_labels', [])

    def get_structure(self):
        if not self.data_dict: return None

        # Read raw POSCAR file as backup, but generate XYZ for reliable 3Dmol visualization
        poscar_content = ""
        try:
             with open(self.data_dict.get('posfile', 'POSCAR'), 'r') as f:
                 poscar_content = f.read()
        except:
             pass
             
        return {
            "lattice": self.data_dict['Lattice'].tolist(),
            "atoms": self.data_dict['atoms'], 
            "coords": self.data_dict.get('coords', []).tolist(), 
            "atom_proj": self.data_dict.get('atom_proj', []),
            "poscar_content": poscar_content
        }

    def get_dft_bands(self):
        if not self.data_dict: return None
        
        # Use aligned subset of DFT bands
        vasp_bands = np.array(self.data_dict['vasp_bands']) # (nk, nbands)
        offset = getattr(self, 'best_offset', 0)
        n_compare = getattr(self, 'n_compare', self.data_dict['num_wan'])
        
        # Handle case where n_dft < offset + n_compare (shouldn't happen with correct logic)
        max_idx = min(vasp_bands.shape[1], offset + n_compare)
        dft_subset = vasp_bands[:, offset : max_idx]

        return {
            "bands": dft_subset.T.tolist(), 
            "kpath": self.data_dict['kpath'].tolist(),
            "k_distance": self.data_dict['xpath'].tolist(),
            "k_ticks": self.data_dict['xsymm'].tolist(),
            "k_labels": self.data_dict['plot_sbol'],
            "offset": offset
        }

    def calculate_tb_bands(self, lambdas_list):
        # lambdas_list is the full list of lambdas from UI
        if self.hk_tb_jax is None: return None
        
        # Robust check to prevent crashes on system switches
        if len(lambdas_list) != len(self.orb_labels):
            print(f"DataManager mismatch: received {len(lambdas_list)} lambdas, expected {len(self.orb_labels)}.")
            return None

        full_lambdas = np.array(lambdas_list)
        
        current_params = full_lambdas[self.fit_indices]
        
        if len(self.fit_indices) > 0:
            h_soc = jnp.tensordot(current_params, self.soc_basis_jax, axes=1)
            h_total = self.hk_tb_jax + h_soc
        else:
            h_total = self.hk_tb_jax
            
        eigvals = jnp.linalg.eigvalsh(h_total) # (nk, n_wan)
        
        # Create numpy copy for alignment search
        eigvals_np = np.array(eigvals)

        # --- Dynamic Re-Alignment ---
        # The user requested that we re-search the window when lambdas change.
        if self.data_dict:
            vasp_bands = self.data_dict['vasp_bands']
            n_dft = self.n_dft
            n_wan = self.n_wan
            n_k = vasp_bands.shape[0]
            
            # Re-scan for best index
            best_offset, min_mse = find_best_alignment(eigvals_np, vasp_bands, n_wan, n_dft, n_k)
            
            # Update state if changed
            if best_offset != self.best_offset:
                # print(f"DataManager: Re-alignment changed offset from {self.best_offset} to {best_offset}")
                self.best_offset = best_offset
                self.n_compare = min(n_wan, n_dft - best_offset)

        # --- Apply Alignment Shift ---
        try:
            vasp_bands = self.data_dict['vasp_bands']
            offset = getattr(self, 'best_offset', 0)
            n_compare = getattr(self, 'n_compare', 0)
            
            if n_compare > 0:
                dft_subset = vasp_bands[:, offset : offset + n_compare]
                tb_subset = eigvals[:, :n_compare]
                
                mean_diff = np.mean(tb_subset - dft_subset)
                eigvals_shifted = eigvals - mean_diff
                
                mae = float(np.mean(np.abs(eigvals_shifted[:, :n_compare] - dft_subset)))
                
                return {
                    "bands": eigvals_shifted.T.tolist(),
                    "mae": mae,
                    "offset": int(offset)
                }
        except Exception as e:
            print(f"Warning: Alignment/MAE calculation failed: {e}")
            
        return {"bands": eigvals.T.tolist(), "mae": None, "offset": getattr(self, 'best_offset', 0)}

    def save_hr_file(self, lambdas_list):
        if self.data_dict is None:
            raise ValueError("Data not loaded")
            
        full_lambdas = np.array(lambdas_list)
        
        # 1. Calculate SOC onsite matrix
        # indices are precalculated in _precalculate or we re-derive them
        fit_indices = np.where(full_lambdas != 0)[0]
        
        if len(fit_indices) == 0:
            h_soc = 0.0 # No soc
        else:
            # Re-build soc basis if needed, or assume it's same as current if fit_indices matched?
            # Safer to rebuild specific to these lambdas OR trust self.soc_basis if structure hasn't changed.
            # However, self.soc_basis depends on WHICH indices are non-zero.
            # If user manually changes a lambda from 0 to 0.1, we might need to rebuild basis.
            # BUT DataManager._precalculate does this. 
            # Ideally we reuse self.soc_basis_jax if indices match self.fit_indices.
            # FOR ROBUSTNESS: Let's just calculate the matrix directly using the same logic as fitsoc/precalculate.
            
            # Using existing self.soc_basis_jax is fast IF indices match.
            # If they don't (user unlocked a param?), we might be in trouble if we rely on cached basis.
            # BUT: In the GUI, 'lambdas_list' comes from the sliders. The indices (which are SOC vs non-SOC) are fixed by the model usually?
            # Actually, `fit_indices` are just non-zero ones.
            # Let's use the robust `get_Hsoc` directly if possible, or `build_soc_basis_matrices`.
            
            # Actually, the simplest way is to recreate the SOC matrix sum.
            # We need the basis matrices for ALL orbitals, not just non-zero ones?
            # `build_soc_basis_matrices` filters by fit_indices.
            
            # Let's do this:
            # We need the full onsite term.
            pass

        # Robust approach: Calculate full SOC matrix from scratch for given lambdas
        # This matches `tbsoc.lib.soc_mat.get_Hsoc`? No, get_Hsoc takes one orb.
        
        # Let's inspect `build_soc_basis_matrices` in `fitsoc`.
        # It returns a list of matrices corresponding to `fit_indices`.
        
        # If we just want to apply the current `lambdas_list` (which has values for ALL possible params):
        # We can iterate over non-zero lambdas and add their contribution.
        
        # Simpler:
        Msoc = self.data_dict['Msoc']
        orbitals = self.data_dict['orbitals'] 
        orb_type = self.data_dict['orb_type']
        orb_num = self.data_dict['orb_num']
        
        # Retrieve non-zero indices
        fit_indices = np.where(full_lambdas != 0)[0]
        
        if len(fit_indices) == 0:
            final_hop = self.data_dict['hop_spinor'].copy()
        else:
            # We need to construct the BASIS matrices for these fit_indices
            basis_mats = build_soc_basis_matrices(
                full_lambdas, fit_indices, 
                orbitals, orb_type, 
                orb_num, Msoc
            )
            # Then sum them up weighted by lambda
            # basis_mats is (N_active, N_wan, N_wan)
            # params is (N_active)
            active_lambdas = full_lambdas[fit_indices]
            h_soc_onsite = np.tensordot(active_lambdas, basis_mats, axes=1)
            
            # Add to original hopping (copy first)
            final_hop = self.data_dict['hop_spinor'].copy()
            
            # R=0 index
            indR0 = self.data_dict['indR0']
            
            # Add SOC to onsite term
            # Ensure complex type
            if final_hop.dtype != complex:
                final_hop = final_hop.astype(complex)
                
            final_hop[indR0] += h_soc_onsite

        # Write to file
        # We write to current directory (state.current_directory)
        # But DataManager doesn't know about `state.current_directory`.
        # We can just write to where `hrfile` was, or accept a path.
        # Let's assume we write to the same directory as the loaded HR file.
        hr_path = self.data_dict.get('hrfile', 'wannier90_hr.dat')
        out_dir = os.path.dirname(os.path.abspath(hr_path))
        
        write_hr(out_dir, final_hop, self.data_dict['Rlatt'])
        return os.path.join(out_dir, 'wannier90_hr_plus_soc.dat')
