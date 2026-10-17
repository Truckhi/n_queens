# ============================================================
# N-QUEENS USING CP-SAT
# Benchmark: N = 2, 3, 4, 8, 20, 50, 100
# 5 runs / N, time limit 30s, 1 worker
# Kết quả benchmark được tổng hợp bằng median.
# ============================================================

from ortools.sat.python import cp_model

import time
import csv
from statistics import median


# ============================================================
# Tạo mô hình N-Queens
# queens[row] biểu diễn cột đặt hậu ở hàng row.
# ============================================================

def build_nqueens_model(n):

    model = cp_model.CpModel()

    queens = [
        model.NewIntVar(
            0,
            n - 1,
            f"q_{row}"
        )
        for row in range(n)
    ]


    # Các hậu phải nằm ở các cột khác nhau
    model.AddAllDifferent(queens)


    # Đường chéo "\": column - row phải khác nhau
    diagonal_1 = []

    for row in range(n):

        d = model.NewIntVar(
            -(n - 1),
            n - 1,
            f"d1_{row}"
        )

        model.Add(
            d == queens[row] - row
        )

        diagonal_1.append(d)

    model.AddAllDifferent(
        diagonal_1
    )


    # Đường chéo "/": column + row phải khác nhau
    diagonal_2 = []

    for row in range(n):

        d = model.NewIntVar(
            0,
            2 * n - 2,
            f"d2_{row}"
        )

        model.Add(
            d == queens[row] + row
        )

        diagonal_2.append(d)

    model.AddAllDifferent(
        diagonal_2
    )


    return model, queens


# ============================================================
# Giải một bài toán N-Queens
# Hàm dùng để kiểm tra nghiệm trực tiếp, không dùng cho benchmark.
# ============================================================

def solve_nqueens_cpsat(
    n,
    timeout_seconds=30
):

    model, queens = build_nqueens_model(n)

    solver = cp_model.CpSolver()

    solver.parameters.max_time_in_seconds = (
        timeout_seconds
    )

    solver.parameters.num_search_workers = 1

    solver.parameters.random_seed = 0


    start = time.perf_counter()

    status = solver.Solve(model)

    end = time.perf_counter()

    solve_time = end - start


    if status in (
        cp_model.OPTIMAL,
        cp_model.FEASIBLE
    ):

        print("Ket qua: SAT")

        print("\nVi tri cac quan hau:")

        for row in range(n):

            print(
                f"Hang {row}: "
                f"cot {solver.Value(queens[row])}"
            )


    elif status == cp_model.INFEASIBLE:

        print("Ket qua: UNSAT")


    elif status == cp_model.UNKNOWN:

        print("Ket qua: TIMEOUT")


    else:

        print("Ket qua: ERROR")


    print(
        "Thoi gian solve =",
        solve_time
    )


# ============================================================
# Benchmark CP-SAT một lần
# Đo thời gian tạo mô hình và thời gian giải.
# ============================================================

def benchmark_cpsat_once(
    n,
    timeout_seconds=30
):

    # Model time
    model_start = time.perf_counter()

    model, queens = build_nqueens_model(n)

    model_end = time.perf_counter()

    model_time = (
        model_end
        - model_start
    )


    solver = cp_model.CpSolver()

    solver.parameters.max_time_in_seconds = (
        timeout_seconds
    )

    solver.parameters.num_search_workers = 1

    solver.parameters.random_seed = 0


    # Solve time
    solve_start = time.perf_counter()

    status = solver.Solve(model)

    solve_end = time.perf_counter()

    solve_time = (
        solve_end
        - solve_start
    )


    total_time = (
        model_time
        + solve_time
    )


    # Trạng thái kết quả
    if status in (
        cp_model.OPTIMAL,
        cp_model.FEASIBLE
    ):

        result_status = "SAT"


    elif status == cp_model.INFEASIBLE:

        result_status = "UNSAT"


    elif status == cp_model.UNKNOWN:

        result_status = "TIMEOUT"


    else:

        result_status = "ERROR"


    return {

        "N": n,

        "Model_Time": model_time,

        "Solving_Time": solve_time,

        "Total_Time": total_time,

        "Status": result_status
    }


# ============================================================
# Chạy một N nhiều lần và lấy median
# ============================================================

def benchmark_cpsat_repeated(
    n,
    repeats=5,
    timeout_seconds=30
):

    runs = []


    print(
        f"\nRunning CP-SAT N={n}"
    )


    for run_id in range(
        1,
        repeats + 1
    ):

        print(
            f"    Run {run_id}/{repeats}"
        )


        result = benchmark_cpsat_once(
            n,
            timeout_seconds
        )


        result["Run"] = run_id


        runs.append(
            result
        )


    # Chỉ lấy các lần chạy hoàn thành
    completed_runs = [

        result

        for result in runs

        if result["Status"]
        in ("SAT", "UNSAT")
    ]


    # Trường hợp không có lần chạy nào hoàn thành
    if len(completed_runs) == 0:

        summary = {

            "N": n,

            "Model_Time": median([
                result["Model_Time"]
                for result in runs
            ]),

            "Solving_Time": median([
                result["Solving_Time"]
                for result in runs
            ]),

            "Total_Time": median([
                result["Total_Time"]
                for result in runs
            ]),

            "Status": "TIMEOUT"
        }


        return summary, runs


    # Xác định trạng thái tổng hợp
    base_status = (
        completed_runs[0]["Status"]
    )


    if len(completed_runs) == repeats:

        final_status = base_status


    else:

        final_status = (
            f"{base_status} "
            f"{len(completed_runs)}/{repeats}"
        )


    # Median của các lần chạy hoàn thành
    summary = {

        "N": n,


        "Model_Time": median([

            result["Model_Time"]

            for result in completed_runs
        ]),


        "Solving_Time": median([

            result["Solving_Time"]

            for result in completed_runs
        ]),


        "Total_Time": median([

            result["Total_Time"]

            for result in completed_runs
        ]),


        "Status": final_status
    }


    return summary, runs


# ============================================================
# In bảng kết quả median
# ============================================================

def print_benchmark_results(
    results
):

    print(
        "\nCP-SAT BENCHMARK "
        "- MEDIAN OF 5 RUNS"
    )


    print("=" * 80)


    print(

        f"{'N':<8}"

        f"{'Model(s)':<16}"

        f"{'Solve(s)':<16}"

        f"{'Total(s)':<16}"

        f"{'Status':<15}"
    )


    print("=" * 80)


    for result in results:

        print(

            f"{result['N']:<8}"

            f"{result['Model_Time']:<16.6f}"

            f"{result['Solving_Time']:<16.6f}"

            f"{result['Total_Time']:<16.6f}"

            f"{result['Status']:<15}"
        )


    print("=" * 80)


# ============================================================
# Lưu kết quả median
# ============================================================

def save_median_results(
    results
):

    filename = (
        "benchmark_cpsat_median.csv"
    )


    fieldnames = [

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
        "benchmark_cpsat_runs.csv"
    )


    fieldnames = [

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

    test_values = [

        2,
        3,
        4,
        8,
        20,
        50,
        100
    ]


    repeats = 5

    timeout_seconds = 30


    median_results = []

    raw_results = []


    # Chạy benchmark
    for n in test_values:

        summary, runs = (
            benchmark_cpsat_repeated(

                n,

                repeats=repeats,

                timeout_seconds=timeout_seconds
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