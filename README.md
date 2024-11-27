# Sunsynk LSW3 Prometheus Agent
Python script to retrieve data from a SunSynk Inverter via LSW-3 data logger and expose data for prometheus.

This script uses the uMODBUS library via pysolarmanv5 to retrieve the following inverter metrics and expose it as a guage metric for prometheus:
- LoadPower - The total power currently being used
- GridPower - The amount of power currently used from the grid 
- SolarPV1 - The amount of solar power currently being generated
- BatterySOC - Current battery state of charge
- InverterTemp - Current Inverter temperature
- InverterState - Current state of the inverter
- GridConnected - Is the power grid currently connected
- GridImport - Amount of power pulled from the grid for the day

This project uses the excellent pysolarmanv5 and modbus libraries:
- [jmccrohan/pysolarmanv5](https://github.com/jmccrohan/pysolarmanv5)
- [uModbus](https://github.com/AdvancedClimateSystems/uModbus)

## Requirements
In order to use this script the following has to be supplied:
- Inverter Port
- Inverter IP
- Inverter Serial Number

## Configuration
The following can be configured in the script:
- Prometheus port can either be set via an OS variable called EXPORTER_PORT, the default port is set as 9877
- The script is currently configured to retrieve stats every 20 seconds

## Dependencies
- Script requires Python 3.8 or greater
- Install pysolarmanv5: `pip install pysolarmanv5`
- Install prometheus client: `pip install prometheus_client`
