from __future__ import annotations

import json
import subprocess
import time
from pathlib import Path

import duckdb


ROOT = Path(__file__).resolve().parents[3]
ANALYSIS_DIR = ROOT / "analysis" / "problem3_informativeness_20260917"
OUT = ANALYSIS_DIR / "outputs"

SOURCE_REPO = Path("/home/soroush/projects/lafc-evict-dataset/repo")
CANDIDATE_SOURCE = (
    SOURCE_REPO
    / "release/lafc-evict-v0.1-open-current-contract-preserved/data/candidate_rows/**/*.parquet"
)
DECISION_VIEW = (
    SOURCE_REPO
    / "release/lafc-evict-v0.1-open-current-contract-preserved/data/decision_view/decision_view.parquet"
)

LINEAR_FIT = (
    ROOT
    / "analysis/feature_provenance_repair_20260917/artifacts/clean_linear_regression_fit.json"
)
PAIRWISE_FIT = (
    ROOT
    / "analysis/feature_provenance_repair_20260917/artifacts/clean_pairwise_logistic_eval.json"
)

KEY = [
    "trace_name",
    "trace_family",
    "dataset_source",
    "capacity",
    "horizon",
    "decision_id",
    "decision_t",
    "decision_chunk_id",
    "split",
]

CLEAN_FEATURES = [
    "candidate_recency_rank",
    "candidate_age_norm",
    "candidate_lru_score",
    "candidate_is_lru_victim",
    "score_gap_to_lru_victim",
    "recent_candidate_request_rate",
    "recent_candidate_hit_rate",
]

METHOD_ORDER = [
    "uniform_random",
    "lru",
    "clean_linear",
    "clean_pairwise_logistic",
    "frozen_hgb",
]

STRATUM_ORDER = {"Z": 0, "Q1": 1, "Q2": 2, "Q3": 3, "Q4": 4, "Q4_sparse": 5}


def _git(args: list[str]) -> str:
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()


def _load_linear_expression() -> str:
    fit = json.loads(LINEAR_FIT.read_text())
    features = fit["features"]
    coefs = fit["coefficients"]
    terms = []
    for feature, coef in zip(features, coefs):
        if feature == "intercept":
            terms.append(f"({coef:.17g})")
        else:
            terms.append(f"({coef:.17g}) * {feature}")
    return " + ".join(terms)


def _load_pairwise_expression() -> str:
    fit = json.loads(PAIRWISE_FIT.read_text())
    terms = [
        f"({coef:.17g}) * {feature}"
        for feature, coef in zip(fit["features"], fit["coefficients"])
    ]
    return " + ".join(terms)


def _copy(con: duckdb.DuckDBPyConnection, query: str, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    con.execute(f"COPY ({query}) TO '{path}' (HEADER, DELIMITER ',')")


def _key_join(left: str, right: str) -> str:
    return " AND ".join(f"{left}.{col} = {right}.{col}" for col in KEY)


def _select_key(prefix: str = "") -> str:
    p = f"{prefix}." if prefix else ""
    return ", ".join(f"{p}{col}" for col in KEY)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    con = duckdb.connect()
    con.execute("SET threads TO 16")
    con.execute("SET memory_limit='48GB'")

    linear_expr = _load_linear_expression()
    pairwise_expr = _load_pairwise_expression()

    source_state = {
        "source_repo": str(SOURCE_REPO),
        "source_branch": "repair/feature-provenance-and-modeling-20260917",
        "source_sha": "a79da7235297eb2be3436a884195025f24df3c68",
        "problem3_branch": _git(["rev-parse", "--abbrev-ref", "HEAD"]),
        "problem3_head_at_run_start": _git(["rev-parse", "HEAD"]),
        "problem3_worktree": str(ROOT),
        "candidate_source": str(CANDIDATE_SOURCE),
        "decision_view": str(DECISION_VIEW),
        "protocol_commit": "076e1cf7ea5e1d3d5058b8b1f3004328687e1aa5",
        "started_unix_time": t0,
    }
    (OUT / "source_state.json").write_text(json.dumps(source_state, indent=2) + "\n")

    print("building decision metrics")
    con.execute(
        f"""
        CREATE OR REPLACE TEMP TABLE loss_hist AS
        SELECT {_select_key()}, y_loss, COUNT(*) AS loss_count
        FROM read_parquet('{CANDIDATE_SOURCE}', hive_partitioning=1)
        GROUP BY ALL
        """
    )
    con.execute(
        """
        CREATE OR REPLACE TEMP TABLE strict_density AS
        SELECT
          trace_name, trace_family, dataset_source, capacity, horizon,
          decision_id, decision_t, decision_chunk_id, split,
          SUM(loss_count) AS candidate_count_from_hist,
          SUM(loss_count * (loss_count - 1) / 2.0) AS equal_loss_pairs,
          SUM(loss_count) * (SUM(loss_count) - 1) / 2.0 AS all_pairs,
          CASE
            WHEN SUM(loss_count) <= 1 THEN 0.0
            ELSE 1.0 - (
              SUM(loss_count * (loss_count - 1) / 2.0)
              / (SUM(loss_count) * (SUM(loss_count) - 1) / 2.0)
            )
          END AS strict_preference_density
        FROM loss_hist
        GROUP BY trace_name, trace_family, dataset_source, capacity, horizon,
          decision_id, decision_t, decision_chunk_id, split
        """
    )
    con.execute(
        f"""
        CREATE OR REPLACE TEMP TABLE decision_metrics AS
        SELECT
          d.*,
          d.regret_mean AS expected_random_regret,
          d.optimal_candidate_count::DOUBLE / d.candidate_count AS optimal_set_fraction,
          d.optimal_candidate_count::DOUBLE / d.candidate_count AS random_optimal_probability,
          d.regret_max AS loss_range,
          s.strict_preference_density,
          CASE
            WHEN d.regret_mean = 0 THEN 'zero'
            WHEN d.regret_mean <= 1.0/256.0 THEN 'tiny'
            WHEN d.regret_mean <= 1.0/64.0 THEN 'small'
            WHEN d.regret_mean <= 1.0/16.0 THEN 'moderate'
            ELSE 'large'
          END AS absolute_info_bin
        FROM read_parquet('{DECISION_VIEW}') d
        JOIN strict_density s ON {_key_join('d', 's')}
        """
    )
    con.execute(
        """
        CREATE OR REPLACE TEMP TABLE positive_strata AS
        SELECT
          trace_name, trace_family, dataset_source, capacity, horizon,
          decision_id, decision_t, decision_chunk_id, split,
          CASE WHEN positive_cell_count < 4 THEN 'Q4_sparse' ELSE 'Q' || q::VARCHAR END AS informativeness_stratum,
          positive_cell_count
        FROM (
          SELECT
            *,
            COUNT(*) OVER (PARTITION BY trace_family, capacity, horizon) AS positive_cell_count,
            NTILE(4) OVER (
              PARTITION BY trace_family, capacity, horizon
              ORDER BY expected_random_regret, trace_name, split, decision_t,
                decision_chunk_id, decision_id
            ) AS q
          FROM decision_metrics
          WHERE expected_random_regret > 0
        )
        """
    )
    con.execute(
        f"""
        CREATE OR REPLACE TEMP TABLE decision_strata AS
        SELECT
          d.*,
          COALESCE(p.informativeness_stratum, 'Z') AS informativeness_stratum,
          CASE COALESCE(p.informativeness_stratum, 'Z')
            WHEN 'Z' THEN 0 WHEN 'Q1' THEN 1 WHEN 'Q2' THEN 2
            WHEN 'Q3' THEN 3 WHEN 'Q4' THEN 4 ELSE 5
          END AS stratum_order,
          COALESCE(p.positive_cell_count, 0) AS positive_cell_count
        FROM decision_metrics d
        LEFT JOIN positive_strata p ON {_key_join('d', 'p')}
        """
    )
    con.execute(
        """
        CREATE OR REPLACE TEMP TABLE alt_metric_long AS
        SELECT *, 'one_minus_optimal_set_fraction' AS alt_metric,
          1.0 - optimal_set_fraction AS alt_value
        FROM decision_strata
        UNION ALL
        SELECT *, 'loss_range' AS alt_metric, loss_range AS alt_value
        FROM decision_strata
        UNION ALL
        SELECT *, 'strict_preference_density' AS alt_metric,
          strict_preference_density AS alt_value
        FROM decision_strata
        """
    )
    con.execute(
        """
        CREATE OR REPLACE TEMP TABLE alt_metric_positive AS
        SELECT
          trace_name, trace_family, dataset_source, capacity, horizon,
          decision_id, decision_t, decision_chunk_id, split, alt_metric,
          CASE WHEN positive_cell_count < 4 THEN 'Q4_sparse' ELSE 'Q' || q::VARCHAR END AS alt_stratum
        FROM (
          SELECT
            *,
            COUNT(*) OVER (PARTITION BY alt_metric, trace_family, capacity, horizon) AS positive_cell_count,
            NTILE(4) OVER (
              PARTITION BY alt_metric, trace_family, capacity, horizon
              ORDER BY alt_value, trace_name, split, decision_t,
                decision_chunk_id, decision_id
            ) AS q
          FROM alt_metric_long
          WHERE alt_value > 0
        )
        """
    )
    con.execute(
        f"""
        CREATE OR REPLACE TEMP TABLE alt_metric_strata AS
        SELECT
          a.trace_name, a.trace_family, a.dataset_source, a.capacity, a.horizon,
          a.decision_id, a.decision_t, a.decision_chunk_id, a.split,
          a.alt_metric, a.alt_value,
          COALESCE(p.alt_stratum, 'Z') AS alt_stratum
        FROM alt_metric_long a
        LEFT JOIN alt_metric_positive p
          ON {_key_join('a', 'p')} AND a.alt_metric = p.alt_metric
        """
    )

    print("scoring selectors")
    key_cols = _select_key("c")
    partition_cols = ", ".join(f"c.{col}" for col in KEY)
    con.execute(
        f"""
        CREATE OR REPLACE TEMP TABLE selector_outcomes AS
        SELECT
          'uniform_random' AS method,
          {_select_key()},
          NULL::VARCHAR AS selected_candidate_page_id,
          NULL::DOUBLE AS selected_y_loss,
          min_y_loss,
          expected_random_regret AS realized_regret,
          random_optimal_probability AS optimal_selection_rate
        FROM decision_strata
        UNION ALL
        SELECT
          method,
          trace_name, trace_family, dataset_source, capacity, horizon,
          decision_id, decision_t, decision_chunk_id, split,
          candidate_page_id AS selected_candidate_page_id,
          y_loss AS selected_y_loss,
          min_y_loss,
          y_loss - min_y_loss AS realized_regret,
          CASE WHEN y_loss = min_y_loss THEN 1.0 ELSE 0.0 END AS optimal_selection_rate
        FROM (
          SELECT
            'lru' AS method,
            {key_cols},
            c.candidate_page_id,
            c.y_loss,
            d.min_y_loss,
            ROW_NUMBER() OVER (
              PARTITION BY {partition_cols}
              ORDER BY c.candidate_is_lru_victim DESC, c.candidate_page_id
            ) AS rn
          FROM read_parquet('{CANDIDATE_SOURCE}', hive_partitioning=1) c
          JOIN decision_strata d ON {_key_join('c', 'd')}
          QUALIFY rn = 1
        )
        UNION ALL
        SELECT
          method,
          trace_name, trace_family, dataset_source, capacity, horizon,
          decision_id, decision_t, decision_chunk_id, split,
          candidate_page_id AS selected_candidate_page_id,
          y_loss AS selected_y_loss,
          min_y_loss,
          y_loss - min_y_loss AS realized_regret,
          CASE WHEN y_loss = min_y_loss THEN 1.0 ELSE 0.0 END AS optimal_selection_rate
        FROM (
          SELECT
            'clean_linear' AS method,
            {key_cols},
            c.candidate_page_id,
            c.y_loss,
            d.min_y_loss,
            ({linear_expr}) AS selector_score,
            ROW_NUMBER() OVER (
              PARTITION BY {partition_cols}
              ORDER BY ({linear_expr}) ASC, c.candidate_page_id
            ) AS rn
          FROM read_parquet('{CANDIDATE_SOURCE}', hive_partitioning=1) c
          JOIN decision_strata d ON {_key_join('c', 'd')}
          QUALIFY rn = 1
        )
        UNION ALL
        SELECT
          method,
          trace_name, trace_family, dataset_source, capacity, horizon,
          decision_id, decision_t, decision_chunk_id, split,
          candidate_page_id AS selected_candidate_page_id,
          y_loss AS selected_y_loss,
          min_y_loss,
          y_loss - min_y_loss AS realized_regret,
          CASE WHEN y_loss = min_y_loss THEN 1.0 ELSE 0.0 END AS optimal_selection_rate
        FROM (
          SELECT
            'clean_pairwise_logistic' AS method,
            {key_cols},
            c.candidate_page_id,
            c.y_loss,
            d.min_y_loss,
            ({pairwise_expr}) AS selector_score,
            ROW_NUMBER() OVER (
              PARTITION BY {partition_cols}
              ORDER BY ({pairwise_expr}) DESC, c.candidate_page_id
            ) AS rn
          FROM read_parquet('{CANDIDATE_SOURCE}', hive_partitioning=1) c
          JOIN decision_strata d ON {_key_join('c', 'd')}
          QUALIFY rn = 1
        )
        """
    )

    hgb_parquet = OUT / "frozen_hgb_outcomes.parquet"
    if hgb_parquet.exists():
        print("including frozen HGB outcomes")
        con.execute(
            f"""
            INSERT INTO selector_outcomes
            SELECT
              'frozen_hgb' AS method,
              trace_name, trace_family, dataset_source, capacity, horizon,
              decision_id, decision_t, decision_chunk_id, split,
              selected_candidate_page_id,
              selected_y_loss,
              min_y_loss,
              realized_regret,
              optimal_selection_rate
            FROM read_parquet('{hgb_parquet}')
            """
        )

    print("writing summaries")
    con.execute(
        """
        CREATE OR REPLACE TEMP TABLE selector_joined AS
        SELECT
          o.*,
          d.expected_random_regret,
          d.optimal_set_fraction,
          d.random_optimal_probability,
          d.loss_range,
          d.strict_preference_density,
          d.absolute_info_bin,
          d.informativeness_stratum,
          d.candidate_count,
          d.stratum_order
        FROM selector_outcomes o
        JOIN decision_strata d
          ON o.trace_name = d.trace_name
         AND o.trace_family = d.trace_family
         AND o.dataset_source = d.dataset_source
         AND o.capacity = d.capacity
         AND o.horizon = d.horizon
         AND o.decision_id = d.decision_id
         AND o.decision_t = d.decision_t
         AND o.decision_chunk_id = d.decision_chunk_id
         AND o.split = d.split
        """
    )
    con.execute(
        """
        CREATE OR REPLACE TEMP TABLE primary_summary AS
        SELECT
          informativeness_stratum,
          stratum_order,
          method,
          COUNT(*) AS n_decisions,
          MIN(expected_random_regret) AS info_min,
          quantile_cont(expected_random_regret, 0.5) AS info_median,
          AVG(expected_random_regret) AS info_mean,
          MAX(expected_random_regret) AS info_max,
          AVG(realized_regret) AS mean_regret,
          quantile_cont(realized_regret, 0.5) AS median_regret,
          quantile_cont(realized_regret, 0.9) AS p90_regret,
          quantile_cont(realized_regret, 0.95) AS p95_regret,
          AVG(optimal_selection_rate) AS optimal_selection_rate
        FROM selector_joined
        GROUP BY informativeness_stratum, stratum_order, method
        """
    )
    con.execute(
        """
        CREATE OR REPLACE TEMP TABLE best_non_oracle AS
        SELECT informativeness_stratum, MIN(mean_regret) AS best_non_oracle_mean_regret
        FROM primary_summary
        WHERE method <> 'uniform_random'
        GROUP BY informativeness_stratum
        """
    )
    con.execute(
        """
        CREATE OR REPLACE TEMP TABLE random_by_stratum AS
        SELECT informativeness_stratum, mean_regret AS random_mean_regret
        FROM primary_summary
        WHERE method = 'uniform_random'
        """
    )
    _copy(
        con,
        """
        SELECT
          p.*,
          CASE p.method
            WHEN 'uniform_random' THEN 0
            WHEN 'lru' THEN 1
            WHEN 'clean_linear' THEN 2
            WHEN 'clean_pairwise_logistic' THEN 3
            WHEN 'frozen_hgb' THEN 4
            ELSE 99
          END AS method_order,
          r.random_mean_regret,
          r.random_mean_regret - p.mean_regret AS regret_improvement_vs_random,
          p.mean_regret - b.best_non_oracle_mean_regret AS excess_regret_vs_best_non_oracle
        FROM primary_summary p
        JOIN random_by_stratum r USING (informativeness_stratum)
        JOIN best_non_oracle b USING (informativeness_stratum)
        ORDER BY stratum_order, method_order
        """,
        OUT / "primary_method_by_informativeness.csv",
    )
    _copy(
        con,
        """
        SELECT
          informativeness_stratum, stratum_order, trace_family, capacity, horizon,
          COUNT(*) AS n_decisions,
          AVG(expected_random_regret) AS mean_expected_random_regret
        FROM decision_strata
        GROUP BY ALL
        ORDER BY stratum_order, trace_family, capacity, horizon
        """,
        OUT / "primary_stratum_composition.csv",
    )
    _copy(
        con,
        """
        SELECT
          absolute_info_bin,
          CASE absolute_info_bin
            WHEN 'zero' THEN 0 WHEN 'tiny' THEN 1 WHEN 'small' THEN 2
            WHEN 'moderate' THEN 3 ELSE 4
          END AS bin_order,
          method,
          CASE method
            WHEN 'uniform_random' THEN 0
            WHEN 'lru' THEN 1
            WHEN 'clean_linear' THEN 2
            WHEN 'clean_pairwise_logistic' THEN 3
            WHEN 'frozen_hgb' THEN 4
            ELSE 99
          END AS method_order,
          COUNT(*) AS n_decisions,
          AVG(expected_random_regret) AS mean_expected_random_regret,
          AVG(realized_regret) AS mean_regret,
          quantile_cont(realized_regret, 0.5) AS median_regret,
          AVG(optimal_selection_rate) AS optimal_selection_rate
        FROM selector_joined
        GROUP BY ALL
        ORDER BY bin_order, method_order
        """,
        OUT / "absolute_bin_method_summary.csv",
    )
    _copy(
        con,
        """
        SELECT
          d.absolute_info_bin,
          CASE d.absolute_info_bin
            WHEN 'zero' THEN 0 WHEN 'tiny' THEN 1 WHEN 'small' THEN 2
            WHEN 'moderate' THEN 3 ELSE 4
          END AS bin_order,
          COUNT(*) AS n_decisions,
          COUNT(*)::DOUBLE / SUM(COUNT(*)) OVER () AS decision_fraction,
          AVG(expected_random_regret) AS mean_expected_random_regret,
          SUM(expected_random_regret) AS total_expected_random_regret,
          SUM(expected_random_regret) / SUM(SUM(expected_random_regret)) OVER () AS share_of_total_random_regret,
          AVG(random_optimal_probability) AS random_optimal_probability
        FROM decision_strata d
        GROUP BY d.absolute_info_bin
        ORDER BY bin_order
        """,
        OUT / "absolute_informativeness_decomposition.csv",
    )
    _copy(
        con,
        """
        SELECT
          CASE
            WHEN expected_random_regret = 0 THEN 'A_all_tied'
            WHEN expected_random_regret > 0 AND optimal_set_fraction >= 0.90 THEN 'B_large_optimal_set_some_worse'
            WHEN expected_random_regret <= 1.0/64.0 THEN 'C_nonlarge_optimal_set_tiny_regret'
            ELSE 'D_material_regret_separation'
          END AS mechanism_group,
          COUNT(*) AS n_decisions,
          COUNT(*)::DOUBLE / SUM(COUNT(*)) OVER () AS decision_fraction,
          AVG(expected_random_regret) AS mean_expected_random_regret,
          SUM(expected_random_regret) AS total_expected_random_regret,
          SUM(expected_random_regret) / SUM(SUM(expected_random_regret)) OVER () AS share_of_total_random_regret,
          AVG(random_optimal_probability) AS random_optimal_probability,
          AVG(optimal_set_fraction) AS mean_optimal_set_fraction,
          AVG(loss_range) AS mean_loss_range
        FROM decision_strata
        GROUP BY mechanism_group
        ORDER BY mechanism_group
        """,
        OUT / "headline_random_optimal_decomposition.csv",
    )
    _copy(
        con,
        """
        SELECT
          trace_family, capacity, horizon,
          COUNT(*) AS n_decisions,
          AVG(CASE WHEN expected_random_regret = 0 THEN 1.0 ELSE 0.0 END) AS all_tied_fraction,
          1.0 - AVG(CASE WHEN expected_random_regret = 0 THEN 1.0 ELSE 0.0 END) AS discriminative_fraction,
          AVG(random_optimal_probability) AS random_optimal_probability,
          AVG(expected_random_regret) AS mean_expected_random_regret,
          AVG(CASE WHEN optimal_candidate_count = 1 THEN 1.0 ELSE 0.0 END) AS unique_winner_fraction,
          AVG(loss_range) AS mean_loss_range,
          MAX(loss_range) AS max_loss_range
        FROM decision_strata
        GROUP BY ALL
        ORDER BY trace_family, capacity, horizon
        """,
        OUT / "per_family_capacity_horizon_baseline_facts.csv",
    )
    _copy(
        con,
        """
        SELECT optimal_candidate_count, COUNT(*) AS n_decisions
        FROM decision_strata
        GROUP BY optimal_candidate_count
        ORDER BY optimal_candidate_count
        """,
        OUT / "optimal_set_size_distribution.csv",
    )
    _copy(
        con,
        """
        SELECT
          horizon,
          COUNT(*) AS n_decisions,
          AVG(CASE WHEN expected_random_regret = 0 THEN 1.0 ELSE 0.0 END) AS all_tied_fraction,
          AVG(random_optimal_probability) AS random_optimal_probability,
          AVG(expected_random_regret) AS mean_expected_random_regret,
          AVG(loss_range) AS mean_loss_range,
          MAX(loss_range) AS max_loss_range
        FROM decision_strata
        GROUP BY horizon
        ORDER BY horizon
        """,
        OUT / "horizon_summary_h4_h16.csv",
    )
    _copy(
        con,
        """
        SELECT
          a.alt_metric,
          a.alt_stratum,
          CASE a.alt_stratum
            WHEN 'Z' THEN 0 WHEN 'Q1' THEN 1 WHEN 'Q2' THEN 2
            WHEN 'Q3' THEN 3 WHEN 'Q4' THEN 4 ELSE 5
          END AS stratum_order,
          o.method,
          CASE o.method
            WHEN 'uniform_random' THEN 0
            WHEN 'lru' THEN 1
            WHEN 'clean_linear' THEN 2
            WHEN 'clean_pairwise_logistic' THEN 3
            WHEN 'frozen_hgb' THEN 4
            ELSE 99
          END AS method_order,
          COUNT(*) AS n_decisions,
          AVG(a.alt_value) AS mean_alt_value,
          AVG(o.realized_regret) AS mean_regret,
          quantile_cont(o.realized_regret, 0.5) AS median_regret,
          AVG(o.optimal_selection_rate) AS optimal_selection_rate
        FROM selector_outcomes o
        JOIN alt_metric_strata a
          ON o.trace_name = a.trace_name
         AND o.trace_family = a.trace_family
         AND o.dataset_source = a.dataset_source
         AND o.capacity = a.capacity
         AND o.horizon = a.horizon
         AND o.decision_id = a.decision_id
         AND o.decision_t = a.decision_t
         AND o.decision_chunk_id = a.decision_chunk_id
         AND o.split = a.split
        GROUP BY ALL
        ORDER BY alt_metric, stratum_order, method_order
        """,
        OUT / "secondary_metric_method_summary.csv",
    )
    _copy(
        con,
        """
        SELECT
          trace_family, informativeness_stratum, stratum_order, method,
          CASE method
            WHEN 'uniform_random' THEN 0
            WHEN 'lru' THEN 1
            WHEN 'clean_linear' THEN 2
            WHEN 'clean_pairwise_logistic' THEN 3
            WHEN 'frozen_hgb' THEN 4
            ELSE 99
          END AS method_order,
          COUNT(*) AS n_decisions,
          AVG(expected_random_regret) AS mean_expected_random_regret,
          AVG(realized_regret) AS mean_regret,
          AVG(optimal_selection_rate) AS optimal_selection_rate
        FROM selector_joined
        GROUP BY ALL
        ORDER BY trace_family, stratum_order, method_order
        """,
        OUT / "family_robustness_method_summary.csv",
    )
    _copy(
        con,
        """
        SELECT
          capacity, informativeness_stratum, stratum_order, method,
          CASE method
            WHEN 'uniform_random' THEN 0
            WHEN 'lru' THEN 1
            WHEN 'clean_linear' THEN 2
            WHEN 'clean_pairwise_logistic' THEN 3
            WHEN 'frozen_hgb' THEN 4
            ELSE 99
          END AS method_order,
          COUNT(*) AS n_decisions,
          AVG(expected_random_regret) AS mean_expected_random_regret,
          AVG(realized_regret) AS mean_regret,
          AVG(optimal_selection_rate) AS optimal_selection_rate
        FROM selector_joined
        GROUP BY ALL
        ORDER BY capacity, stratum_order, method_order
        """,
        OUT / "capacity_robustness_method_summary.csv",
    )
    _copy(
        con,
        """
        SELECT
          horizon, informativeness_stratum, stratum_order, method,
          CASE method
            WHEN 'uniform_random' THEN 0
            WHEN 'lru' THEN 1
            WHEN 'clean_linear' THEN 2
            WHEN 'clean_pairwise_logistic' THEN 3
            WHEN 'frozen_hgb' THEN 4
            ELSE 99
          END AS method_order,
          COUNT(*) AS n_decisions,
          AVG(expected_random_regret) AS mean_expected_random_regret,
          AVG(realized_regret) AS mean_regret,
          AVG(optimal_selection_rate) AS optimal_selection_rate
        FROM selector_joined
        GROUP BY ALL
        ORDER BY horizon, stratum_order, method_order
        """,
        OUT / "horizon_robustness_method_summary.csv",
    )
    _copy(
        con,
        """
        SELECT
          informativeness_stratum, stratum_order, method,
          CASE method
            WHEN 'uniform_random' THEN 0
            WHEN 'lru' THEN 1
            WHEN 'clean_linear' THEN 2
            WHEN 'clean_pairwise_logistic' THEN 3
            WHEN 'frozen_hgb' THEN 4
            ELSE 99
          END AS method_order,
          COUNT(*) AS n_decisions,
          AVG(expected_random_regret) AS mean_expected_random_regret,
          AVG(realized_regret) AS mean_regret,
          AVG(optimal_selection_rate) AS optimal_selection_rate
        FROM selector_joined
        WHERE trace_family <> 'wiki2018'
        GROUP BY ALL
        ORDER BY stratum_order, method_order
        """,
        OUT / "excluding_wiki2018_method_summary.csv",
    )
    _copy(
        con,
        """
        SELECT
          informativeness_stratum, stratum_order, method,
          CASE method
            WHEN 'uniform_random' THEN 0
            WHEN 'lru' THEN 1
            WHEN 'clean_linear' THEN 2
            WHEN 'clean_pairwise_logistic' THEN 3
            WHEN 'frozen_hgb' THEN 4
            ELSE 99
          END AS method_order,
          COUNT(*) AS n_decisions,
          AVG(expected_random_regret) AS mean_expected_random_regret,
          AVG(realized_regret) AS mean_regret,
          AVG(optimal_selection_rate) AS optimal_selection_rate
        FROM selector_joined
        WHERE split = 'test'
        GROUP BY ALL
        ORDER BY stratum_order, method_order
        """,
        OUT / "test_split_method_summary.csv",
    )

    baseline = con.execute(
        """
        SELECT
          COUNT(*) AS total_decision_horizon_count,
          SUM(candidate_count) AS total_candidate_rows,
          AVG(CASE WHEN expected_random_regret = 0 THEN 1.0 ELSE 0.0 END) AS all_tied_fraction,
          1.0 - AVG(CASE WHEN expected_random_regret = 0 THEN 1.0 ELSE 0.0 END) AS discriminative_fraction,
          AVG(random_optimal_probability) AS random_optimal_probability,
          AVG(expected_random_regret) AS expected_uniform_random_regret,
          AVG(CASE WHEN optimal_candidate_count = 1 THEN 1.0 ELSE 0.0 END) AS unique_winner_fraction,
          MIN(optimal_candidate_count) AS min_optimal_set_size,
          AVG(optimal_candidate_count) AS mean_optimal_set_size,
          MAX(optimal_candidate_count) AS max_optimal_set_size,
          quantile_cont(expected_random_regret, 0.9) AS p90_expected_random_regret,
          quantile_cont(expected_random_regret, 0.95) AS p95_expected_random_regret,
          quantile_cont(expected_random_regret, 0.99) AS p99_expected_random_regret
        FROM decision_strata
        """
    ).fetchdf().to_dict(orient="records")[0]
    validation = con.execute(
        """
        SELECT
          SUM(CASE WHEN expected_random_regret = 0 AND informativeness_stratum <> 'Z' THEN 1 ELSE 0 END) AS zero_not_z,
          SUM(CASE WHEN expected_random_regret > 0 AND informativeness_stratum = 'Z' THEN 1 ELSE 0 END) AS positive_z,
          COUNT(*) AS n_decisions,
          SUM(candidate_count) AS n_candidate_rows
        FROM decision_strata
        """
    ).fetchdf().to_dict(orient="records")[0]
    baseline["elapsed_seconds"] = time.time() - t0
    baseline["validation"] = validation
    (OUT / "baseline_facts.json").write_text(json.dumps(baseline, indent=2) + "\n")
    print(json.dumps(baseline, indent=2))


if __name__ == "__main__":
    main()
