import logging
import argparse
import os
import time
from glob import glob
from prometheus_client import start_http_server, Gauge
from pysolarmanv5 import PySolarmanV5,NoSocketAvailableError
from enum import Enum
import sys

class Registers(Enum):
    LoadPower = 178
    GridPower = 169
    SolarPV1 = 186
    BatterySOC = 184
    InverterTemp = 90
    InverterState = 59
    GridConnected = 194
    GridImport = 76

# Logging 
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Exporter for Prometheus
class CustomExporter:
    def __init__(self) -> None:
        # Values for Solarman logger
        self.inverterPort = 8899
        self.inverterIP = "<INVERTER IP>"
        self.inverterSN = <Serial Number>
        self.loadPower = -1
        self.gridPower = -1
        self.solarPower = -1
        self.batterySOC = -1
        self.inverterTemp = -1
        self.inverterState = 2 #Normal state
        self.gridConnected = 1 # Default connected state
        self.gridImport = -1
        self.metric_dict = {}
    
    # Metrics to store
    class Metrics(Enum):
        LoadPower = "SUN_5K_Load_Power"
        GridPower = "SUN_5K_Grid_Power"
        SolarPV1 = "SUN_5K_Solar_Power"
        BatterySOC = "SUN_5K_Battery_SOC"
        InverterTemp = "SUN_5K_Temperature"
        InverterState = "SUN_5K_State"
        GridConnected = "SUN_5K_Grid_Connected"
        GridImport = "SUN_5K_Grid_Import"
    
    # Retreive metrics using sync function
    def get_inverter_metrics(self, modbus):
        try:
            logging.info("Read registers")            
            # Retrieve Inverter State
            inverterState = modbus.read_holding_registers(register_addr=Registers.InverterState.value, quantity=1)
            self.inverterState = inverterState[0]
            logging.info(Registers.InverterState.name + " : " + str(inverterState[0]))

            # Retrieve Load Power
            loadPower = modbus.read_holding_registers(register_addr=Registers.LoadPower.value, quantity=1)
            self.loadPower = loadPower[0]
            logging.info(Registers.LoadPower.name + " : " + str(loadPower[0]) + " Wh")
            
            # Retrieve Grid Power
            gridPower = modbus.read_holding_registers(register_addr=Registers.GridPower.value, quantity=1)
            self.gridPower = gridPower[0]
            logging.info(Registers.GridPower.name + " : " + str(gridPower[0]) + " Wh")
            
            # Retrieve Solar PV1
            solarPower = modbus.read_holding_registers(register_addr=Registers.SolarPV1.value, quantity=1)
            self.solarPower = solarPower[0]
            logging.info(Registers.SolarPV1.name + " : " + str(solarPower[0])  + " Wh")
            
            # Retrieve Battery SOC
            batterySOC = modbus.read_holding_registers(register_addr=Registers.BatterySOC.value, quantity=1)
            self.batterySOC = batterySOC[0]
            logging.info(Registers.BatterySOC.name + " : " + str(batterySOC[0]) + " %")
            
            # Retrieve Inverter Temp
            inverterTemp = modbus.read_holding_registers(register_addr=Registers.InverterTemp.value, quantity=1)
            self.inverterTemp = inverterTemp[0]
            try:
                logging.info(Registers.InverterTemp.name + " : " + str(inverterTemp[0]/100) + " °C")
            except:
                logging.info(Registers.InverterTemp.name + " : " + str(inverterTemp[0]) + " °C")

            # Retrieve Grid State
            gridConnected = modbus.read_holding_registers(register_addr=Registers.GridConnected.value, quantity=1)
            self.gridConnected = gridConnected[0]
            logging.info(Registers.GridConnected.name + " : " + str(gridConnected[0]))

            # Retrieve Grid Imported Stats
            gridImport = modbus.read_holding_registers(register_addr=Registers.GridImport.value, quantity=1)
            self.gridImport = gridImport[0]
            logging.info(Registers.GridImport.name + " : " + str(gridImport[0])  + " Wh")

            logging.info("Registers retrieved")
        except NoSocketAvailableError as ns:
            # Occassionally there's a no socket available error when retrieving stats from 
            logging.error(f"No Socket Available Error: {ns}")
        except Exception as e:
            logging.error(f"Failed with: {e}")
            sys.exit(1)
        return

    # Convert Inverter state to text description
    def get_status(self, status):
        if status == [0]:
            stand_by = "Stand-by"
            return stand_by
        elif status == [1]:
            self_check = "Self-check"
            return self_check
        elif status == [2]:
            normal = "Normal"
            return normal
        elif status == [3]:
            warning = "Warning"
            return warning
        elif status == [4]:
            fault = "Fault"
            return fault
        else:
            error = "Error"
            return error

    # Create gauge metric for Prometheus using a dict
    def create_gauge_for_metric(self):
        for metric in self.Metrics:
            match metric:
                case self.Metrics.LoadPower:
                    self.create_or_set_gauge_for_metric(metric.value, self.loadPower)
                case self.Metrics.GridPower:
                    self.create_or_set_gauge_for_metric(metric.value, self.gridPower)
                case self.Metrics.SolarPV1:
                    self.create_or_set_gauge_for_metric(metric.value, self.solarPower)
                case self.Metrics.BatterySOC:
                    self.create_or_set_gauge_for_metric(metric.value, self.batterySOC)
                case self.Metrics.InverterTemp:
                    self.create_or_set_gauge_for_metric(metric.value, self.inverterTemp)
                case self.Metrics.InverterState:
                    self.create_or_set_gauge_for_metric(metric.value, self.inverterState)
                case self.Metrics.GridConnected:
                    self.create_or_set_gauge_for_metric(metric.value, self.gridConnected)
                case self.Metrics.GridImport:
                    self.create_or_set_gauge_for_metric(metric.value, self.gridImport)
        return
    
    # If metric does not exist, create it, if it does, update value
    def create_or_set_gauge_for_metric(self, metric_name, metric_value):
        if self.metric_dict.get(metric_name) is None:
            logging.info(f"Creating metric {metric_name} with value '{metric_value}'")
            self.metric_dict[metric_name] = Gauge(metric_name, str(metric_value))
        else:
            self.metric_dict[metric_name].set(str(metric_value))
            logging.info(f"Updating metric {metric_name} with value '{metric_value}'")
        return

    def main(self):
        # Set exporter port for Prometheus
        exporter_port = int(os.environ.get("EXPORTER_PORT", "9877"))

        modbus = PySolarmanV5(self.inverterIP, self.inverterSN, port=self.inverterPort, mb_slave_id=1, verbose=False, auto_reconnect=True)
        
        # Start exporter service
        start_http_server(exporter_port)
        while True:
            self.get_inverter_metrics(modbus)
            self.create_gauge_for_metric()
            # Timer for data retrieval
            time.sleep(20)

if __name__ == "__main__":
    c = CustomExporter()
    c.main()
