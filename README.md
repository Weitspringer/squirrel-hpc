# Squirrel - Carbon-aware HPC Scheduling
<div align="center">
<img src="assets\logo-500px.png" alt="drawing" width="150"/>
</div>
Squirrel is a carbon-aware scheduler for Slurm batch jobs. It is a bridge system between the user and Slurm.

We propose three scheduling algorithms considering the grid carbon intensity (GCI) and servers' thermal design power (TDP) values.

## Key Features
- **Temporal shifting** based on the energy zone of the data center.
- Intra-datacenter **spatial shifting** based on the nodes' TDP of CPUs and GPUs you provide.
- Built-in, configurable forecasting based on historical data.
- Integration of any forecasting data.

## Prerequisites

### Simulation
- Python with **version 3.11** or above.
- Docker Installation

### Production
- All of the above.
- You have access to `sbatch` and the `scontrol` Slurm command.

## Setup
- Setup a **InfluxDB** instance ([setup tutorial](https://github.com/Weitspringer/squirrel-hpc/wiki/InfluxDB-Setup)).
- Create a virtual environment which has the requirements from `requirements.txt` installed.
- Populate InfluxDB with data. See the [guide](https://github.com/Weitspringer/squirrel-hpc/wiki/Grid-Carbon-Intensity-(GCI)-Data) for getting started with grid carbon intensity data.

## Configuration

See the [wiki page](https://github.com/Weitspringer/squirrel-hpc/wiki/Configuration) for details on configuring Squirrel.

## Usage

To submit an sbatch job, use 
```bash
python -m cli submit "<rest-of-the-slurm-arguments>" --time=<hours> --partition=<partition_names> --gpus-per-node=[type:]<number>
```

If you want to run Squirrel in simulation mode, use `python -m cli simulate-submit`. It also has the optional parameter `--submit_date=<isoformat-datestring>`.

### Shorten Command

You can also shorten the command by setting an alias.

```bash
alias squirrel="python -m cli"

squirrel submit [...]
```

## Contribute

### Testing

```bash
python -m unittest
```

