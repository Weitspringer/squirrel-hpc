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
url = <host>
org = <org>
token = <token>

[influxdb.gci.history]
bucket = squirrel
measurement = electricity_maps
field = carbonIntensity
zone = DE

[influxdb.gci.forecast]
bucket = squirrel
measurement = forecast
field = carbonIntensity
zone = DE
```
- **url**: URL to the InfluxDB host, including the port. E.g., `<host>:1234`.
- **org**: InfluxDB organization (workspace for a group of users).
- **token**: InfluxDB API token.

The subsections `influxdb.gci.history` (grid carbon intensity history) and `influxdb.gci.forecast` (grid carbon intensity forecast) allow for configuration how your data model for the respective data looks like. When you use the builtin forecasting method, you will need to configure `influx.gci.history`, otherwise you will need to configure `influx.gci.forecast`.

#### Forecasting
If you don't write forecasting data to InfluxDB, you can use the builtin forecasting based on the historical data from InfluxDB, at the cost of performance. Set `use_builtin` to `False` when you want to retrieve the forecast data from InfluxDB.
The amount of forecasted days, and therefore the scheduling scope, can also be adjusted here using `forecast_days` (should be less or equal your forecasting data when you are using forecasting data from InfluxDB).
```ini
[forecast]
use_builtin = True
forecast_days = 1
[forecast.builtin]
lookback_days = 2
```

#### Locals
Configures local paths. `viz_path` is the directory where visualizations of Squirrel will be stored, `schedule` is the path to the file where the scheduler state will be persisted. Please make sure that the parent directories exist. 

```ini
[local]
viz_path = viz
schedule = schedule.csv
```