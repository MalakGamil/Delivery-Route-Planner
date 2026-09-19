import argparse
from core.parser import parse
from core.validator import validate
from core.planner import plan
from core.formatter import format_output

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("filepath")
    parser.add_argument("capacity", type=float, nargs="?", default=10)
    args = parser.parse_args()

    if args.capacity <= 0:
        raise SystemExit("Error: capacity must be a positive number.")

    raw_deliveries = parse(args.filepath)
    valid_deliveries, invalid_deliveries = validate(raw_deliveries, args.capacity)
    trips = plan(valid_deliveries, args.capacity)
    format_output(trips, invalid_deliveries)


if __name__ == "__main__":
    main()