from ortools.sat.python import cp_model

import time
import csv
from statistics import median


# =========================================================
# 1. TẠO MODEL N-QUEENS CHO CP-SAT
# =========================================================

def build_nqueens_model(n):

    model = cp_model.CpModel()

    # -----------------------------------------------------
    # queens[row] = cột đặt quân hậu ở hàng row
    #
    # Ví dụ:
    # queens = [1, 3, 0, 2]
    #
    # Hàng 0 -> cột 1
    # Hàng 1 -> cột 3
    # Hàng 2 -> cột 0
    # Hàng 3 -> cột 2
    # -----------------------------------------------------

    queens = [
        model.NewIntVar(
            0,
            n - 1,
            f"q_{row}"
        )
        for row in range(n)
    ]


    # =====================================================
    # RÀNG BUỘC 1:
    # Không có 2 quân hậu cùng cột
    # =====================================================

    model.AddAllDifferent(queens)


    # =====================================================
    # RÀNG BUỘC 2:
    # Không có 2 quân hậu cùng đường chéo "\"
    #
    # Các hậu cùng đường chéo "\" có:
    # column - row giống nhau
    # =====================================================

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


    # =====================================================
    # RÀNG BUỘC 3:
    # Không có 2 quân hậu cùng đường chéo "/"
    #
    # Các hậu cùng đường chéo "/" có:
    # column + row giống nhau
    # =====================================================

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


# =========================================================
# 2. GIẢI N-QUEENS VÀ IN NGHIỆM
#
# Hàm này chỉ dùng khi muốn kiểm tra trực quan.
# Không dùng cho benchmark chính thức.
# =========================================================

def solve_nqueens_cpsat(
    n,
    timeout_seconds=10
):

    model, queens = build_nqueens_model(n)


    solver = cp_model.CpSolver()


    # -----------------------------------------------------
    # Giới hạn thời gian
    # -----------------------------------------------------

    solver.parameters.max_time_in_seconds = (
        timeout_seconds
    )


    # -----------------------------------------------------
    # Chỉ sử dụng 1 worker
    #
    # Giúp benchmark với SAT công bằng hơn
    # -----------------------------------------------------

    solver.parameters.num_search_workers = 1


    # -----------------------------------------------------
    # Cố định seed để kết quả ổn định hơn
    # -----------------------------------------------------

    solver.parameters.random_seed = 0


    start = time.perf_counter()

    status = solver.Solve(model)

    end = time.perf_counter()


    solve_time = end - start


    # =====================================================
    # KẾT QUẢ
    # =====================================================

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


# =========================================================
# 3. BENCHMARK CP-SAT MỘT LẦN
# =========================================================

def benchmark_cpsat_once(
    n,
    timeout_seconds=10
):

    # =====================================================
    # MODEL TIME
    # =====================================================

    model_start = time.perf_counter()


    model, queens = build_nqueens_model(n)


    model_end = time.perf_counter()


    model_time = (
        model_end
        - model_start
    )


    # =====================================================
    # TẠO SOLVER
    # =====================================================

    solver = cp_model.CpSolver()


    solver.parameters.max_time_in_seconds = (
        timeout_seconds
    )


    # Dùng 1 CPU worker để benchmark công bằng hơn
    solver.parameters.num_search_workers = 1


    # Cố định seed
    solver.parameters.random_seed = 0


    # =====================================================
    # SOLVE TIME
    # =====================================================

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


    # =====================================================
    # XÁC ĐỊNH TRẠNG THÁI
    # =====================================================

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


# =========================================================
# 4. CHẠY MỘT N NHIỀU LẦN VÀ LẤY MEDIAN
# =========================================================

def benchmark_cpsat_repeated(
    n,
    repeats=5,
    timeout_seconds=10
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


        # Ghi thêm số thứ tự lần chạy
        result["Run"] = run_id


        runs.append(
            result
        )


    # =====================================================
    # CHỈ LẤY CÁC LẦN HOÀN THÀNH
    # =====================================================

    completed_runs = [

        result

        for result in runs

        if result["Status"]
        in ("SAT", "UNSAT")
    ]


    # =====================================================
    # NẾU CẢ 5 LẦN ĐỀU TIMEOUT
    # =====================================================

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


    # =====================================================
    # TRẠNG THÁI
    # =====================================================

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


    # =====================================================
    # MEDIAN
    # =====================================================

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


# =========================================================
# 5. IN BẢNG MEDIAN
# =========================================================

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


# =========================================================
# 6. LƯU KẾT QUẢ MEDIAN
# =========================================================

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


# =========================================================
# 7. LƯU TẤT CẢ CÁC LẦN CHẠY
# =========================================================

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


# =========================================================
# 8. MAIN
# =========================================================

if __name__ == "__main__":

    # Các kích thước cần test
    test_values = [

        2,
        3,
        4,
        8,
        20,
        50,
        100
    ]


    # Mỗi N chạy 5 lần
    repeats = 5


    # Mỗi lần tối đa 30 giây
    timeout_seconds = 30


    # Kết quả median
    median_results = []


    # Kết quả toàn bộ từng lần chạy
    raw_results = []


    # =====================================================
    # CHẠY BENCHMARK
    # =====================================================

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


    # =====================================================
    # IN BẢNG MEDIAN
    # =====================================================

    print_benchmark_results(
        median_results
    )


    # =====================================================
    # LƯU CSV
    # =====================================================

    save_median_results(
        median_results
    )


    save_raw_results(
        raw_results
    )