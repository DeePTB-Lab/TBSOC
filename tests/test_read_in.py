import numpy as np
import pytest
from pathlib import Path
from tbsoc.lib.read_in import read_poscar_wan_in, read_KPOINTS, read_EIGENVAL, read_hr

# Get the directory of the current test file
TEST_DIR = Path(__file__).parent

def test_read_poscar_wan_in():
    """
    Test the read_poscar_wan_in function.
    """
    poscar_path = TEST_DIR / "test_data" / "POSCAR"
    win_path = TEST_DIR / "test_data" / "wannier90.win"

    Lattice, atoms, coords, atom_proj, orbitals, orb_num, orb_type, orb_labels = read_poscar_wan_in(
        poscarfile=poscar_path, waninfile=win_path
    )


    # Test Lattice
    expected_lattice = np.array([
        [10.0, 0.0, 0.0],
        [0.0, 10.0, 0.0],
        [0.0, 0.0, 10.0]
    ])
    assert np.allclose(Lattice, expected_lattice)

    # Test atoms
    assert atoms == ["Si"]

    # Test atom_proj
    assert atom_proj == {"Si": ["0", "1"]}

    # Test orbitals - The current implementation does not expand 'p'
    assert orbitals == ["s", "p"]

    # Test orb_num - This is the number of actual orbitals (s=1, p=3)
    assert np.array_equal(orb_num, [1, 3])

    # Test orb_type
    assert np.array_equal(orb_type, [0, 1])


def test_read_KPOINTS():
    """
    Test the read_KPOINTS function.
    """
    kpoints_path = TEST_DIR / "test_data" / "KPOINTS"
    # read_KPOINTS requires a lattice matrix to calculate xpath
    # Use a simple cubic lattice a=10.0
    lattice = np.array([
        [10.0, 0.0, 0.0],
        [0.0, 10.0, 0.0],
        [0.0, 0.0, 10.0]
    ])

    kpath, xpath, xsymm, plot_sbol = read_KPOINTS(
        Latt=lattice, kpofile=kpoints_path
    )

    # Validate output shapes
    # KPOINTS file requests 10 points between G and X
    assert kpath.shape == (10, 3), f"Expected 10 k-points, got {kpath.shape[0]}"
    assert xpath.shape == (10,), f"Expected 10 x-values, got {xpath.shape[0]}"

    # Validate High Symmetry Points (Coordinates)
    # Start: G (0,0,0)
    assert np.allclose(kpath[0], [0.0, 0.0, 0.0]), "Start k-point should be G (0,0,0)"
    # End: X (0.5,0,0) - Note: implementation might be inclusive/exclusive? 
    # Usually interpolation includes endpoints.
    assert np.allclose(kpath[-1], [0.5, 0.0, 0.0]), "End k-point should be X (0.5,0,0)"

    # Validate X-axis distances (xpath)
    # Reciprocal lattice vector length for a=10 is b = 2*pi/10 = 0.2*pi
    # Distance G->X in reciprocal space: |(0.5,0,0)| * b = 0.5 * 0.2*pi = 0.1*pi
    total_dist = 0.1 * np.pi
    
    assert len(xsymm) == 2, "Expected 2 symmetry points (Start and End)"
    assert np.isclose(xsymm[0], 0.0), "First symmetry point should be at x=0"
    assert np.isclose(xsymm[1], total_dist), f"Last symmetry point should be at x={total_dist}"
    assert np.isclose(xpath[-1], total_dist), "Last xpath value should match total distance"

    # Validate Plot Symbols
    # Expected: ['G', 'X'] from parsing "0.0 0.0 0.0 ! G" and "0.5 0.0 0.0 ! X"
    expected_labels = ["G", "X"]
    assert plot_sbol == expected_labels, f"Expected labels {expected_labels}, got {plot_sbol}"


def test_read_EIGENVAL():
    """
    Test the read_EIGENVAL function.
    """
    eigenval_path = TEST_DIR / "test_data" / "EIGENVAL"

    k_bands, k_list2 = read_EIGENVAL(FILENAME=eigenval_path)

    # We have 2 k-points and 2 bands
    assert k_bands.shape == (2, 2)
    assert k_list2.shape == (2, 3)

    # Check the band energies
    expected_bands = np.array([
        [-5.0, 5.0],
        [-3.0, 3.0]
    ])
    assert np.allclose(k_bands, expected_bands)

    # Check the k-points
    expected_k_list = np.array([
        [0.0, 0.0, 0.0],
        [0.5, 0.0, 0.0]
    ])
    assert np.allclose(k_list2, expected_k_list)


def test_read_hr():
    """
    Test the read_hr function.
    """
    hr_path = TEST_DIR / "test_data" / "wannier90_hr.dat"

    hop_spinor, Rlatt, indR0 = read_hr(Filename=hr_path)

    # num_wann = 2, nrpts = 3
    # hop_spinor shape should be (nrpts, 2*num_wann, 2*num_wann)
    assert hop_spinor.shape == (3, 4, 4)
    assert Rlatt.shape == (3, 3)

    # indR0 should be the index where Rlatt is [0, 0, 0]
    assert indR0 == 0

    # Check the R=0 hopping matrix (spinor)
    # H_R0 = [[1.0, 0.0], [0.0, 1.0]]
    # hop_spinor[0] should be kron(eye(2), H_R0)
    expected_H0_spinor = np.array([
        [1.0, 0.0, 0.0, 0.0],
        [0.0, 1.0, 0.0, 0.0],
        [0.0, 0.0, 1.0, 0.0],
        [0.0, 0.0, 0.0, 1.0]
    ])
    assert np.allclose(hop_spinor[0], expected_H0_spinor)

    # Check the R=(1,0,0) hopping matrix
    # H_R1 = [[0.5, 0.0], [0.0, 0.5]]
    expected_H1_spinor = np.kron(np.eye(2), [[0.5, 0.0], [0.0, 0.5]])
    assert np.allclose(hop_spinor[1], expected_H1_spinor)
