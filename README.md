# Squirrel - Carbon-aware HPC Scheduling
<div align="center">
<img src="assets\logo-500px.png" alt="drawing" width="150"/>
</div>
Squirrel is a carbon-aware scheduler for Slurm batch jobs.

It is a bridge system between the user and Slurm.

## Key Features
- **Temporal shifting** based on the energy zone of the data center.
- Intra-datacenter **spatial shifting** based on the nodes' TDP of CPUs and GPUs you provide.
- Change scheduling strategies at runtime.
- Built-in, configurable forecasting based on historical data.

## Prerequisites

- Python with **version 3.11** or above.
- A running **InfluxDB** instance ([self-hosted](https://github.com/influxdata/influxdb) or [cloud](https://www.influxdata.com/get-influxdb/)).
- You have access to `sbatch` and the `sinfo` Slurm command.

## Configuration

See the [wiki page](https://github.com/Weitspringer/squirrel-hpc/wiki/Configuration) for details on configuring Squirrel.

## Usage

Navigate to the root directory of this repository.

When issuing `sbatch` commands, replace `sbatch` with `./squirrel`. Additionally, you need to provide the runtime parameter (in hours) with `--runtime` and possible node partitions with `--partitions`.

If you want to run Squirrel in simulation mode, use `./squirrel-sim`.
