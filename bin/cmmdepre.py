#!/usr/bin/env python3
import os
import argparse
import sys
from cmmde_dftb import xyz2gen
import numpy as np
from cmmde_surface import surface
from cmmde_formats import read, write
from cmmde_dftb import xyz2gen
from cmmde_tools import sort
from cmmde_decahedron import Decahedron
from cmmde_icosahedron import Icosahedron
from cmmde_tetrahedron import Tetrahedron
from cmmde_cubic import FaceCenteredCubic, SimpleCubic, BodyCenteredCubic
import pymatgen.analysis.adsorption as pa
import pymatgen.core.structure as st
from pymatgen.core import Structure
import argparse
import sys
import warnings

warnings.filterwarnings("ignore")

parser = argparse.ArgumentParser(
    description="CMMDEPRE: Program untuk modifikasi input file"
)
parser.add_argument(
    "-i",
    "--input",
    type=str,
    default="None",
    help="Input geometri dalam berbagai format. Format yang didukung: .smi, .mol2, dan semua format yang didukung oleh openbabel.",
)
parser.add_argument(
    "-j", "--job", type=str, default="sp", help="Jenis pekerjaan yang dilakukan."
)
parser.add_argument("-s", "--size", type=str, help="Ukuran supersel yang ingin dibuat.")
parser.add_argument(
    "-hkl", "--hkl", type=str, help="Indeks Miller (hkl) permukaan yang akan dibuat."
)
parser.add_argument(
    "-v",
    "--vacuum",
    type=float,
    default=20,
    help="Tebal lapisan vakum yang dibuat (dalam angstrom). Default: 20 Angstrom.",
)
parser.add_argument(
    "-n",
    "--layer",
    type=int,
    help="Jumlah lapisan permukaan atau klaster yang akan dibuat.",
)
parser.add_argument(
    "-ads",
    "--ads",
    type=str,
    help="File koordinat Cartesian berisikan molekul adsorbat",
)
parser.add_argument(
    "-d",
    "--distance",
    type=float,
    default=1.5,
    help="Jarak adsorbat dari lapisan teratas permukaan (Angstrom). Default: 1.5 Angstrom.",
)
parser.add_argument(
    "-height",
    "--height",
    type=float,
    default=2.0,
    help="Tebal lapisan sisi aktif (Angstrom). Default: 2.0.",
)
parser.add_argument(
    "-dyn",
    "--dyn",
    type=float,
    default=3.5,
    help="Tebal lapisan bawah permukaan yang dibuat kaku (Angstrom). Default: 3.0.",
)
parser.add_argument("-e", "--element", type=str, help="Unsur yang akan dibuat klaster")
parser.add_argument(
    "-t",
    "--type",
    type=str,
    help="Tipe klaster yang akan dibuat. Pilihan: decahedron dan icosahedron",
)
parser.add_argument(
    "-lc",
    "--lc",
    type=float,
    help="Panjang sel satuan kristal ruah jika dianggap kubus.",
)
# Setup untuk klaster decahedron
parser.add_argument(
    "-npar",
    "--parallel",
    type=int,
    help="Jumlah atom pada sisi sejajar dengan ekuatorial.",
)
parser.add_argument(
    "-nper",
    "--perpendicular",
    type=int,
    help="Jumlah atom pada sisi tegak lurus dengan ekuatorial.",
)
opt = parser.parse_args(sys.argv[1:])


opt = parser.parse_args(sys.argv[1:])


if opt.job == "smi2xyz":
    os.system("echo '{}' > geom.smi".format(opt.input))
    with open("run_babel.sh", "w") as fout:
        print(
            """#!/bin/bash
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --time=168:0:0
export OMP_NUM_THREADS=1
cd $PWD
obabel geom.smi -O geom.xyz --gen3d""",
            file=fout,
        )
    os.system("sbatch run_babel.sh")
if opt.job == "mol2xyz" or opt.job == "pdb2xyz":
    with open("run_babel.sh", "w") as fout:
        print(
            """#!/bin/bash
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --time=168:0:0
export OMP_NUM_THREADS=1
cd $PWD
obabel {} -O geom.xyz""".format(
                opt.input
            ),
            file=fout,
        )
        os.system("sbatch run_babel.sh")
if opt.job == "gen2poscar":
    from cmmde_gen2poscar import gen2poscar

    gen2poscar(opt.input)

if ".mol2" in opt.input and "charge" in opt.job:
    charges = []
    with open(opt.input, "r") as f:
        lines = f.readlines()
        Natom = int(lines[2].split()[0])
        for i in range(1, Natom + 1):
            charges.append(float(lines[7 + i].split()[8]))
    charges = np.array(charges)
    print("Muatan total = {}".format(round(sum(charges))))

if opt.job == "combinexyz":
    xyz = opt.input.split(" ")
    natom = 0
    coord = []
    for i in xyz:
        with open(i, "r") as f:
            natom += int(next(f))
            next(f)
            for line in f:
                coord.append(line.strip())
    with open("geom.xyz", "w") as f:
        print(natom, file=f)
        print("Complex file generated by CMMDE", file=f)
        for i in coord:
            print(i, file=f)

if opt.job == "supercell":
    cell = opt.size.split("x")
    filename = opt.input.split(".")[0]
    os.system(
        "aflow --supercell={},{},{} < {} > {}_{}{}{}.vasp".format(
            cell[0], cell[1], cell[2], opt.input, filename, cell[0], cell[1], cell[2]
        )
    )

if opt.job == "surface":
    hkl = [int(x) for x in str(opt.hkl)]

    bulk = read(opt.input)

    slab = surface(bulk, (hkl[0], hkl[1], hkl[2]), opt.layer, vacuum=opt.vacuum)
    size = opt.size.split("x")
    superslab = slab * (int(size[0]), int(size[1]), 1)
    superslab_sorted = sort(superslab)

    write("slab_{}{}{}.xyz".format(hkl[0], hkl[1], hkl[2]), superslab_sorted)
    # write('slab.vasp', slab*(int(size[0]),int(size[1]),1))
    x = []
    y = []
    z = []
    sym = []
    a1 = 0
    b1 = 0
    c1 = 0
    a2 = 0
    b2 = 0
    c2 = 0
    a3 = 0
    b3 = 0
    c3 = 0
    with open("slab_{}{}{}.xyz".format(hkl[0], hkl[1], hkl[2]), "r") as f:
        Natoms = int(next(f))
        lat = next(f).split("Lattice=")[1].split()
        a1 += float(lat[0].strip('"'))
        a2 += float(lat[1])
        a3 += float(lat[2])
        b1 += float(lat[3])
        b2 += float(lat[4])
        b3 += float(lat[5])
        c1 += float(lat[6])
        c2 += float(lat[7])
        c3 += float(lat[8].strip('"'))
    xyz2gen(
        "slab_{}{}{}.xyz".format(hkl[0], hkl[1], hkl[2]),
        a1,
        a2,
        a3,
        b1,
        b2,
        b3,
        c1,
        c2,
        c3,
    )
    from cmmde_gen2poscar import gen2poscar

    gen2poscar("in.gen")
    os.system("mv in.vasp slab_{}{}{}.vasp".format(hkl[0], hkl[1], hkl[2]))


if opt.job == "adsorb":
    os.system(
        "cmmde_adsorbate.py -s {} -ad {} -all true -dyn {} -height {} -d {}".format(
            opt.input, opt.ads, opt.dyn, opt.height, opt.distance
        )
    )

if opt.job == "clusadsorb":
    os.system("cmmde_xyz2poscar.rb {} > POSCAR".format(opt.input))
    os.system(
        "cmmde_adsorbate.py -s POSCAR -ad {} -all true -dyn {} -height {} -d {}".format(
            opt.ads, opt.dyn, opt.height, opt.distance
        )
    )

if opt.job == "poscar2xyz":
    os.system("cmmde_poscar2gen.rb {} > in.gen".format(opt.input))
    filename = opt.input.split(".")[0]
    os.system("cmmde_gen2xyz.rb in.gen > {}.xyz".format(filename))

if opt.job == "surfinfo":
    moveatoms = []
    frozen = []
    index = 0
    with open(opt.input, "r") as f:
        next(f)
        next(f)
        next(f)
        next(f)
        next(f)
        next(f)
        next(f)
        next(f)
        next(f)
        for line in f:
            arr = line.split()
            index += 1
            if arr[3] == "T" and arr[4] == "T" and arr[5] == "T":
                moveatoms.append(index)
            else:
                frozen.append(index)
    print("Serial Atom-atom beku:")
    for i in frozen:
        print(i, end=" ")
    print("")
    print("Serial Atom-atom aktif:")
    for i in moveatoms:
        print(i, end=" ")
    print("")

if opt.job == "cluster":
    if opt.type == "icosahedron":
        struct = Icosahedron(opt.element, opt.layer, opt.lc)
        struct.write("{}_{}_{}.xyz".format(opt.element, opt.type, opt.layer))
    if opt.type == "decahedron":
        struct = Decahedron(opt.element, opt.perpendicular, opt.parallel, 0, opt.lc)
        struct.write(
            "{}_{}_{}_{}.xyz".format(
                opt.element, opt.type, opt.parallel, opt.perpendicular
            )
        )
    if opt.type == "tetrahedron":
        struct = Tetrahedron(opt.element)
