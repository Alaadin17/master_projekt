import logging
import os
from datetime import datetime

import matplotlib.pyplot as plt
import pandas as pd
from oemof.tools import logger
from oemof.solph import (
    EnergySystem, Model, buses, components as cmp, flows,
    helpers, processing, views
)

import matplotlib.pyplot as plt  # Falls oben noch nicht importiert


class EnergySystemModel:
    def __init__(self):
        # Allgemeine Initialisierungen
        self.start_date: str = "2022-01-01"
        self.periods: int = 24
        self.freq: str = "h"
        self.time_index: pd.DatetimeIndex | None = None
        self.es: EnergySystem | None = None
        self.model: Model | None = None
        self.results: dict | None = None
        self.should_dump_results: bool = True
        self.solver: str = "cbc"
        self.solver_verbose: bool = False
        self.debug: bool = False

        # Zeitreihen (Platzhalter - ersetzbar durch Dateiimport)
        self.PV_load: list[float] = []
        self.Demand: list[float] = []

        # Logging initialisieren
        logger.define_logging(
            logfile="oemof_example.log",
            screen_level=logging.INFO,
            file_level=logging.INFO
        )

        logging.info("Initialisiere das Energiesystemmodell")
        self.main()

    def main(self) -> None:
        """Startet den Modellierungsablauf."""
        logging.info("define_time_index")
        self.define_time_index()
        logging.info("define_timeseries")
        self.define_timeseries()
        logging.info("create_oemof_objects")
        self.create_oemof_objects()
        logging.info("optimise_energy_system")
        self.optimise_energy_system()
        logging.info("solve_energy_system")
        self.solve_energy_system()
        logging.info("extract_results")
        self.extract_results()
        if self.should_dump_results:
            logging.info("dump_results")
            self.dump_results()

    def define_time_index(self) -> None:
        """Definiert den Zeitindex und initialisiert das Energiesystem."""
        if self.debug:
            self.periods = 3  # Verkürzung für Debugging
        self.time_index = pd.date_range(start=self.start_date, periods=self.periods, freq=self.freq)
        self.es = EnergySystem(timeindex=self.time_index)

    def define_timeseries(self) -> None:
        """Definiert exemplarische Zeitreihen für PV-Erzeugung und Last."""
        self.PV_load = [209, 207, 200, 191, 185, 180, 172, 170, 171, 179, 189, 201,
                        208, 207, 205, 206, 217, 232, 237, 232, 224, 219, 223, 213]
        self.Demand = [0.18, 0.11, 0.05, 0.05, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
                       0.0, 0.05, 0.07, 0.11, 0.13, 0.15, 0.22, 0.28, 0.33, 0.25, 0.17, 0.09]

        if len(self.PV_load) != self.periods or len(self.Demand) != self.periods:
            raise ValueError("Zeitreihenlängen stimmen nicht mit 'periods' überein.")

    def create_oemof_objects(self) -> None:
        """Erstellt Komponenten und fügt sie dem Energiesystem hinzu."""
        assert self.es is not None, "EnergySystem wurde nicht initialisiert."

        # Bus definieren
        bus_elec = buses.Bus(label="electricity")
        self.es.add(bus_elec)

        # Überproduktion zulassen
        self.es.add(cmp.Sink(label="excess_bel", inputs={bus_elec: flows.Flow()}))

        # PV-Erzeugung
        self.es.add(cmp.Source(
            label="pv",
            outputs={bus_elec: flows.Flow(fix=self.PV_load, nominal_value=1000)}
        ))

        # Stromverbrauch
        self.es.add(cmp.Sink(
            label="demand",
            inputs={bus_elec: flows.Flow(fix=self.Demand, nominal_value=1)}
        ))

    def optimise_energy_system(self) -> None:
        """Initialisiert das Optimierungsmodell."""
        self.model = Model(self.es)

        if self.debug:
            file_path = os.path.join(helpers.extend_basic_path("lp_files"), "debug_model.lp")
            logging.info(f"LP-Datei wird gespeichert unter: {file_path}")
            self.model.write(file_path, io_options={"symbolic_solver_labels": True})

    def solve_energy_system(self) -> None:
        """Löst das Optimierungsproblem."""
        assert self.model is not None, "Optimierungsmodell wurde nicht erstellt."
        self.model.solve(solver=self.solver, solve_kwargs={"tee": self.solver_verbose})

    def extract_results(self) -> None:
        """Extrahiert Ergebnisse aus dem gelösten Modell."""
        self.results = {
            "main": processing.results(self.model),
            "meta": processing.meta_results(self.model)
        }
        self.es.results = self.results

    def dump_results(self) -> None:
        """Speichert Modell und Ergebnisse in einer Datei."""
        self.es.dump(filename="energysystem_dump.oemof")
       
if __name__ == "__main__":
    model = EnergySystemModel()
