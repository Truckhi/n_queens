# ============================================================
# FINAL ANALYSIS FOR N-QUEENS BENCHMARK
#
# Experiment structure:
#
#   SAT:
#       Pairwise
#       Sequential
#       Binary
#       Commander
#       Product
#
#   Exact methods:
#       CP-SAT
#       CPLEX CP
#       CPLEX MIP
#       Gurobi MIP
#
# Input:
#   benchmark_sat_median.csv
#   OR benchmark_results_median.csv
#
#   benchmark_cpsat_median.csv
#   benchmark_cplex_cp_median.csv
#   benchmark_cplex_mip_median.csv
#   benchmark_gurobi_median.csv
#
# Output:
#   benchmark_all_methods.csv
#   total_time_comparison.csv
#   status_comparison.csv
#   exact_methods_time_breakdown.csv
#
#   charts/
#       01_total_runtime_all_methods.png
#       02_sat_runtime_comparison.png
#       03_exact_methods_runtime.png
#       04_sat_clause_comparison.png
#       05_sat_variable_comparison.png
#       06_sat_solve_time_comparison.png
# ============================================================


from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


# ============================================================
# CONFIG
# ============================================================

BASE_DIR = Path(__file__).resolve().parent

CHART_DIR = BASE_DIR / "charts"

CHART_DIR.mkdir(
    exist_ok=True
)


N_VALUES = [
    2,
    3,
    4,
    8,
    20,
    50,
    100,
]


SAT_ENCODINGS = [
    "Pairwise",
    "Sequential",
    "Binary",
    "Commander",
    "Product",
]


EXACT_METHODS = [
    "CP-SAT",
    "CPLEX CP",
    "CPLEX MIP",
    "Gurobi MIP",
]


METHOD_ORDER = [
    "SAT - Pairwise",
    "SAT - Sequential",
    "SAT - Binary",
    "SAT - Commander",
    "SAT - Product",

    "CP-SAT",
    "CPLEX CP",
    "CPLEX MIP",
    "Gurobi MIP",
]


# Timeout dùng trong benchmark final
TIMEOUT_SECONDS = 30


# ============================================================
# 1. TÌM FILE
# ============================================================

def find_existing_file(candidates):

    for filename in candidates:

        path = BASE_DIR / filename

        if path.exists():

            return path


    raise FileNotFoundError(
        "Khong tim thay file nao trong: "
        + ", ".join(candidates)
    )


# ============================================================
# SAT
#
# Hỗ trợ cả tên cũ và tên mới
# ============================================================

SAT_FILE = find_existing_file(
    [
        "benchmark_sat_median.csv",
        "benchmark_results_median.csv",
    ]
)


# ============================================================
# CP-SAT
# ============================================================

CPSAT_FILE = find_existing_file(
    [
        "benchmark_cpsat_median.csv",
    ]
)


# ============================================================
# CPLEX CP
# ============================================================

CPLEX_CP_FILE = find_existing_file(
    [
        "benchmark_cplex_cp_median.csv",
    ]
)


# ============================================================
# CPLEX MIP
# ============================================================

CPLEX_MIP_FILE = find_existing_file(
    [
        "benchmark_cplex_mip_median.csv",
    ]
)


# ============================================================
# GUROBI
# ============================================================

GUROBI_FILE = find_existing_file(
    [
        "benchmark_gurobi_median.csv",
    ]
)


# ============================================================
# 2. HELPER FUNCTIONS
# ============================================================

def read_csv(path):

    return pd.read_csv(
        path,
        encoding="utf-8-sig"
    )


def numeric_column(
    df,
    possible_names
):

    for column in possible_names:

        if column in df.columns:

            return pd.to_numeric(
                df[column],
                errors="coerce"
            )


    return pd.Series(
        np.nan,
        index=df.index,
        dtype=float
    )


def text_column(
    df,
    possible_names,
    default=""
):

    for column in possible_names:

        if column in df.columns:

            return (
                df[column]
                .fillna(default)
                .astype(str)
            )


    return pd.Series(
        default,
        index=df.index,
        dtype=str
    )


def is_timeout_status(status):

    return (
        "TIMEOUT"
        in str(status).upper()
    )


def is_success_status(status):

    status = str(
        status
    ).upper()


    return (
        status.startswith("SAT")
        or
        status.startswith("UNSAT")
    )


# ============================================================
# 3. LOAD SAT
# ============================================================

def load_sat():

    df = read_csv(
        SAT_FILE
    )


    required_columns = [
        "Encoding",
        "N",
        "Status",
    ]


    for column in required_columns:

        if column not in df.columns:

            raise ValueError(
                f"SAT file thieu cot: "
                f"{column}"
            )


    # ========================================================
    # Tạo DataFrame với cùng index file gốc
    # ========================================================

    result = pd.DataFrame(
        index=df.index
    )


    result["Method"] = (
        "SAT - "
        + df["Encoding"].astype(str)
    )


    result["Category"] = (
        "SAT"
    )


    result["Encoding"] = (
        df["Encoding"].astype(str)
    )


    result["N"] = pd.to_numeric(
        df["N"],
        errors="coerce"
    )


    # ========================================================
    # MODEL SIZE
    # ========================================================

    result["Variables"] = numeric_column(
        df,
        [
            "Variables",
        ]
    )


    result["Clauses"] = numeric_column(
        df,
        [
            "Clauses",
        ]
    )


    result["Constraints"] = (
        np.nan
    )


    # ========================================================
    # SAT BUILD TIME
    #
    # Build =
    # Encoding + Loading CNF
    # ========================================================

    encode_time = numeric_column(
        df,
        [
            "Encode_Time",
            "Encoding_Time",
        ]
    )


    load_time = numeric_column(
        df,
        [
            "Load_Time",
        ]
    )


    result["Build_Time"] = (
        encode_time
        + load_time
    )


    # ========================================================
    # SOLVE TIME
    # ========================================================

    result["Solve_Time"] = numeric_column(
        df,
        [
            "Solve_Time",
            "Solving_Time",
        ]
    )


    # ========================================================
    # TOTAL TIME
    # ========================================================

    result["Total_Time"] = numeric_column(
        df,
        [
            "Total_Time",
        ]
    )


    # ========================================================
    # STATUS
    # ========================================================

    result["Status"] = text_column(
        df,
        [
            "Status",
        ]
    )


    return result


# ============================================================
# 4. LOAD GENERIC EXACT METHOD
#
# Dùng cho:
#   CP-SAT
#   CPLEX CP
#   CPLEX MIP
#   Gurobi MIP
# ============================================================

def load_exact_method(
    path,
    method_name
):

    df = read_csv(
        path
    )


    if "N" not in df.columns:

        raise ValueError(
            f"{path.name} khong co cot N"
        )


    result = pd.DataFrame(
        index=df.index
    )


    # ========================================================
    # METHOD
    # ========================================================

    result["Method"] = (
        method_name
    )


    result["Category"] = (
        "Exact"
    )


    result["Encoding"] = (
        ""
    )


    # ========================================================
    # N
    # ========================================================

    result["N"] = pd.to_numeric(
        df["N"],
        errors="coerce"
    )


    # ========================================================
    # MODEL SIZE
    # ========================================================

    result["Variables"] = numeric_column(
        df,
        [
            "Variables",
        ]
    )


    result["Clauses"] = (
        np.nan
    )


    result["Constraints"] = numeric_column(
        df,
        [
            "Constraints",
        ]
    )


    # ========================================================
    # MODEL / BUILD TIME
    # ========================================================

    result["Build_Time"] = numeric_column(
        df,
        [
            "Model_Time",
            "Model(s)",
        ]
    )


    # ========================================================
    # SOLVING TIME
    # ========================================================

    result["Solve_Time"] = numeric_column(
        df,
        [
            "Solve_Time",
            "Solving_Time",
            "Solve(s)",
        ]
    )


    # ========================================================
    # TOTAL TIME
    # ========================================================

    result["Total_Time"] = numeric_column(
        df,
        [
            "Total_Time",
            "Total(s)",
        ]
    )


    # ========================================================
    # STATUS
    # ========================================================

    result["Status"] = text_column(
        df,
        [
            "Status",
        ]
    )


    return result


# ============================================================
# 5. LOAD ALL RESULTS
# ============================================================

sat = load_sat()


cpsat = load_exact_method(
    CPSAT_FILE,
    "CP-SAT"
)


cplex_cp = load_exact_method(
    CPLEX_CP_FILE,
    "CPLEX CP"
)


cplex_mip = load_exact_method(
    CPLEX_MIP_FILE,
    "CPLEX MIP"
)


gurobi = load_exact_method(
    GUROBI_FILE,
    "Gurobi MIP"
)


# ============================================================
# GHÉP TẤT CẢ
# ============================================================

all_results = pd.concat(
    [
        sat,
        cpsat,
        cplex_cp,
        cplex_mip,
        gurobi,
    ],
    ignore_index=True
)


# ============================================================
# LOẠI N KHÔNG HỢP LỆ
# ============================================================

all_results = all_results[
    all_results["N"].notna()
].copy()


all_results["N"] = (
    all_results["N"]
    .astype(int)
)


# ============================================================
# 6. SORT
# ============================================================

method_rank = {

    method:
        index

    for index, method
    in enumerate(
        METHOD_ORDER
    )
}


all_results[
    "_method_rank"
] = (

    all_results[
        "Method"
    ].map(
        method_rank
    )
)


all_results = (

    all_results
    .sort_values(
        [
            "_method_rank",
            "N",
        ],
        na_position="last"
    )
    .drop(
        columns=[
            "_method_rank",
        ]
    )
    .reset_index(
        drop=True
    )
)


# ============================================================
# 7. KIỂM TRA DATA SAU KHI LOAD
# ============================================================

print()

print(
    "=" * 95
)

print(
    "CHECK LOADED METHODS"
)

print(
    "=" * 95
)


for method in METHOD_ORDER:

    count = int(
        (
            all_results[
                "Method"
            ] == method
        ).sum()
    )


    if count > 0:

        print(
            f"OK      {method:<20}"
            f" rows = {count}"
        )


    else:

        print(
            f"MISSING {method}"
        )


print(
    "=" * 95
)


# ============================================================
# 8. SAVE COMBINED CSV
# ============================================================

combined_file = (
    BASE_DIR
    / "benchmark_all_methods.csv"
)


all_results.to_csv(
    combined_file,
    index=False,
    encoding="utf-8-sig"
)


# ============================================================
# 9. TOTAL TIME TABLE
# ============================================================

total_time_table = (

    all_results
    .pivot_table(
        index="N",
        columns="Method",
        values="Total_Time",
        aggfunc="first"
    )
    .reindex(
        N_VALUES
    )
)


ordered_columns = [

    method

    for method
    in METHOD_ORDER

    if method
    in total_time_table.columns
]


total_time_table = (
    total_time_table[
        ordered_columns
    ]
)


total_time_file = (
    BASE_DIR
    / "total_time_comparison.csv"
)


total_time_table.to_csv(
    total_time_file,
    encoding="utf-8-sig"
)


# ============================================================
# 10. STATUS TABLE
# ============================================================

status_table = (

    all_results
    .pivot_table(
        index="N",
        columns="Method",
        values="Status",
        aggfunc="first"
    )
    .reindex(
        N_VALUES
    )
)


status_columns = [

    method

    for method
    in METHOD_ORDER

    if method
    in status_table.columns
]


status_table = (
    status_table[
        status_columns
    ]
)


status_file = (
    BASE_DIR
    / "status_comparison.csv"
)


status_table.to_csv(
    status_file,
    encoding="utf-8-sig"
)


# ============================================================
# 11. EXACT METHODS TIME BREAKDOWN
#
# Xuất riêng Model / Solve / Total time cho:
#   CP-SAT
#   CPLEX CP
#   CPLEX MIP
#   Gurobi MIP
#
# Phần này chỉ tạo thêm CSV.
# Không thay đổi dữ liệu dùng để vẽ chart.
# ============================================================

exact_methods_breakdown = (

    all_results[

        all_results[
            "Method"
        ].isin(
            EXACT_METHODS
        )

    ][
        [
            "Method",
            "N",
            "Build_Time",
            "Solve_Time",
            "Total_Time",
            "Status",
        ]
    ]
    .copy()
)


# Trong các solver CP/MIP,
# Build_Time chính là thời gian tạo model.
exact_methods_breakdown = (

    exact_methods_breakdown
    .rename(
        columns={
            "Build_Time":
                "Model_Time",
        }
    )
)


# Giữ thứ tự:
# CP-SAT -> CPLEX CP -> CPLEX MIP -> Gurobi MIP
exact_method_rank = {

    method:
        index

    for index, method
    in enumerate(
        EXACT_METHODS
    )
}


exact_methods_breakdown[
    "_method_rank"
] = (

    exact_methods_breakdown[
        "Method"
    ].map(
        exact_method_rank
    )
)


exact_methods_breakdown = (

    exact_methods_breakdown
    .sort_values(
        [
            "_method_rank",
            "N",
        ]
    )
    .drop(
        columns=[
            "_method_rank",
        ]
    )
    .reset_index(
        drop=True
    )
)


exact_methods_breakdown_file = (
    BASE_DIR
    / "exact_methods_time_breakdown.csv"
)


exact_methods_breakdown.to_csv(
    exact_methods_breakdown_file,
    index=False,
    encoding="utf-8-sig"
)


# ============================================================
# 12. PLOT HELPER
# ============================================================

def plot_method_lines(
    dataframe,
    methods,
    value_column,
    title,
    ylabel,
    output_filename,
    log_scale=True,
    mark_timeouts=False,
    success_only=True
):

    fig, ax = plt.subplots(
        figsize=(11, 7)
    )


    # Dùng để tránh label timeout
    # chồng hoàn toàn lên nhau.
    timeout_stack = {}


    for method in methods:

        subset = dataframe[
            dataframe[
                "Method"
            ] == method
        ].sort_values(
            "N"
        )


        if subset.empty:

            continue


        # ====================================================
        # Chọn dữ liệu để nối đường
        #
        # Runtime:
        #   chỉ nối các instance hoàn thành.
        #
        # Variable / Clause:
        #   không phụ thuộc SAT/TIMEOUT,
        #   miễn có số liệu thì vẫn vẽ.
        # ====================================================

        if success_only:

            line_data = subset[
                subset[
                    "Status"
                ].apply(
                    is_success_status
                )
            ].copy()


        else:

            line_data = (
                subset.copy()
            )


        line_data = line_data[
            line_data[
                value_column
            ].notna()
        ]


        line_color = None


        if not line_data.empty:

            line, = ax.plot(

                line_data["N"],

                line_data[
                    value_column
                ],

                marker="o",

                linewidth=1.8,

                label=method
            )


            line_color = (
                line.get_color()
            )


        # ====================================================
        # TIMEOUT MARKERS
        # ====================================================

        if mark_timeouts:

            timeout = subset[
                subset[
                    "Status"
                ].apply(
                    is_timeout_status
                )
            ].copy()


            if not timeout.empty:

                # ============================================
                # Nếu Total_Time bị thiếu ở timeout,
                # đặt marker tại giới hạn 30 giây.
                # ============================================

                timeout[
                    "_plot_value"
                ] = timeout[
                    value_column
                ]


                if (
                    value_column
                    == "Total_Time"
                ):

                    timeout[
                        "_plot_value"
                    ] = (

                        timeout[
                            "_plot_value"
                        ]
                        .fillna(
                            TIMEOUT_SECONDS
                        )
                    )


                timeout = timeout[
                    timeout[
                        "_plot_value"
                    ].notna()
                ]


                if not timeout.empty:

                    scatter_args = {

                        "marker":
                            "x",

                        "s":
                            90,

                        "linewidths":
                            2,
                    }


                    if line_color is not None:

                        scatter_args[
                            "color"
                        ] = line_color


                    ax.scatter(

                        timeout["N"],

                        timeout[
                            "_plot_value"
                        ],

                        **scatter_args
                    )


                    # ========================================
                    # Ghi rõ encoding nào timeout
                    # ========================================

                    for _, row in timeout.iterrows():

                        n_value = int(
                            row["N"]
                        )


                        stack_index = (
                            timeout_stack.get(
                                n_value,
                                0
                            )
                        )


                        timeout_stack[
                            n_value
                        ] = (
                            stack_index
                            + 1
                        )


                        short_name = (
                            method.replace(
                                "SAT - ",
                                ""
                            )
                        )


                        ax.annotate(

                            f"{short_name} Timeout",

                            (
                                row["N"],
                                row[
                                    "_plot_value"
                                ]
                            ),

                            xytext=(
                                5,
                                7
                                + 12
                                * stack_index
                            ),

                            textcoords=
                                "offset points",

                            fontsize=8
                        )


    # ========================================================
    # TITLE / AXES
    # ========================================================

    ax.set_title(
        title
    )


    ax.set_xlabel(
        "N"
    )


    ax.set_ylabel(
        ylabel
    )


    ax.set_xticks(
        N_VALUES
    )


    if log_scale:

        ax.set_yscale(
            "log"
        )


    ax.grid(
        True,
        which="both",
        linestyle="--",
        alpha=0.35
    )


    # ========================================================
    # LEGEND
    # ========================================================

    handles, labels = (
        ax.get_legend_handles_labels()
    )


    if handles:

        ax.legend(
            fontsize=8
        )


    fig.tight_layout()


    # ========================================================
    # SAVE
    # ========================================================

    output_path = (
        CHART_DIR
        / output_filename
    )


    fig.savefig(
        output_path,
        dpi=300,
        bbox_inches="tight"
    )


    plt.close(
        fig
    )


# ============================================================
# 13. CHART 1
#
# TOTAL RUNTIME:
# TẤT CẢ PHƯƠNG PHÁP
#
# 5 SAT encoding
# +
# 4 exact methods
# ============================================================

plot_method_lines(

    dataframe=
        all_results,

    methods=
        METHOD_ORDER,

    value_column=
        "Total_Time",

    title=
        "N-Queens: Total Runtime Comparison",

    ylabel=
        "Median Total Time (seconds, log scale)",

    output_filename=
        "01_total_runtime_all_methods.png",

    log_scale=True,

    mark_timeouts=True,

    success_only=True
)


# ============================================================
# 14. CHART 2
#
# SAT ENCODING TOTAL RUNTIME
# ============================================================

sat_methods = [

    f"SAT - {encoding}"

    for encoding
    in SAT_ENCODINGS
]


plot_method_lines(

    dataframe=
        all_results,

    methods=
        sat_methods,

    value_column=
        "Total_Time",

    title=
        "SAT Encoding Runtime Comparison",

    ylabel=
        "Median Total Time (seconds, log scale)",

    output_filename=
        "02_sat_runtime_comparison.png",

    log_scale=True,

    mark_timeouts=True,

    success_only=True
)


# ============================================================
# 15. CHART 3
#
# EXACT METHODS:
#
# CP-SAT
# CPLEX CP
# CPLEX MIP
# Gurobi MIP
# ============================================================

plot_method_lines(

    dataframe=
        all_results,

    methods=
        EXACT_METHODS,

    value_column=
        "Total_Time",

    title=
        "Exact Method Runtime Comparison",

    ylabel=
        "Median Total Time (seconds, log scale)",

    output_filename=
        "03_exact_methods_runtime.png",

    log_scale=True,

    mark_timeouts=True,

    success_only=True
)


# ============================================================
# 16. CHART 4
#
# SAT CLAUSE COUNT
#
# Đây là thuộc tính encoding,
# không phụ thuộc solver có timeout hay không.
# ============================================================

plot_method_lines(

    dataframe=
        all_results,

    methods=
        sat_methods,

    value_column=
        "Clauses",

    title=
        "SAT Encoding Clause Count",

    ylabel=
        "Number of Clauses (log scale)",

    output_filename=
        "04_sat_clause_comparison.png",

    log_scale=True,

    mark_timeouts=False,

    success_only=False
)


# ============================================================
# 17. CHART 5
#
# SAT VARIABLE COUNT
#
# Đây cũng là thuộc tính encoding.
# ============================================================

plot_method_lines(

    dataframe=
        all_results,

    methods=
        sat_methods,

    value_column=
        "Variables",

    title=
        "SAT Encoding Variable Count",

    ylabel=
        "Number of Variables (log scale)",

    output_filename=
        "05_sat_variable_comparison.png",

    log_scale=True,

    mark_timeouts=False,

    success_only=False
)


# ============================================================
# 18. CHART 6
#
# SAT SOLVE TIME ONLY
#
# Phân biệt:
#
#   Encoding / Loading
#
# với
#
#   Actual SAT solving
# ============================================================

plot_method_lines(

    dataframe=
        all_results,

    methods=
        sat_methods,

    value_column=
        "Solve_Time",

    title=
        "SAT Encoding Solve-Time Comparison",

    ylabel=
        "Median Solve Time (seconds, log scale)",

    output_filename=
        "06_sat_solve_time_comparison.png",

    log_scale=True,

    mark_timeouts=False,

    success_only=True
)


# ============================================================
# 19. PRINT FINAL SUMMARY
# ============================================================

print()

print(
    "=" * 95
)

print(
    "FINAL N-QUEENS ANALYSIS"
)

print(
    "=" * 95
)


print()

print(
    "SAT file:",
    SAT_FILE.name
)


print(
    "CP-SAT file:",
    CPSAT_FILE.name
)


print(
    "CPLEX CP file:",
    CPLEX_CP_FILE.name
)


print(
    "CPLEX MIP file:",
    CPLEX_MIP_FILE.name
)


print(
    "Gurobi file:",
    GUROBI_FILE.name
)


# ============================================================
# METHOD CHECK
# ============================================================

print()

print(
    "Methods:"
)


for method in METHOD_ORDER:

    count = int(
        (
            all_results[
                "Method"
            ] == method
        ).sum()
    )


    if count > 0:

        print(
            f"  OK      "
            f"{method:<20}"
            f" rows={count}"
        )


    else:

        print(
            f"  MISSING "
            f"{method}"
        )


# ============================================================
# OUTPUT FILES
# ============================================================

print()

print(
    "Combined data:",
    combined_file.name
)


print(
    "Runtime table:",
    total_time_file.name
)


print(
    "Status table:",
    status_file.name
)


print(
    "Exact-method breakdown:",
    exact_methods_breakdown_file.name
)


print(
    "Charts directory:",
    CHART_DIR
)


print()

print(
    "Generated charts:"
)


for chart in sorted(
    CHART_DIR.glob(
        "*.png"
    )
):

    print(
        "  ",
        chart.name
    )


print()

print(
    "=" * 95
)

print(
    "DONE"
)

print(
    "=" * 95
)