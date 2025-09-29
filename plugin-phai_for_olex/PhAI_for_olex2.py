import numpy as np
import os
import sys, getopt

print(os.getcwd())


# ===========================

try:
    # """
    from cctbx import maptbx
    from cctbx import miller
    from cctbx.array_family import flex
    from cctbx import sgtbx
    from cctbx_olex_adapter import OlexCctbxAdapter
    from olexFunctions import OV
    import olexex
    import olx
    from NoSpherA2 import cubes_maps

    # """
    # '''
    # check if we have torch and einops installed
    try:
        import torch
        import torch.nn as nn
        from einops.layers.torch import Rearrange
    except ImportError or ModuleNotFoundError:
        selection = olx.Alert(
            "torch not found",
            """
            Error: No working torch installation found!.
            Do you want to install this now?""",
            "YN",
            False,
        )
        if selection == "Y":
            olexex.pip("torch")
            olexex.pip("einops")
            import torch
            import torch.nn as nn
            from einops.layers.torch import Rearrange
        else:
            print(
                "Please install torch and einops inside the DataDir() manually, keeping in mind the version compatibility with installed numpy, scipy and pillow!"
            )
    DRY_RUN = False
    # '''
except:
    print(
        "No olex functionalities could be loaded, you are potentially operating outside of olex2."
    )
    print("This script will be run in form of a dry run. Setting DRY_RUN to True.")
    DRY_RUN = True

# ===========================

from ai_for_olex.PhAI import get_PhAI_phases

# ===============================================================

if DRY_RUN:

    def main(argv):
        args = "-i -n -t -p".split()
        optlist, args = getopt.getopt(argv, "i:n:tp:")
        infile = ""
        n = 1
        t = False
        p = 0
        for opt, arg in optlist:
            if opt == "-i":
                infile = arg
            elif opt == "-n":
                n = int(arg)
            elif opt == "-t":
                t = True
            elif opt == "-p":
                p = int(arg)

        return infile, n, t, p

    infile, n, t, p = main(sys.argv[1:])
    if not infile and DRY_RUN:
        import importlib.resources

        # Get a Traversable object for the 'test_files' package directory
        path_testing_dir = importlib.resources.files("ai_for_olex.PhAI.test_files")

        infile = path_testing_dir / "COD_2016452.hkl"
        infile = str(infile)

        n = 5
        p = 1
        t = True  ## this must be the saving parameter

    cycles = n

    dict_params_PhAI = {}
    dict_params_PhAI["t"] = t
    dict_params_PhAI["randomize_phases"] = p
    dict_params_PhAI["cycles"] = cycles
    dict_params_PhAI["INPUT_IS_SQUARED"] = True
    dict_params_PhAI["name_infile"] = os.path.join(
        os.getcwd(), os.path.basename(infile)
    )

    # =================================================================================

    ### I adapt how the file is read here, since an olex2 (shelx?) input file must have 5 five columns
    data = np.loadtxt(infile)  # , delimiter=" ")
    H_tmp = data[:, 0:3].astype(int)
    Fabs_tmp = data[:, 3].astype(float)
    f_sq_obs = [Fabs_tmp, H_tmp]
    # guess = get_PhAI_phases(
    #     f_sq_obs, randomize_phases=1, cycles=int(cycles), name_infile=infile
    # )
    guess = get_PhAI_phases(f_sq_obs, **dict_params_PhAI)


if not DRY_RUN:

    def millering(f_sq_obs, hkl_array, amplitudes_ord, ph):
        # try:
        # multiply Fs with the phases:
        C_Fs = flex.complex_double(
            (amplitudes_ord * np.exp(1j * np.deg2rad(ph))).tolist()
        )
        # for c_number in list(C_Fs):
        #     print(c_number)
        miller_set = miller.array(
            miller_set=miller.set(
                crystal_symmetry=f_sq_obs.crystal_symmetry(),
                indices=flex.miller_index(hkl_array.tolist()),
                anomalous_flag=False,
            ),
            data=C_Fs,
        )
        # print(miller_set)
        return miller_set

    # except Exception as e:
    #     print("something wrong with 'millering'?")
    #     print(e)
    #     pass

    def post_single_peak(xyz, height, cutoff=1.0):
        sp = height  # hp
        id = olx.xf.au.NewAtom("%.2f" % (sp), *xyz)
        if id != "-1":
            olx.xf.au.SetAtomU(id, "0.06")

    def create_solution_map(cycles=1, max_peaks="auto"):
        cctbx_adapter = OlexCctbxAdapter()
        f_sq_obs = cctbx_adapter.reflections.f_sq_obs_merged
        # print(f_sq_obs)
        hkl_array, amplitudes_ord, ph = get_PhAI_phases(
            f_sq_obs,
            randomize_phases=1,
            cycles=int(cycles),
            name_infile="",
            INPUT_IS_SQUARED=True,
        )
        guess = millering(f_sq_obs, hkl_array, amplitudes_ord, ph)
        # print(guess)
        print("test1")
        # rename it  fft_map_?
        guess = guess.expand_to_p1().set_observation_type_xray_amplitude()

        if max_peaks == "auto":
            expected_peaks = (
                guess.unit_cell().volume() / 18.6 / len(guess.space_group())
            )
            expected_peaks *= 1.3
            max_peaks = expected_peaks
        max_peaks = int(max_peaks)
        print("test2")

        obs_map = guess.fft_map(
            symmetry_flags=sgtbx.search_symmetry_flags(use_space_group_symmetry=False),
            resolution_factor=1,
            grid_step=0.2,
            f_000=1200,
        ).apply_volume_scaling()
        obs_map.apply_volume_scaling()
        # print("obs_map")
        # print(obs_map)
        # print(guess.d_min())
        # print()
        peaks = obs_map.peak_search(
            parameters=maptbx.peak_search_parameters(
                # peak_search_level=1,
                # peak_cutoff=0.05,
                # interpolate=True,
                min_distance_sym_equiv=0.2,
                general_positions_only=False,
                min_cross_distance=guess.d_min() / 2,
                max_clusters=max_peaks,
            ),
            verify_symmetry=True,
        ).all()
        print("test3")

        # print('peaks')
        # print(list(peaks))
        # for xyz, height in zip(peaks.sites(), peaks.heights()):
        #     print(xyz, height)

        olx.Kill("$Q", au=True)

        print('\n\n\n\nhallo\n\n\n\n')

        for xyz, height in zip(peaks.sites(), peaks.heights()):
            # print("xyz, height", xyz, height)
            if not xyz:
                have_solution = False
                break
            else:
                post_single_peak(xyz, height)
        if OV.HasGUI():
            try:
                olx.Freeze(True)
                olx.Compaq(q=True)
                olx.xf.EndUpdate()
                olx.Move()
            finally:
                olx.Freeze(False)

        if OV.HasGUI():
            basis = olx.gl.Basis()
            frozen = olx.Freeze(True)
        olx.xf.EndUpdate(True)  # clear LST
        olx.Compaq(q=True)
        if OV.HasGUI():
            olx.gl.Basis(basis)
            olx.Freeze(frozen)
        olx.Compaq(q=True)



    # OV.registerFunction(
    #     create_solution_map,
    #     False,
    #     "PhAI",
    # )
