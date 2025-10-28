# Running HNN on Brown's Oscar supercomputer

**Note**: these are instructions for installing the *original* version of HNN, which is **no longer actively-developed**, and only made available for scientific reproducibility. If you are reading this, you probably want to be using the actively-developed version, called *HNN-Core*, which is [available here](https://github.com/jonescompneurolab/hnn-core).

**(Brown students, staff, faculty only)**

Brown's [Oscar supercomputer](https://docs.ccv.brown.edu/oscar) operated by the Center for Computation and Visualization (CCV) group is able to run HNN as a Docker container using [Singularity](https://www.sylabs.io/guides/3.0/user-guide/). This method greatly simplifies installing HNN and its prerequisites. Instead, HNN is pre-installed in a vetted environment inside a Docker container that is pulled from Docker Hub before starting on Oscar.

## Getting an account on Oscar

To create an Oscar account, follow the instructions and click the New User Account link on [Oscar's frontpage](https://docs.ccv.brown.edu/oscar). If you are a member of a lab that has priority or Condo access on Oscar, make sure to list the PI and request those accesses. Otherwise choose an free "Exploratory" account for access to 16 cores, which is adequate for most HNN simulations.

## Running HNN

1. Go to [Oscar-on-Demand](https://ood.ccv.brown.edu/pun/sys/dashboard).
2. Choose the Desktop application and launch a new session (pick the "6 cores" option).
3. Once the Desktop is launched, open the "Terminal Emulator" program (one of the options at the bottom of the Desktop), and enter the following command. (Note that after you have installed and run HNN for the first time, you no longer need to run this line.)

```bash
singularity pull docker://jonescompneurolab/hnn
```

3. To open the HNN graphical user interface (GUI), run the following commands:

```bash
singularity shell hnn_latest.sif
source /home/hnn_user/hnn_envs
cd /home/hnn_user/hnn_source_code
python3 hnn.py
```

4. HNN should open with two windows, and you should be able to click the "Run Simulation" button and see a small dialogue box appear displaying the time steps of the simulation appear in real-time. Now it's time to simulate!

## Troubleshooting

If you have issues with the above installation method, you can view older but different install methods at [this link here](2021_instructions).
