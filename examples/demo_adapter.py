"""Run a WNTR model using a platform-specific EPANET-Turbo library."""

import argparse

import wntr

from turbo_adapter import TurboSimulator


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--inp", required=True, help="EPANET input file")
    parser.add_argument("--library", required=True, help="EPANET-Turbo DLL, SO, or dylib")
    parser.add_argument("--file-prefix", default="turbo_simulation")
    args = parser.parse_args()

    network = wntr.network.WaterNetworkModel(args.inp)
    results = TurboSimulator(network, args.library).run_sim(file_prefix=args.file_prefix)
    print(results.node["pressure"].head())


if __name__ == "__main__":
    main()
