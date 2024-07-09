# Squirrel - Carbon-aware HPC Scheduling

Squirrel is a scheduler plugin for Slurm.
The plugin is part of my Master Thesis at the Hasso-Plattner-Institut of the University of Postdam.

## Prerequisites

- Python with version 3.11 or above

## Setup

For the connection to InfluxDB, set environment variables.

- SQUIRREL_INFLUX_URL: URL to the InfluxDB host, including the port. E.g., "<host>:1234"
- SQUIRREL_INFLUX_ORG: InfluxDB organization (workspace for a group of users).
- SQUIRREL_INFLUX_TOKEN: InfluxDB API token.