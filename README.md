# Squirrel - Carbon-aware HPC Scheduling

Squirrel is a carbon-aware scheduler for Slurm workloads. This code is part of my Master Thesis at the Hasso-Plattner Institute (HPI) of the University of Postdam (UP).

## Prerequisites

- Python with **version 3.11** or above.
- A running **InfluxDB** instance ([self-hosted](https://github.com/influxdata/influxdb) or [cloud](https://www.influxdata.com/get-influxdb/)).
- The system has access to `sbatch` and the `sinfo` Slurm command.

## Configuration

See the [wiki page](https://github.com/Weitspringer/squirrel-hpc/wiki/Configuration) for details on configuring Squirrel.

## Usage

Navigate to the root directory of this repository.

When issuing `sbatch` commands, replace `sbatch` with `./squirrel`. Additionally, you need to provide the runtime parameter (in hours) with `--runtime` and possible node partitions with `--partitions`.

If you want to run Squirrel in simulation mode, use `./squirrel-sim`.