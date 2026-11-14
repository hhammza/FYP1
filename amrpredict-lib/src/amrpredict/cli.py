"""Command-line interface: ``amrpredict <command> [options]``."""
import argparse
import json
import sys


def _read_fasta(path):
    if path == '-':
        return sys.stdin.read()
    with open(path, 'r', encoding='utf-8', errors='replace') as fh:
        return fh.read()


def _emit(payload, pretty):
    print(json.dumps(payload, indent=2 if pretty else None, default=str))


def build_parser():
    from . import __version__

    parser = argparse.ArgumentParser(
        prog='amrpredict',
        description='Predict antimicrobial resistance from genomic data.',
    )
    parser.add_argument('--version', action='version', version=f'amrpredict {__version__}')
    parser.add_argument('--compact', action='store_true', help='emit single-line JSON')
    parser.add_argument('--model-dir', default=None, help='use artifacts from this directory')
    sub = parser.add_subparsers(dest='command', required=True)

    p = sub.add_parser('forecast', help='predict from metadata + MIC value')
    p.add_argument('antibiotic')
    p.add_argument('--taxon-id', type=int, default=None, help='NCBI taxonomy ID, e.g. 562')
    p.add_argument('--mic-value', type=float, default=None, help='MIC in mg/L')
    p.add_argument('--mic-sign', default=None, help="MIC comparator, e.g. '=' or '>'")
    p.add_argument('--genus', default='unknown')
    p.add_argument('--species', default='unknown')
    p.add_argument('--threshold', type=float, default=None,
                   help="default: the bundled model's own threshold")

    p = sub.add_parser('predict', help='predict from a complete genome FASTA')
    p.add_argument('fasta', help="path to a FASTA file, or '-' for stdin")
    p.add_argument('antibiotic')
    p.add_argument('--threshold', type=float, default=None,
                   help="default: the model's own threshold")
    p.add_argument('--genus', default=None)
    p.add_argument('--species', default=None)
    genes = p.add_mutually_exclusive_group()
    genes.add_argument('--kmers', action='store_true', help='always use the k-mer model')
    genes.add_argument('--genes', action='store_true',
                       help='require the gene model (needs AMRFinderPlus)')

    p = sub.add_parser('species', help='identify the species of a complete genome')
    p.add_argument('fasta', help="path to a FASTA file, or '-' for stdin")

    p = sub.add_parser('trend', help='yearly resistance of a genus and drug, and its forecast')
    p.add_argument('genus')
    p.add_argument('antibiotic')
    p.add_argument('--years', type=int, default=5, help='years ahead, 1 to 10')

    p = sub.add_parser('plan', help='drug per week: the RL agent against fixed schedules')
    p.add_argument('antibiotic', help='ciprofloxacin, gentamicin or imipenem')
    p.add_argument('--weeks', type=int, default=52, help='1 to 104')
    p.add_argument('--seed', type=int, default=42)

    p = sub.add_parser('timeline', help='simulate resistance evolution (not a trained model)')
    p.add_argument('fasta', help="path to a FASTA file, or '-' for stdin")
    p.add_argument('antibiotic')
    p.add_argument('--weeks', type=int, default=8)

    p = sub.add_parser('antibiotics', help='list the antibiotics a model knows')
    p.add_argument('--model', default='genome', choices=['genome', 'forecast', 'trend', 'rl'])
    sub.add_parser('status', help='report which models loaded')
    return parser


def main(argv=None):
    import amrpredict

    args = build_parser().parse_args(argv)
    pretty = not args.compact
    md = args.model_dir

    try:
        if args.command == 'forecast':
            result = amrpredict.forecast(
                args.antibiotic, taxon_id=args.taxon_id, mic_value=args.mic_value,
                mic_sign=args.mic_sign, genus=args.genus, species=args.species,
                threshold=args.threshold, model_dir=md,
            )
        elif args.command == 'predict':
            result = amrpredict.predict_fasta(
                _read_fasta(args.fasta), args.antibiotic, threshold=args.threshold,
                genus=args.genus, species=args.species,
                use_genes=False if args.kmers else (True if args.genes else None), model_dir=md,
            )
        elif args.command == 'species':
            result = amrpredict.identify_species(_read_fasta(args.fasta), model_dir=md)
        elif args.command == 'trend':
            result = amrpredict.forecast_trend(args.genus, args.antibiotic,
                                               years_ahead=args.years, model_dir=md)
        elif args.command == 'plan':
            result = amrpredict.plan_treatment(args.antibiotic, n_weeks=args.weeks,
                                               seed=args.seed, model_dir=md)
        elif args.command == 'timeline':
            result = amrpredict.simulate_timeline(
                _read_fasta(args.fasta), args.antibiotic,
                n_weeks=args.weeks, model_dir=md,
            )
        elif args.command == 'antibiotics':
            result = amrpredict.antibiotics(args.model, model_dir=md)
        else:
            result = amrpredict.status(model_dir=md)
    except FileNotFoundError as exc:
        print(f'amrpredict: {exc}', file=sys.stderr)
        return 2
    except ValueError as exc:
        print(f'amrpredict: {exc}', file=sys.stderr)
        return 1

    _emit(result, pretty)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
