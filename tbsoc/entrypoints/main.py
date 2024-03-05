import argparse
from tbsoc.entrypoints.addsoc import addsoc
from tbsoc.entrypoints.fitsoc import fitsoc
from tbsoc.entrypoints.precalc import precalc

def main_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="TBSOC: A computational method to estimate spin-orbital interaction strength in solid state systems",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "-v",
        "--version",
        action="version",
        version="%(prog)s (version 0.1)",
    )
    subparsers = parser.add_subparsers(title="Valid subcommands", dest="command")
    parser_precalc = subparsers.add_parser("precalc", help="precalculate the non-soc TB",
                                             formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser_precalc.add_argument("INPUT",
                                help="the input parameter file in json format", type=str, default="input.json")
    parser_soc = subparsers.add_parser("addsoc", help="add soc to non-soc TB",
                                        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser_soc.add_argument("INPUT", 
                            help="the input parameter file in json format", type=str, default="input.json")
    parser_soc.add_argument("-o","--outdir", 
                            help="the output directory", type=str, default="./")
    parser_fit = subparsers.add_parser("fit", help="fit soc to non-soc TB",
                                       formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser_fit.add_argument("INPUT", 
                            help="the input parameter file in json format", type=str, default="input.json")
    parser_fit.add_argument("-o","--outdir", 
                            help="the output directory", type=str, default="./")

    return parser

def main():
    parser = main_parser()
    args = parser.parse_args()
    # TODO: normalizaing the input data
    if args.command == "precalc":
        precalc(args.INPUT)
    elif args.command == "addsoc":
        addsoc(args.INPUT, args.outdir)
    elif args.command == "fit":
        fitsoc(args.INPUT, args.outdir)
    else:
        parser.print_help()
        exit(1)

