#!/usr/bin/env python3
"""
Recompute greedy and optimal_mcs for an existing run, then update summary/plots.
"""

import argparse
from pathlib import Path
import sys
import pandas as pd

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.optimization.methods import greedy_assignment
from src.optimization.optimizer import solve_optimization
from src.optimization.plotting import generate_all_plots, calculate_summary


def resolve_cb_dir(outdir: Path, cb_value: int) -> Path:
    if (outdir / "candidates.csv").exists():
        return outdir
    cb_dir = outdir / f"Cb_{cb_value}"
    if (cb_dir / "candidates.csv").exists():
        return cb_dir
    raise FileNotFoundError(f"candidates.csv not found under {outdir} or {cb_dir}")


def ensure_method_objective(df: pd.DataFrame, method: str, objective: str) -> pd.DataFrame:
    if "method" not in df.columns:
        df["method"] = method
    if "objective" not in df.columns:
        df["objective"] = objective
    return df


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Recompute greedy and optimal_mcs for an existing Cb run."
    )
    parser.add_argument(
        "--outdir",
        required=True,
        help="Base output dir or Cb_* dir (e.g., simulation/output/multibs_3_limit300)",
    )
    parser.add_argument("--cb-value", type=int, required=True, help="C_b value (e.g., 10)")
    parser.add_argument("--solver-time-limit", type=int, default=300, help="ILP time limit (sec)")
    parser.add_argument("--solver-verbose", action="store_true", help="Enable solver logs")
    parser.add_argument("--rolling-window", type=int, default=0, help="Rolling window for plots")
    args = parser.parse_args()

    cb_dir = resolve_cb_dir(Path(args.outdir), args.cb_value)
    plots_dir = cb_dir / "plots"
    plots_dir.mkdir(parents=True, exist_ok=True)

    candidates = pd.read_csv(cb_dir / "candidates.csv")

    greedy = greedy_assignment(candidates, args.cb_value)
    greedy["method"] = "greedy_mcs"
    greedy["objective"] = "throughput"
    greedy.to_csv(cb_dir / "assignment_greedy_mcs.csv", index=False)

    opt_mcs_T = solve_optimization(
        candidates,
        args.cb_value,
        rate_col="rate_mcs",
        objective="throughput",
        verbose=args.solver_verbose,
        time_limit_sec=args.solver_time_limit,
    )
    opt_mcs_T["method"] = "optimal_mcs"
    opt_mcs_T["objective"] = "throughput"
    opt_mcs_T.to_csv(cb_dir / "assignment_optimal_mcs_T.csv", index=False)

    opt_mcs_O = solve_optimization(
        candidates,
        args.cb_value,
        rate_col="rate_mcs",
        objective="outage",
        verbose=args.solver_verbose,
        time_limit_sec=args.solver_time_limit,
    )
    opt_mcs_O["method"] = "optimal_mcs"
    opt_mcs_O["objective"] = "outage"
    opt_mcs_O.to_csv(cb_dir / "assignment_optimal_mcs_O.csv", index=False)

    random = pd.read_csv(cb_dir / "assignment_random.csv")
    proposed_T = pd.read_csv(cb_dir / "assignment_proposed_optimal_dkmcs_T.csv")
    proposed_O = pd.read_csv(cb_dir / "assignment_proposed_optimal_dkmcs_O.csv")

    random = ensure_method_objective(random, "random", "throughput")
    proposed_T = ensure_method_objective(proposed_T, "proposed_optimal_dkmcs", "throughput")
    proposed_O = ensure_method_objective(proposed_O, "proposed_optimal_dkmcs", "outage")

    results_T = {
        "random": random,
        "greedy_mcs": greedy,
        "optimal_mcs_T": opt_mcs_T,
        "proposed_T": proposed_T,
    }
    results_O = {
        "random": random,
        "greedy_mcs": greedy,
        "optimal_mcs_O": opt_mcs_O,
        "proposed_O": proposed_O,
    }
    all_results = {
        "random": {"throughput": random},
        "greedy_mcs": {"throughput": greedy},
        "optimal_mcs": {"throughput": opt_mcs_T, "outage": opt_mcs_O},
        "proposed_optimal_dkmcs": {"throughput": proposed_T, "outage": proposed_O},
    }

    summaries = []
    for df in [random, greedy, opt_mcs_T, opt_mcs_O, proposed_T, proposed_O]:
        summary = calculate_summary(df)
        summary["method"] = df["method"].iloc[0]
        summary["objective"] = df["objective"].iloc[0]
        summary["cb_value"] = args.cb_value
        summaries.append(summary)
    pd.DataFrame(summaries).to_csv(cb_dir / "summary.csv", index=False)

    pd.concat(
        [random, greedy, opt_mcs_T, opt_mcs_O, proposed_T, proposed_O],
        ignore_index=True,
    ).to_csv(cb_dir / "all_assignments.csv", index=False)

    generate_all_plots(results_T, results_O, all_results, plots_dir, args.rolling_window)
    print(f"OK: updated greedy/optimal_mcs and plots under {cb_dir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
