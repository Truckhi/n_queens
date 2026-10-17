# ============================================================
# N-QUEENS USING CPLEX CP OPTIMIZER
# Benchmark: N = 2, 3, 4, 8, 20, 50, 100
# 5 runs / N, time limit 30s, 1 worker
# Kết quả benchmark được tổng hợp bằng median.
# ============================================================

from docplex.cp.model import CpoModel

import time
import csv

from statistics import median


# ============================================================
# Cấu hình benchmark
# ============================================================

TEST_VALUES = [
    2,
    3,
    4,
    8,
    20,
    50,
    100,
]

REPEATS = 5

TIMEOUT_SECONDS = 30

WORKERS = 1


# ============================================================
# Tạo mô hình N-Queens bằng CPLEX CP
# queens[row] biểu diễn cột đặt hậu ở hàng row.
# ============================================================

def build_nqueens_cplex_cp(n):

    model = CpoModel()


    queens = model.integer_var_list(
        n,
        0,
        n - 1,
        name="q"
    )


    # Các hậu phải nằm ở các cột khác nhau
    model.add(
        model.all_diff(queens)
    )


    # Đường chéo "\": queens[row] - row phải khác nhau
    diagonal_1 = [

        queens[row] - row

        for row in range(n)
    ]

    model.add(
        model.all_diff(diagonal_1)
    )


    # Đường chéo "/": queens[row] + row phải khác nhau
    diagonal_2 = [

        queens[row] + row

        for row in range(n)
    ]

    model.add(
        model.all_diff(diagonal_2)
    )


    return model, queens


# ============================================================
# Giải một bài toán N-Queens
# Hàm dùng để kiểm tra nghiệm trực tiếp.
# ============================================================

def solve_nqueens_cplex_cp(
    n,
    timeout_seconds=TIMEOUT_SECONDS
):

    model, queens = (
        build_nqueens_cplex_cp(n)
    )


    start = time.perf_counter()


    result = model.solve(

        TimeLimit=timeout_seconds,

        Workers=WORKERS,

        LogVerbosity="Quiet"
    )


    end = time.perf_counter()


    solve_time = (
        end - start
    )


    # Trạng thái kết quả
    if result.is_solution():

        print("Ket qua: SAT")

        print(
            "\nVi tri cac quan hau:"
        )

        for row in range(n):

            print(
                f"Hang {row}: "
                f"cot {result[queens[row]]}"
            )


    else:

        solve_status = str(
            result.get_solve_status()
        ).lower()

        if "infeasible" in solve_status:

            print(
                "Ket qua: UNSAT"
            )

        else:

            print(
                "Ket qua: TIMEOUT"
            )


    print(
        "Thoi gian solve =",
        solve_time
    )


# ============================================================
# Benchmark CPLEX CP một lần
# Đo thời gian tạo mô hình và thời gian giải.
# ============================================================

def benchmark_cplex_cp_once(
    n,
    timeout_seconds=TIMEOUT_SECONDS
):

    # Model time
    model_start = (
        time.perf_counter()
    )


    model, queens = (
        build_nqueens_cplex_cp(n)
    )


    model_end = (
        time.perf_counter()
    )


    model_time = (
        model_end
        - model_start
    )


    # Solve time
    solve_start = (
        time.perf_counter()
    )


    result = model.solve(

        TimeLimit=timeout_seconds,

        Workers=WORKERS,

        LogVerbosity="Quiet"
    )


    solve_end = (
        time.perf_counter()
    )


    solve_time = (
        solve_end
        - solve_start
    )


    total_time = (
        model_time
        + solve_time
    )


    # Xác định trạng thái
    if result.is_solution():

        result_status = "SAT"


    else:

        solve_status = str(
            result.get_solve_status()
        ).lower()


        if "infeasible" in solve_status:

            result_status = "UNSAT"


        else:

            result_status = "TIMEOUT"


    return {

        "Solver":
            "CPLEX CP",

        "N":
            n,

        "Model_Time":
            model_time,

        "Solving_Time":
            solve_time,

        "Total_Time":
            total_time,

        "Status":
            result_status
    }


# ============================================================
# Chạy mỗi N nhiều lần và lấy median
# ============================================================

def benchmark_cplex_cp_repeated(
    n,
    repeats=REPEATS,
    timeout_seconds=TIMEOUT_SECONDS
):

    runs = []


    print(
        f"\nRunning CPLEX CP N={n}"
    )


    for run_id in range(
        1,
        repeats + 1
    ):

        print(
            f"    Run {run_id}/{repeats}"
        )


        result = (
            benchmark_cplex_cp_once(
                n,
                timeout_seconds
            )
        )


        result[
            "Run"
        ] = run_id


        runs.append(
            result
        )


    # Các lần chạy hoàn thành
    completed_runs = [

        result

        for result in runs

        if result["Status"]
        in (
            "SAT",
            "UNSAT"
        )
    ]


    # Trường hợp không có lần chạy nào hoàn thành
    if len(
        completed_runs
    ) == 0:

        summary = {

            "Solver":
                "CPLEX CP",

            "N":
                n,

            "Model_Time":
                median(
                    [
                        result[
                            "Model_Time"
                        ]
                        for result
                        in runs
                    ]
                ),

            "Solving_Time":
                median(
                    [
                        result[
                            "Solving_Time"
                        ]
                        for result
                        in runs
                    ]
                ),

            "Total_Time":
                median(
                    [
                        result[
                            "Total_Time"
                        ]
                        for result
                        in runs
                    ]
                ),

            "Status":
                "TIMEOUT"
        }


        return (
            summary,
            runs
        )


    # Trạng thái tổng hợp
    base_status = (
        completed_runs[0][
            "Status"
        ]
    )


    if (
        len(completed_runs)
        == repeats
    ):

        final_status = (
            base_status
        )


    else:

        final_status = (

            f"{base_status} "

            f"{len(completed_runs)}"

            f"/{repeats}"
        )


    # Median của các lần chạy hoàn thành
    summary = {

        "Solver":
            "CPLEX CP",

        "N":
            n,

        "Model_Time":
            median(
                [
                    result[
                        "Model_Time"
                    ]

                    for result
                    in completed_runs
                ]
            ),

        "Solving_Time":
            median(
                [
                    result[
                        "Solving_Time"
                    ]

                    for result
                    in completed_runs
                ]
            ),

        "Total_Time":
            median(
                [
                    result[
                        "Total_Time"
                    ]

                    for result
                    in completed_runs
                ]
            ),

        "Status":
            final_status
    }


    return (
        summary,
        runs
    )


# ============================================================
# Định dạng thời gian
# ============================================================

def format_time(value):

    if value is None:

        return "-"


    return (
        f"{value:.6f}"
    )


# ============================================================
# In bảng kết quả median
# ============================================================

def print_benchmark_results(
    results
):

    print()


    print(
        "CPLEX CP BENCHMARK "
        "- MEDIAN OF 5 RUNS"
    )


    print(
        "=" * 80
    )


    print(

        f"{'N':<8}"

        f"{'Model(s)':<16}"

        f"{'Solve(s)':<16}"

        f"{'Total(s)':<16}"

        f"{'Status':<15}"
    )


    print(
        "=" * 80
    )


    for result in results:

        print(

            f"{result['N']:<8}"

            f"{format_time(result['Model_Time']):<16}"

            f"{format_time(result['Solving_Time']):<16}"

            f"{format_time(result['Total_Time']):<16}"

            f"{result['Status']:<15}"
        )


    print(
        "=" * 80
    )


# ============================================================
# Lưu kết quả median
# ============================================================

def save_median_results(
    results
):

    filename = (
        "benchmark_cplex_cp_median.csv"
    )


    fieldnames = [

        "Solver",

        "N",

        "Model_Time",

        "Solving_Time",

        "Total_Time",

        "Status"
    ]


    with open(

        filename,

        "w",

        newline="",

        encoding="utf-8-sig"

    ) as file:


        writer = csv.DictWriter(

            file,

            fieldnames=fieldnames
        )


        writer.writeheader()


        writer.writerows(
            results
        )


    print(
        "\nDa luu median vao:",
        filename
    )


# ============================================================
# Lưu toàn bộ các lần chạy
# ============================================================

def save_raw_results(
    results
):

    filename = (
        "benchmark_cplex_cp_runs.csv"
    )


    fieldnames = [

        "Solver",

        "N",

        "Run",

        "Model_Time",

        "Solving_Time",

        "Total_Time",

        "Status"
    ]


    with open(

        filename,

        "w",

        newline="",

        encoding="utf-8-sig"

    ) as file:


        writer = csv.DictWriter(

            file,

            fieldnames=fieldnames
        )


        writer.writeheader()


        writer.writerows(
            results
        )


    print(
        "Da luu raw runs vao:",
        filename
    )


# ============================================================
# Main
# ============================================================

if __name__ == "__main__":

    print()


    print(
        "=" * 80
    )


    print(
        "N-QUEENS CPLEX CP BENCHMARK"
    )


    print(
        f"Runs per N: {REPEATS}"
    )


    print(
        f"Time limit: "
        f"{TIMEOUT_SECONDS}s"
    )


    print(
        f"Workers: {WORKERS}"
    )


    print(
        "=" * 80
    )


    median_results = []

    raw_results = []


    # Chạy benchmark
    for n in TEST_VALUES:

        summary, runs = (
            benchmark_cplex_cp_repeated(

                n,

                repeats=REPEATS,

                timeout_seconds=
                    TIMEOUT_SECONDS
            )
        )


        median_results.append(
            summary
        )


        raw_results.extend(
            runs
        )


    # In kết quả
    print_benchmark_results(
        median_results
    )


    # Lưu CSV
    save_median_results(
        median_results
    )


    save_raw_results(
        raw_results
    )