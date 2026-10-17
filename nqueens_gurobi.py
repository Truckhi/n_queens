# ============================================================
# N-QUEENS USING GUROBI MIP
# Benchmark: N = 2, 3, 4, 8, 20, 50, 100
# 5 runs / N, time limit 30s, 1 thread
# Kết quả benchmark được tổng hợp bằng median.
# ============================================================

import csv
import time
from statistics import median

import gurobipy as gp
from gurobipy import GRB


# ============================================================
# Cấu hình benchmark
# ============================================================

N_VALUES = [
    2,
    3,
    4,
    8,
    20,
    50,
    100,
]

RUNS = 5

TIME_LIMIT = 30

THREADS = 1


# ============================================================
# Kiểm tra nghiệm
# Đảm bảo không có hai hậu cùng hàng, cột hoặc đường chéo.
# ============================================================

def validate_solution(positions, n):

    if len(positions) != n:
        return False

    rows = set()
    cols = set()
    diag1 = set()
    diag2 = set()

    for row, col in positions:

        if row in rows:
            return False

        if col in cols:
            return False

        if row - col in diag1:
            return False

        if row + col in diag2:
            return False

        rows.add(row)
        cols.add(col)
        diag1.add(row - col)
        diag2.add(row + col)

    return True


# ============================================================
# Giải một bài toán N-Queens bằng Gurobi MIP
# ============================================================

def solve_nqueens_gurobi(n):

    model = None

    try:

        # Thời gian xây dựng mô hình
        model_start = time.perf_counter()

        model = gp.Model(
            f"NQueens_{n}"
        )

        model.Params.OutputFlag = 0

        model.Params.Threads = THREADS

        model.Params.TimeLimit = TIME_LIMIT

        model.Params.Seed = 0


        # Biến nhị phân
        # x[row, col] = 1 nếu đặt hậu tại vị trí (row, col).
        x = model.addVars(
            n,
            n,
            vtype=GRB.BINARY,
            name="x"
        )


        # Mỗi hàng có chính xác một hậu
        for row in range(n):

            model.addConstr(
                gp.quicksum(
                    x[row, col]
                    for col in range(n)
                ) == 1,
                name=f"row_{row}"
            )


        # Mỗi cột có chính xác một hậu
        for col in range(n):

            model.addConstr(
                gp.quicksum(
                    x[row, col]
                    for row in range(n)
                ) == 1,
                name=f"col_{col}"
            )


        # Đường chéo "\": row - col không đổi
        for d in range(
            -(n - 1),
            n
        ):

            diagonal = [
                x[row, col]
                for row in range(n)
                for col in range(n)
                if row - col == d
            ]

            if len(diagonal) > 1:

                model.addConstr(
                    gp.quicksum(
                        diagonal
                    ) <= 1,
                    name=f"diag_back_{d}"
                )


        # Đường chéo "/": row + col không đổi
        for s in range(
            2 * n - 1
        ):

            diagonal = [
                x[row, col]
                for row in range(n)
                for col in range(n)
                if row + col == s
            ]

            if len(diagonal) > 1:

                model.addConstr(
                    gp.quicksum(
                        diagonal
                    ) <= 1,
                    name=f"diag_slash_{s}"
                )


        # Bài toán feasibility nên không cần tối ưu hàm mục tiêu
        model.setObjective(
            0.0,
            GRB.MINIMIZE
        )

        model.update()

        variables = model.NumVars
        constraints = model.NumConstrs

        model_end = time.perf_counter()

        model_time = (
            model_end
            - model_start
        )


        # Thời gian giải
        solve_start = (
            time.perf_counter()
        )

        model.optimize()

        solve_end = (
            time.perf_counter()
        )

        solve_time = (
            solve_end
            - solve_start
        )


        # Xác định trạng thái nghiệm
        status_code = model.Status

        status = "UNKNOWN"

        valid = None


        if status_code == GRB.INFEASIBLE:

            status = "UNSAT"


        elif model.SolCount > 0:

            status = "SAT"

            positions = []

            for row in range(n):

                for col in range(n):

                    if x[row, col].X > 0.5:

                        positions.append(
                            (
                                row,
                                col
                            )
                        )

            valid = validate_solution(
                positions,
                n
            )


        elif status_code == GRB.TIME_LIMIT:

            status = "TIMEOUT"


        elif status_code == GRB.OPTIMAL:

            status = "SAT"


        else:

            status = (
                f"STATUS_{status_code}"
            )


        total_time = (
            model_time
            + solve_time
        )


        result = {
            "N":
                n,

            "Variables":
                variables,

            "Constraints":
                constraints,

            "Model_Time":
                model_time,

            "Solve_Time":
                solve_time,

            "Total_Time":
                total_time,

            "Status":
                status,

            "Valid":
                valid,
        }


        model.dispose()

        return result


    except gp.GurobiError as exc:

        if model is not None:

            try:
                model.dispose()

            except Exception:
                pass

        return {
            "N":
                n,

            "Variables":
                None,

            "Constraints":
                None,

            "Model_Time":
                None,

            "Solve_Time":
                None,

            "Total_Time":
                None,

            "Status":
                "ERROR",

            "Valid":
                None,

            "Message":
                f"GurobiError {exc.errno}: {exc}",
        }


    except Exception as exc:

        if model is not None:

            try:
                model.dispose()

            except Exception:
                pass

        return {
            "N":
                n,

            "Variables":
                None,

            "Constraints":
                None,

            "Model_Time":
                None,

            "Solve_Time":
                None,

            "Total_Time":
                None,

            "Status":
                "ERROR",

            "Valid":
                None,

            "Message":
                str(exc),
        }


# ============================================================
# Tính median, bỏ qua giá trị None
# ============================================================

def safe_median(values):

    clean_values = [
        value
        for value in values
        if value is not None
    ]

    if len(clean_values) == 0:
        return None

    return median(
        clean_values
    )


# ============================================================
# Benchmark
# Chạy mỗi N RUNS lần và lấy median.
# ============================================================

def benchmark_gurobi():

    raw_results = []

    median_results = []


    print()

    print(
        "=" * 100
    )

    print(
        "N-QUEENS GUROBI MIP BENCHMARK"
    )

    print(
        f"Runs per N: {RUNS}"
    )

    print(
        f"Time limit: {TIME_LIMIT}s"
    )

    print(
        f"Threads: {THREADS}"
    )

    print(
        "=" * 100
    )

    print()


    for n in N_VALUES:

        print(
            f"Running GUROBI MIP N={n}"
        )

        run_results = []


        for run in range(
            1,
            RUNS + 1
        ):

            print(
                f"    Run "
                f"{run}/{RUNS}",
                end="",
                flush=True
            )

            result = (
                solve_nqueens_gurobi(
                    n
                )
            )

            result[
                "Run"
            ] = run

            raw_results.append(
                result
            )

            run_results.append(
                result
            )


            if result["Status"] in [
                "SAT",
                "UNSAT",
            ]:

                print(
                    f" | "
                    f"{result['Status']} "
                    f"| Total = "
                    f"{result['Total_Time']:.6f}s"
                )


            elif result[
                "Status"
            ] == "TIMEOUT":

                print(
                    f" | TIMEOUT "
                    f"(>{TIME_LIMIT}s)"
                )


            else:

                print(
                    f" | "
                    f"{result['Status']}"
                )

                if "Message" in result:

                    print(
                        "       ",
                        result["Message"]
                    )


        # Lấy các lần chạy thành công
        successful_runs = [
            result
            for result in run_results
            if result["Status"]
            in [
                "SAT",
                "UNSAT",
            ]
        ]


        if len(
            successful_runs
        ) > 0:

            final_status = (
                successful_runs[0][
                    "Status"
                ]
            )

            median_result = {
                "N":
                    n,

                "Variables":
                    int(
                        median(
                            [
                                result[
                                    "Variables"
                                ]
                                for result
                                in successful_runs
                            ]
                        )
                    ),

                "Constraints":
                    int(
                        median(
                            [
                                result[
                                    "Constraints"
                                ]
                                for result
                                in successful_runs
                            ]
                        )
                    ),

                "Model_Time":
                    safe_median(
                        [
                            result[
                                "Model_Time"
                            ]
                            for result
                            in successful_runs
                        ]
                    ),

                "Solve_Time":
                    safe_median(
                        [
                            result[
                                "Solve_Time"
                            ]
                            for result
                            in successful_runs
                        ]
                    ),

                "Total_Time":
                    safe_median(
                        [
                            result[
                                "Total_Time"
                            ]
                            for result
                            in successful_runs
                        ]
                    ),

                "Status":
                    final_status,
            }


        elif any(
            result["Status"]
            == "TIMEOUT"
            for result
            in run_results
        ):

            median_result = {
                "N":
                    n,

                "Variables":
                    None,

                "Constraints":
                    None,

                "Model_Time":
                    None,

                "Solve_Time":
                    None,

                "Total_Time":
                    safe_median(
                        [
                            result[
                                "Total_Time"
                            ]
                            for result
                            in run_results
                            if result[
                                "Status"
                            ]
                            == "TIMEOUT"
                        ]
                    ),

                "Status":
                    "TIMEOUT",
            }


        else:

            median_result = {
                "N":
                    n,

                "Variables":
                    None,

                "Constraints":
                    None,

                "Model_Time":
                    None,

                "Solve_Time":
                    None,

                "Total_Time":
                    None,

                "Status":
                    "ERROR",
            }


        median_results.append(
            median_result
        )

        print()


    # ========================================================
    # Lưu kết quả từng lần chạy
    # ========================================================

    raw_file = (
        "benchmark_gurobi_runs.csv"
    )

    raw_fields = [
        "N",
        "Run",
        "Variables",
        "Constraints",
        "Model_Time",
        "Solve_Time",
        "Total_Time",
        "Status",
        "Valid",
        "Message",
    ]

    with open(
        raw_file,
        "w",
        newline="",
        encoding="utf-8"
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=raw_fields,
            extrasaction="ignore"
        )

        writer.writeheader()

        writer.writerows(
            raw_results
        )


    # ========================================================
    # Lưu kết quả median
    # ========================================================

    median_file = (
        "benchmark_gurobi_median.csv"
    )

    median_fields = [
        "N",
        "Variables",
        "Constraints",
        "Model_Time",
        "Solve_Time",
        "Total_Time",
        "Status",
    ]

    with open(
        median_file,
        "w",
        newline="",
        encoding="utf-8"
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=median_fields
        )

        writer.writeheader()

        writer.writerows(
            median_results
        )


    # ========================================================
    # In bảng kết quả
    # ========================================================

    print()

    print(
        "=" * 110
    )

    print(
        "GUROBI MIP BENCHMARK "
        "- MEDIAN OF 5 RUNS"
    )

    print(
        "=" * 110
    )

    print(
        f"{'N':<8}"
        f"{'Variables':<14}"
        f"{'Constraints':<16}"
        f"{'Model(s)':<16}"
        f"{'Solve(s)':<16}"
        f"{'Total(s)':<16}"
        f"{'Status':<14}"
    )

    print(
        "=" * 110
    )


    def fmt_time(value):

        if value is None:
            return "-"

        return (
            f"{value:.6f}"
        )


    for result in median_results:

        variables = (
            "-"
            if result[
                "Variables"
            ] is None
            else str(
                result[
                    "Variables"
                ]
            )
        )

        constraints = (
            "-"
            if result[
                "Constraints"
            ] is None
            else str(
                result[
                    "Constraints"
                ]
            )
        )


        print(
            f"{result['N']:<8}"
            f"{variables:<14}"
            f"{constraints:<16}"
            f"{fmt_time(result['Model_Time']):<16}"
            f"{fmt_time(result['Solve_Time']):<16}"
            f"{fmt_time(result['Total_Time']):<16}"
            f"{result['Status']:<14}"
        )


    print(
        "=" * 110
    )

    print()

    print(
        "Da luu median vao:",
        median_file
    )

    print(
        "Da luu raw runs vao:",
        raw_file
    )

    print()


# ============================================================
# Main
# ============================================================

if __name__ == "__main__":

    benchmark_gurobi()