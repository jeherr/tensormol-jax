import glob
import os
from ase.data import atomic_numbers
from tensorchem.dataset.molecule import MoleculeSet, Atom

for mol in glob.glob("/home/jeherr/tensorchem/data/chemspider_data/outputs/less50_1/*.out"):
    with open(mol, "r") as f:
        lines = f.readlines()
    head, mol = os.path.split(mol)
    atoms = None

    for line in lines:
        if atoms is not None:
            if "$end" in line:
                break
            elif not line.strip():
                continue
            else:
                atoms += 1
        if "$molecule" in line:
            atoms = -1

    atomic_nums = []
    coords = []
    energies = []
    forces = []
    dipoles = []
    quadrupoles = []
    charges = []
    #converged = False

    try:
        for i, line in enumerate(lines):
            #if "**  OPTIMIZATION CONVERGED  **" in line:
            #    converged = True
            #    break
            # atomic numbers
            if "Standard Nuclear Orientation" in line:
                atom_nums = []
                for j in range(atoms):
                    atom_nums.append(atomic_numbers[lines[i + 3 + j].split()[1]])
                atomic_nums.append(atom_nums)
                if len(atom_nums) != atoms:
                    print(mol)
                    exit(0)
            # coordinates
            if "Standard Nuclear Orientation" in line:
                xyz = []
                for j in range(atoms):
                    xyz.append((float(lines[i + 3 + j].split()[2]), float(lines[i + 3 + j].split()[3]),
                                float(lines[i + 3 + j].split()[4])))
                coords.append(xyz)
            # energies
            if "Convergence criterion met" in line:
                energies.append(float(line.split()[1]))
            # forces
            if "Gradient of SCF Energy" in line:
                k = 0
                l = 0
                force = []
                for j in range(1, atoms+1):
                    force.append((float(lines[i + k + 2].split()[l + 1]) / -0.529177208590000,
                                  float(lines[i + k + 3].split()[l + 1]) / -0.529177208590000,
                                  float(lines[i + k + 4].split()[l + 1]) / -0.529177208590000))
                    l += 1
                    if (j % 6) == 0:
                        k += 4
                        l = 0
                forces.append(force)
            # dipoles
            if "Dipole Moment (Debye)" in line:
                dipole = []
                for j in range(3):
                    dipole.append(float(lines[i + 1].split()[1 + j * 2]))
                dipoles.append(dipole)
            # quadrupoles
            if "Quadrupole Moments (Debye-Ang)" in line:
                quadrupole = []
                for j in range(3):
                    quadrupole.append(
                        [float(lines[i + 1].split()[1 + j * 2]), float(lines[i + 2].split()[1 + j * 2])])
                quadrupoles.append(quadrupole)
            # charges
            if "Ground-State Mulliken Net Atomic Charges" in line:
                charge = []
                for j in range(atoms):
                    charge.append(float(lines[i + j + 4].split()[2]))
                charges.append(charge)
    except Exception as Ex:
        print(Ex, mol, i)
        continue

    #if converged:
    if len(atomic_nums) == len(coords) == len(energies) == len(dipoles) == len(quadrupoles) == len(charges) > 0:
        for i, atomic_num_1 in enumerate(atomic_nums):
            for atomic_num_2 in atomic_nums[i+1:]:
                if tuple(atomic_num_1) != tuple(atomic_num_2):
                    print("Atomic numbers are not the same between frames")
                    print(mol)
                    exit(0)
        atoms = [Atom(at_num) for at_num in atomic_nums[0]]
        mset = MoleculeSet(atoms)
        opt_geoms = []
        for i in range(len(energies)):
            coord = coords[i]
            mol_labels = {"wb97x-d.6-311gss.energy": energies[i],
                          "wb97x-d.6-311gss.dipole": dipoles[i],
                          "wb97x-d.6-311gss.quadrupole": quadrupoles[i]}
            atom_labels = {"wb97x-d.6-311gss.forces": forces[i],
                           "wb97x-d.6-311gss.mulliken_charges": charges[i]}
            opt_geoms.append(mset.build_geom(coord, mol_labels, atom_labels))
        mset.identifiers = {"possible_chemspider_id": mol[:-4]}
        mset.trajectories['wb97x-d.6-311gss.optimize.geometry'] = opt_geoms
        if not os.path.isfile(os.path.join("/mnt/sdb1/jeherr/chemspider_data/expanded_msets/meta/less50/", ".".join((mol[:-4], "mset")))):
            mset.save(filename=os.path.join("/mnt/sdb1/jeherr/chemspider_data/expanded_msets/meta/less50/", ".".join((mol[:-4], "mset"))))
        else:
            print(mol)
    else:
        print(mol)
        print(len(atomic_nums), len(energies), len(forces), len(dipoles), len(quadrupoles), len(charges))
    #else:
    #    print("Optimization did not converge for "+mol)