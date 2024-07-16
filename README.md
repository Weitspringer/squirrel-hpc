# Squirrel - Carbon-aware HPC Scheduling

Squirrel is a carbon-aware scheduler for Slurm workloads. This code is part of my Master Thesis at the Hasso-Plattner Institute (HPI) of the University of Postdam (UP).

## Prerequisites

- Python with **version 3.11** or above.
- A running **InfluxDB** instance ([self-hosted](https://github.com/influxdata/influxdb) or [cloud](https://www.influxdata.com/get-influxdb/)).
- The system has access to `sbatch` and the `sinfo` Slurm command.

## Configuration

### Create Configuration
To create the configuration, copy the `squirrel_template.ini` file and paste it as `squirrel.ini` in the same directory.

### Modify Configuration
Some values are set by default, but you will need to adjust `squirrel.ini` in order to have a working configuration.

#### InfluxDB
Configures the connection to InfluxDB.
```ini
[influxdb]
url=http://172.20.18.12:8086
org=<org>
token=<token>
```
- url: URL to the InfluxDB host, including the port. E.g., "<host>:1234"
- org: InfluxDB organization (workspace for a group of users).
- roken: InfluxDB API token.

#### Builtin Forecasting

```ini
[forecast]
use_builtin = True
forecast_days = 1
[forecast.builtin]
lookback_days = 2
```

#### Misc
```ini
[local]
viz_path = viz
```