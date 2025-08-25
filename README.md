# OpenFAST Study of Loads from Low-Level Jets
Details in de Jong et al., 2023. "Idealized Offshore Low-Level Jets for Turbine
Structural Impact Considerations." Submitted to Wind Energy, NAWEA/WindTech
2023 Conference Special Issue. 

The OpenFAST model is based on the IEA 15-MW reference wind turbine. 

To run all cases:

1. Clone [OpenFAST](https://github.com/OpenFAST/openfast) and compile.
2. Clone the [Reference Open-Source Controller](https://github.com/nrel/rosco)
   and compile.
3. Update the `DLL_FileName` parameter in
   *template_classC/IEA-15-240-RWT-Monopile_ServoDyn.dat*.
4. Run `setup_openfast_runs_classC.py` to create the simulation directory
   structure for each case day.
5. (SERIAL) Run `run_all.sh` in each case directory -OR-
6. (PARALLEL) Use the jobscripts *1-runscript_turbsim* and
   *2-runscript_openfast* to run all TurbSim and OpenFAST simulations,
   respectively. Depending on your HPC system and build configuration, you may
   or may not run into issues with running concurrent turbsim simulations -- see
   the notes in *1-runscript_turbsim*.

