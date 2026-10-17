# ============================================================
# N-QUEENS USING CPLEX MIP
# Benchmark: N = 2, 3, 4, 8, 20, 50, 100
# 5 runs / N, time limit 30s, 1 thread
# Kết quả benchmark được tổng hợp bằng median.
# ============================================================

from docplex.mp.model import Model

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

THREADS = 1


# ============================================================
# Tạo mô hình N-Queens bằng CPLEX MIP
# ============================================================

def build_nqueens_cplex_mip(n):

    model = Model(
        name=f"nqueens_{n}"
    )


    # Biến nhị phân
    # x[row, col] = 1 nếu đặt hậu tại ô (row, col).
    x = model.binary_var_matrix(
        range(n),
        range(n),
        name="x"
    )


    # Mỗi hàng có chính xác một hậu
    for row in range(n):

        model.add_constraint(

            model.sum(
                x[row, col]
                for col in range(n)
            )

            == 1
        )


    # Mỗi cột có chính xác một hậu
    for col in range(n):

        model.add_constraint(

            model.sum(
                x[row, col]
                for row in range(n)
            )

            == 1
        )


    # Nhóm các ô theo hai hướng đường chéo
    diagonal_backslash = {}

    diagonal_slash = {}


    for row in range(n):

        for col in range(n):

            # Đường chéo "\": row - col
            key1 = row - col

            if key1 not in diagonal_backslash:
                diagonal_backslash[key1] = []

            diagonal_backslash[key1].append(
                x[row, col]
            )


            # Đường chéo "/": row + col
            key2 = row + col

            if key2 not in diagonal_slash:
                diagonal_slash[key2] = []

            diagonal_slash[key2].append(
                x[row, col]
            )


    # Mỗi đường chéo "\" có tối đa một hậu
    for group in diagonal_backslash.values():

        if len(group) > 1:

            model.add_constraint(
                model.sum(group) <= 1
            )


    # Mỗi đường chéo "/" có tối đa một hậu
    for group in diagonal_slash.values():

        if len(group) > 1:

            model.add_constraint(
                model.sum(group) <= 1
            )


    return model, x


# ============================================================
# Giải một bài toán N-Queens
# Hàm dùng để kiểm tra nghiệm trực tiếp.
# ============================================================

def solve_nqueens_cplex_mip(
    n,
    timeout_seconds=TIMEOUT_SECONDS
):

    model, x = (
        build_nqueens_cplex_mip(n)
    )


    model.parameters.threads = (
        THREADS
    )


    model.parameters.timelimit = (
        timeout_seconds
    )


    start = time.perf_counter()


    solution = model.solve(
        log_output=False
    )


    end = time.perf_counter()


    solve_time = (
        end - start
    )


    # Trạng thái kết quả
    if solution is not None:

        print(
            "Ket qua: SAT"
        )

        print(
            "\nVi tri cac quan hau:"
        )


        for row in range(n):

            for col in range(n):

                if (
                    solution.get_value(
                        x[row, col]
                    )
                    > 0.5
                ):

                    print(
                        f"Hang {row}: "
                        f"cot {col}"
                    )


    else:

        status = str(
            model.solve_details.status
        ).lower()


        if "infeasible" in status:

            print(
                "Ket qua: UNSAT"
            )


        elif (
            "time" in status
            or
            "limit" in status
        ):

            print(
                "Ket qua: TIMEOUT"
            )


        else:

            print(
                "Ket qua: ERROR"
            )

            print(
                "Solver status:",
                model.solve_details.status
            )


    print(
        "Thoi gian solve =",
        solve_time
    )


    model.end()


# ============================================================
# Benchmark CPLEX MIP một lần
# Đo thời gian tạo mô hình và thời gian giải.
# ============================================================

def benchmark_cplex_mip_once(
    n,
    timeout_seconds=TIMEOUT_SECONDS
):

    # Model time
    model_start = (
        time.perf_counter()
    )


    model, x = (
        build_nqueens_cplex_mip(n)
    )


    model_end = (
        time.perf_counter()
    )


    model_time = (
        model_end
        - model_start
    )


    # Thống kê mô hình
    number_variables = (
        model.number_of_variables
    )


    number_constraints = (
        model.number_of_constraints
    )


    # Cấu hình solver
    model.parameters.threads = (
        THREADS
    )


    model.parameters.timelimit = (
        timeout_seconds
    )


    # Solve time
    solve_start = (
        time.perf_counter()
    )


    try:

        solution = model.solve(
            log_output=False
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
        if solution is not None:

            result_status = (
                "SAT"
            )

            message = ""


        else:

            status_text = str(
                model.solve_details.status
            ).lower()


            if (
                "infeasible"
                in status_text
            ):

                result_status = (
                    "UNSAT"
                )


            elif (
                "time"
                in status_text

                or

                "limit"
                in status_text
            ):

                result_status = (
                    "TIMEOUT"
                )


            else:

                result_status = (
                    "ERROR"
                )


            message = str(
                model.solve_details.status
            )


    except Exception as error:

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


        result_status = (
            "ERROR"
        )


        message = str(
            error
        )


    result = {

        "Solver":
            "CPLEX MIP",

        "N":
            n,

        "Variables":
            number_variables,

        "Constraints":
            number_constraints,

        "Model_Time":
            model_time,

        "Solving_Time":
            solve_time,

        "Total_Time":
            total_time,

        "Status":
            result_status,

        "Message":
            message
    }


    model.end()


    return result


# ============================================================
# Chạy mỗi N nhiều lần và lấy median
# ============================================================

def benchmark_cplex_mip_repeated(
    n,
    repeats=REPEATS,
    timeout_seconds=TIMEOUT_SECONDS
):

    runs = []


    print(
        f"\nRunning CPLEX MIP N={n}"
    )


    for run_id in range(
        1,
        repeats + 1
    ):

        print(
            f"    Run "
            f"{run_id}/{repeats}"
        )


        result = (
            benchmark_cplex_mip_once(
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


        if (
            result["Status"]
            == "ERROR"
        ):

            print(
                "        ERROR:",
                result["Message"]
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


    # Các lần timeout
    timeout_runs = [

        result

        for result in runs

        if result["Status"]
        == "TIMEOUT"
    ]


    if (
        len(timeout_runs)
        == repeats
    ):

        summary = {

            "Solver":
                "CPLEX MIP",

            "N":
                n,

            "Variables":
                runs[0][
                    "Variables"
                ],

            "Constraints":
                runs[0][
                    "Constraints"
                ],

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
                "TIMEOUT",

            "Message":
                ""
        }


        return (
            summary,
            runs
        )


    # Các lần lỗi
    error_runs = [

        result

        for result in runs

        if result[
            "Status"
        ] == "ERROR"
    ]


    if (
        len(error_runs)
        == repeats
    ):

        summary = {

            "Solver":
                "CPLEX MIP",

            "N":
                n,

            "Variables":
                runs[0][
                    "Variables"
                ],

            "Constraints":
                runs[0][
                    "Constraints"
                ],

            "Model_Time":
                None,

            "Solving_Time":
                None,

            "Total_Time":
                None,

            "Status":
                "ERROR",

            "Message":
                error_runs[0][
                    "Message"
                ]
        }


        return (
            summary,
            runs
        )


    # Trường hợp không có lần chạy hoàn thành
    if (
        len(completed_runs)
        == 0
    ):

        summary = {

            "Solver":
                "CPLEX MIP",

            "N":
                n,

            "Variables":
                runs[0][
                    "Variables"
                ],

            "Constraints":
                runs[0][
                    "Constraints"
                ],

            "Model_Time":
                None,

            "Solving_Time":
                None,

            "Total_Time":
                None,

            "Status":
                "ERROR",

            "Message":
                "No completed runs."
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
            "CPLEX MIP",

        "N":
            n,

        "Variables":
            completed_runs[0][
                "Variables"
            ],

        "Constraints":
            completed_runs[0][
                "Constraints"
            ],

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
            final_status,

        "Message":
            ""
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
        "CPLEX MIP BENCHMARK "
        "- MEDIAN OF 5 RUNS"
    )


    print(
        "=" * 105
    )


    print(

        f"{'N':<8}"

        f"{'Variables':<14}"

        f"{'Constraints':<16}"

        f"{'Model(s)':<16}"

        f"{'Solve(s)':<16}"

        f"{'Total(s)':<16}"

        f"{'Status':<15}"
    )


    print(
        "=" * 105
    )


    for result in results:

        print(

            f"{result['N']:<8}"

            f"{result['Variables']:<14}"

            f"{result['Constraints']:<16}"

            f"{format_time(result['Model_Time']):<16}"

            f"{format_time(result['Solving_Time']):<16}"

            f"{format_time(result['Total_Time']):<16}"

            f"{result['Status']:<15}"
        )


    print(
        "=" * 105
    )


# ============================================================
# Lưu kết quả median
# ============================================================

def save_median_results(
    results
):

    filename = (
        "benchmark_cplex_mip_median.csv"
    )


    fieldnames = [

        "Solver",

        "N",

        "Variables",

        "Constraints",

        "Model_Time",

        "Solving_Time",

        "Total_Time",

        "Status",

        "Message"
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
        "benchmark_cplex_mip_runs.csv"
    )


    fieldnames = [

        "Solver",

        "N",

        "Run",

        "Variables",

        "Constraints",

        "Model_Time",

        "Solving_Time",

        "Total_Time",

        "Status",

        "Message"
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
        "=" * 90
    )


    print(
        "N-QUEENS CPLEX MIP BENCHMARK"
    )


    print(
        f"Runs per N: {REPEATS}"
    )


    print(
        f"Time limit: "
        f"{TIMEOUT_SECONDS}s"
    )


    print(
        f"Threads: {THREADS}"
    )


    print(
        "=" * 90
    )


    median_results = []

    raw_results = []


    # Chạy benchmark
    for n in TEST_VALUES:

        summary, runs = (
            benchmark_cplex_mip_repeated(

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