import argparse
import json
import logging
from datetime import date
from pathlib import Path

from medallion.config import PipelineConfig, money_threshold
from medallion.contracts import AS_OF_DATE, SEED


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description="Synthetic e-commerce medallion pipeline")
    commands = result.add_subparsers(dest="command", required=True)
    commands.add_parser("setup-java", help="Download a full JDK 21 into this virtualenv")
    generate = commands.add_parser("generate", help="Generate deterministic synthetic CSVs")
    generate.add_argument("--output", type=Path, default=Path("data"))
    generate.add_argument("--customers", type=int, default=10000)
    generate.add_argument("--orders", type=int, default=100000)
    generate.add_argument("--products", type=int, default=500)
    generate.add_argument("--seed", type=int, default=SEED)
    generate.add_argument("--as-of-date", type=date.fromisoformat, default=AS_OF_DATE)
    generate.add_argument("--clean", action="store_true", help="Do not inject quality issues")
    run = commands.add_parser("run", help="Run the local Parquet pipeline and HTML dashboard")
    run.add_argument("--source", type=Path, default=Path("data"))
    run.add_argument("--output", type=Path, default=Path("artifacts/local"))
    run.add_argument("--as-of-date", type=date.fromisoformat, default=AS_OF_DATE)
    run.add_argument("--high-value-threshold", type=money_threshold, default=money_threshold("1000"))
    return result


def _run_local(args: argparse.Namespace) -> None:
    from medallion.dashboard.render import render_dashboard
    from medallion.pipeline import run_pipeline
    from medallion.runtime import local_spark
    from medallion.storage import LocalStore

    config = PipelineConfig(
        str(args.source.resolve()), args.as_of_date, args.high_value_threshold
    )
    spark = local_spark()
    try:
        store = LocalStore(spark, args.output)
        manifest = run_pipeline(spark, config, store)
        gold = {name: store.read("gold", name) for name in manifest["rows"]["gold"]}
        dashboard_path = store.root / "dashboard.html"
        manifest["dashboard_status"] = "RUNNING"
        store.manifest(manifest)
        render_dashboard(gold, dashboard_path, run_id=manifest["run_id"])
        manifest["dashboard"] = str(dashboard_path)
        manifest["dashboard_status"] = "SUCCESS"
        store.manifest(manifest)
        (store.root / "quality_report.json").write_text(
            json.dumps(manifest["quality_metrics"], indent=2) + "\n"
        )
        print(json.dumps({
            "run_id": manifest["run_id"],
            "status": manifest["status"],
            "rows": manifest["rows"],
            "reconciliation": manifest["reconciliation"],
            "dashboard": manifest["dashboard"],
        }, indent=2))
    finally:
        spark.stop()


def main() -> int:
    args = parser().parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    try:
        if args.command == "setup-java":
            from medallion.runtime import install_local_java

            print(install_local_java())
        elif args.command == "generate":
            from medallion.data_generation.generate_sample_data import generate_sample_data

            manifest = generate_sample_data(
                args.output,
                customers=args.customers,
                orders=args.orders,
                products=args.products,
                seed=args.seed,
                as_of_date=args.as_of_date,
                inject_issues=not args.clean,
            )
            print(json.dumps(manifest, indent=2))
        else:
            _run_local(args)
    except (OSError, ValueError) as exc:
        logging.error("%s", exc)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
