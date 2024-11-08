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
- Setup a **InfluxDB** instance. See our [setup tutorial](https://github.com/Weitspringer/squirrel-hpc/wiki/InfluxDB-Setup).
- Create a virtual environment which has the requirements from `requirements.txt` installed.
- Make sure InfluxDB is populated with data for your intended use.

## Configuration

See the [wiki page](https://github.com/Weitspringer/squirrel-hpc/wiki/Configuration) for details on configuring Squirrel.

## Usage

Squirrel is build with [Typer](https://typer.tiangolo.com/), so you can interact with it via command line interface (CLI).
You can use Squirrel to submit batch jobs similar to Slurm's `sbatch`, manage historical/forecast GCI data, and run simulations.

### Submit a Batch Job

To submit an sbatch job, use 
```bash
python -m cli submit "<rest-of-the-slurm-arguments>" --time=<hours> --partition=<partition_names> --gpus-per-node=[type:]<number>
```

If you want to run Squirrel in simulation mode, use `python -m cli simulate-submit`. It also has the optional parameter `--submit_date=<isoformat-datestring>`.

### Import Historical GCI Data from Electricity Maps
To import historical GCI data from the [data portal](https://www.electricitymaps.com/data-portal), use:
```bash
python -m cli electricitymaps ingest-history --help
```

### Forecast GCI Data
Forecast based on current configuration and storage of results in InfluxDB:
```bash
python -m cli forecast to-influx --help
```
Configurable forecast based on range of historical data and storage of results in InfluxDB:
```bash
python -m cli forecast range-to-influx --help
```
Check out other possibilities:
```bash
python -m cli forecast --help
```

### Shorten Command

You can also shorten the command by setting an alias.

```bash
alias squirrel="python -m cli"

squirrel submit [...]
```

## Project Structure
.
├── assets                          # Assets
├── cli                             # Typer CLI
├── config                          # Configuration files
│   ├── cluster_info_template.cfg   # Template for metainformation
│   ├── cluster_info.cfg            # Your metainformation
│   ├── squirrel_template.cfg       # Template for Squirrel configuration
│   └── squirrel.cfg                # Your Squirrel configuration
├── scripts                         # Thesis remnants
├── src                             # Main logic
│   ├── cluster                     # Slurm cluster functionality
│   ├── config                      # Configuration logic
│   ├── data                        # GCI data adapters
│   ├── errors                      # Custom errors
│   ├── forecasting                 # Builtin forecasting
│   ├── sched                       # Timeslots, timetable, scheduler
│   ├── sim                         # Simulation logic, scenarios
│   └── submit                      # Adapters for job submissions
├── tests                           # Unittests
└── viz                             # Directory for simulation results etc.

## Testing

```bash
python -m unittest
```

