
import matplotlib.pyplot as plt
import pandas as pd
from oemof.solph import EnergySystem
import logging
from oemof.tools import logger
from oemof.solph import buses, views


 # initiate the logger (see the API docs for more information)
logger.define_logging(
    logfile="oemof_example.log",
    screen_level=logging.INFO,
    file_level=logging.INFO,)


def restore_results() -> None:
    restore_results = True
    if restore_results:
        logging.info("Restore the energy system and the results.")

        energysystem = EnergySystem()
        energysystem.restore(dpath=None, filename="energysystem_dump.oemof")

        results_df = energysystem.results["main"]
        return results_df

def df_results() -> None:
    Dictionary_flows_electricity = {}
    results = restore_results()
    for k, v in results.items():
        if str(k[0]) == "electricity" or str(k[1]) == "electricity":
            label = str(k[1].label)  # label sicher als String
            flow = v["sequences"]["flow"]
            Dictionary_flows_electricity[label] = flow

    Data_electricity = pd.DataFrame(Dictionary_flows_electricity)

    print(Data_electricity)

    for k, v in results:
        print(f"von {k} to {v}")


restore_results()
df_results()

