"""

                Bus_ele         
PV--------------|                   |
Demand----------|                   |
                |----- Conventer----|
Sink für        |                   
Überprodkution--|   

"""

###########################################################################
# imports
###########################################################################
import logging
import os
import pprint as pp
from datetime import datetime

import matplotlib.pyplot as plt
import pandas as pd
from oemof.tools import logger

from oemof.solph import EnergySystem
from oemof.solph import Model
from oemof.solph import buses
from oemof.solph import components as cmp
from oemof.solph import create_time_index
from oemof.solph import flows
from oemof.solph import helpers
from oemof.solph import processing
from oemof.solph import views


class EnergySystemModel:
    # *************************************************************************
    # ********** PART 1 - Define and optimise the energy system ***************
    # *************************************************************************
    def __init__(self):
        super().__init__()
        # ****** Defining Variables ****** 
        self.start_date = None
        self.periods = None
        self.freq = None
        self.time_index = None
        self.es = None
        self.model = None
        self.results = None
        self.data = None
        self.ev_params = None

        # initiate the logger (see the API docs for more information)
        logger.define_logging(
            logfile="oemof_example.log",
            screen_level=logging.INFO,
            file_level=logging.INFO,)

        #Output Info
        logging.info("Initialize the energy system")

        self.main()

    def main(self):
        dump_and_restore=True
        self.dump_results = dump_and_restore
        self.solver = "cbc"  # 'glpk', 'gurobi',....
        self.solver_verbose = False  # show/hide solver output
        self.debug = False  # Set number_of_timesteps to 3 to get a readable lp-file.


        logging.info("define_time_index")
        self.define_time_index()
        logging.info("define_timeseries")
        self.define_timeseries()
        logging.info("Create oemof objects")
        self.create_Oemof_Objects()
        logging.info("Optimise the energy system")
        self.optimise_Energysystem()
        # if tee_switch is true solver messages will be displayed
        logging.info("Solve the optimization problem")
        self.solve_Energysystem()
        logging.info("extract_results")
        self.extract_results()
        logging.info("Dump the energy system and the results.")
        self.dump_results()

    def define_time_index(self):
        # ****** Defining Time index ****** 
        self.start_date = "2022-01-01"
        self.periods = 24
        self.freq = 'h'
        self.time_index = pd.date_range(start=self.start_date, periods=self.periods, freq=self.freq)
        self.es = EnergySystem(timeindex=self.time_index)

    def define_timeseries(self):
         #Zeitreihen
        self.PV_load = [209,207,200,191,185,180,172,170,171,179,189,201,208,207,205,206,217,232,237,232,224,219,223,213,201,192,
              187,184,184,182,180,191,207,222,231,238,241,237,234,235,242,264,265,260,245,238,241,231,]
        self.Demand = [0.18,0.11,0.05,0.05,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.05,0.07,0.11,0.13,0.15,0.22,0.28,0.33,0.25,0.17,
          0.09,0.09,0.07,0.05,0.05,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.09,0.21,0.33,0.44,0.54,0.61,0.65,0.67,0.64,0.59,0.52,]

    def create_Oemof_Objects(self):
    ##########################################################################
    # Create oemof object
    ##########################################################################

        # create electricity bus
        bus_elec = buses.Bus(label="electricity")

        # adding the buses to the energy system
        self.es.add(bus_elec)

        # create excess component for the electricity bus to allow overproduction
        self.es.add(
            cmp.Sink(label="excess_bel", 
                    inputs={bus_elec: flows.Flow()}))


        # create fixed source object representing pv power plants
        self.es.add(
            cmp.Source(
                label="pv",
                outputs={bus_elec: flows.Flow(fix=self.PV_load, nominal_value=700)},))

        # create simple sink object representing the electrical demand
        self.es.add(
            cmp.Sink(
                label="demand",
                inputs={bus_elec: flows.Flow(fix=self.Demand, nominal_value=1)},))

    def optimise_Energysystem(self):
    ##########################################################################
    # Optimise the energy system and plot the results
    ##########################################################################

        # initialise the operational model
        self.model = Model(self.es)

        #model.receive_duals() #Schattenpreis

        if self.debug:
            file_path = os.path.join(
            helpers.extend_basic_path("lp_files"), "basic_example.lp")
            logging.info(f"Store lp-file in {file_path}.")
            io_option = {"symbolic_solver_labels": True}
            self.model.write(file_path, io_options=io_option)

    def solve_Energysystem(self):
        # if tee_switch is true solver messages will be displayed
        self.model.solve(solver=self.solver, solve_kwargs={"tee": self.solver_verbose})

    def extract_results(self):
        # add results to the energy system to make it possible to store them.
        self.es.results["main"] = processing.results(self.model)
        self.es.results["meta"] = processing.meta_results(self.model)

    def dump_results(self):
        # The default path is the '.oemof' folder in your $HOME directory.
        # The default filename is 'es_dump.oemof'.
        # You can omit the attributes (as None is the default value) for testing
        # cases. You should use unique names/folders for valuable results to avoid
        # overwriting.
        if self.dump_results:
            self.es.dump(dpath=None, filename="Test1")


if __name__ == "__main__":
    Energysystem = EnergySystemModel()