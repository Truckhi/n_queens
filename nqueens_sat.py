# ============================================================
# N-QUEENS USING SAT
# Compare 5 AMO encodings:
#
#   1. Pairwise
#   2. Sequential Counter
#   3. Binary
#   4. Commander
#   5. Product
#
# SAT Solver: Glucose3 (PySAT)
#
# Benchmark:
#   N = 2, 3, 4, 8, 20, 50, 100
#   5 runs / configuration
#   Hard timeout = 10 seconds / run
#   Report median time
#
# Output:
#   benchmark_results_median.csv
#   benchmark_sat_runs.csv
# ============================================================


import csv
import math
import time
import multiprocessing as mp

from statistics import median

from pysat.formula import CNF
from pysat.solvers import Glucose3
from pysat.card import CardEnc, EncType


# ============================================================
# CẤU HÌNH BENCHMARK
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

ENCODINGS = [
    "Pairwise",
    "Sequential",
    "Binary",
    "Commander",
    "Product",
]

RUNS = 5

TIMEOUT_SECONDS = 30


# ============================================================
# BIẾN x[row, col]
#
# Mỗi ô trên bàn cờ tương ứng với một biến Boolean.
#
# x[row, col] = True
#   <=> có quân hậu tại vị trí (row, col)
#
# ID biến:
#   1 ... N^2
# ============================================================

def var_id(row, col, n):

    return (
        row * n
        + col
        + 1
    )


# ============================================================
# QUẢN LÝ BIẾN PHỤ
#
# Các encoding như Sequential, Binary, Commander, Product
# cần auxiliary variables.
#
# Biến gốc:
#       1 ... N^2
#
# Biến phụ:
#       N^2 + 1 ...
# ============================================================

class AuxVarManager:

    def __init__(self, first_aux_var):

        self.next_var = first_aux_var


    def new_var(self):

        var = self.next_var

        self.next_var += 1

        return var


    @property
    def top_id(self):

        return self.next_var - 1


    def sync(self, max_var):

        if max_var >= self.next_var:

            self.next_var = (
                max_var + 1
            )


# ============================================================
# 1. PAIRWISE ENCODING
#
# AMO(x1, x2, ..., xn)
#
# Với mọi cặp (xi, xj):
#
#       ¬xi OR ¬xj
#
# Nếu có n biến:
#
#       C(n, 2)
#
# clauses.
# ============================================================

def add_amo_pairwise(
    cnf,
    lits,
    var_manager
):

    m = len(lits)

    if m <= 1:
        return

    for i in range(m):

        for j in range(
            i + 1,
            m
        ):

            cnf.append(
                [
                    -lits[i],
                    -lits[j],
                ]
            )


# ============================================================
# 2. SEQUENTIAL COUNTER ENCODING
#
# Dùng encoding có sẵn của PySAT.
#
# bound = 1
# => At Most One
#
# Sequential Counter sử dụng auxiliary variables.
# ============================================================

def add_amo_sequential(
    cnf,
    lits,
    var_manager
):

    if len(lits) <= 1:
        return

    encoding = CardEnc.atmost(
        lits=lits,
        bound=1,
        top_id=var_manager.top_id,
        encoding=EncType.seqcounter,
    )

    cnf.extend(
        encoding.clauses
    )

    # Đồng bộ ID biến phụ mà PySAT vừa sinh
    var_manager.sync(
        encoding.nv
    )


# ============================================================
# 3. BINARY ENCODING
#
# Ý tưởng:
#
# Với m biến:
#
#       x1, x2, ..., xm
#
# tạo:
#
#       ceil(log2(m))
#
# auxiliary variables làm các bit nhị phân.
#
# Mỗi xi được gán một mã binary duy nhất.
#
# Nếu xi = True
# => các bit phụ phải nhận đúng mã của xi.
#
# Hai xi khác nhau có mã khác nhau
# => không thể cùng True.
# ============================================================

def add_amo_binary(
    cnf,
    lits,
    var_manager
):

    m = len(lits)

    if m <= 1:
        return

    num_bits = math.ceil(
        math.log2(m)
    )

    bit_vars = []

    for _ in range(num_bits):

        bit_vars.append(
            var_manager.new_var()
        )

    for index, x in enumerate(lits):

        for bit in range(num_bits):

            bit_value = (
                index >> bit
            ) & 1

            if bit_value == 1:

                # x -> bit
                #
                # ¬x OR bit
                cnf.append(
                    [
                        -x,
                        bit_vars[bit],
                    ]
                )

            else:

                # x -> ¬bit
                #
                # ¬x OR ¬bit
                cnf.append(
                    [
                        -x,
                        -bit_vars[bit],
                    ]
                )


# ============================================================
# 4. COMMANDER ENCODING
#
# Chia các biến thành các nhóm nhỏ.
#
# Ví dụ:
#
#   x1 x2 x3  -> commander c1
#   x4 x5 x6  -> commander c2
#
# Trong mỗi nhóm:
#   dùng Pairwise AMO
#
# Nếu xi True:
#   commander của nhóm phải True
#
# Sau đó:
#   các commander cũng phải AMO.
#
# group_size = 3
# ============================================================

def add_amo_commander(
    cnf,
    lits,
    var_manager,
    group_size=3
):

    m = len(lits)

    if m <= 1:
        return

    # Nhóm nhỏ thì Pairwise trực tiếp
    if m <= group_size:

        add_amo_pairwise(
            cnf,
            lits,
            var_manager
        )

        return

    commanders = []

    for start in range(
        0,
        m,
        group_size
    ):

        group = lits[
            start:
            start + group_size
        ]

        # Nếu nhóm chỉ còn 1 biến
        # thì dùng luôn biến đó
        if len(group) == 1:

            commanders.append(
                group[0]
            )

            continue

        # AMO bên trong nhóm
        add_amo_pairwise(
            cnf,
            group,
            var_manager
        )

        # Tạo commander
        commander = (
            var_manager.new_var()
        )

        commanders.append(
            commander
        )

        # xi -> commander
        for x in group:

            cnf.append(
                [
                    -x,
                    commander,
                ]
            )

    # Các commander cũng phải AMO
    add_amo_commander(
        cnf,
        commanders,
        var_manager,
        group_size
    )


# ============================================================
# 5. PRODUCT ENCODING
#
# 2-Product Encoding.
#
# Ánh xạ m biến vào một ma trận gần vuông.
#
# Ví dụ:
#
#           col1 col2 col3
#
# row1       x1   x2   x3
# row2       x4   x5   x6
# row3       x7   x8   x9
#
# Nếu xij True:
#
#       row_i True
#       col_j True
#
# Đồng thời:
#
#       AMO(row variables)
#       AMO(column variables)
#
# => tối đa một x có thể True.
# ============================================================

def add_amo_product(
    cnf,
    lits,
    var_manager
):

    m = len(lits)

    if m <= 1:
        return

    # Trường hợp rất nhỏ
    # Pairwise đơn giản hơn
    if m <= 3:

        add_amo_pairwise(
            cnf,
            lits,
            var_manager
        )

        return

    # Kích thước ma trận gần vuông
    p = math.ceil(
        math.sqrt(m)
    )

    q = math.ceil(
        m / p
    )

    row_vars = []

    col_vars = []

    for _ in range(p):

        row_vars.append(
            var_manager.new_var()
        )

    for _ in range(q):

        col_vars.append(
            var_manager.new_var()
        )

    for index, x in enumerate(lits):

        row = (
            index // q
        )

        col = (
            index % q
        )

        # x -> row
        cnf.append(
            [
                -x,
                row_vars[row],
            ]
        )

        # x -> column
        cnf.append(
            [
                -x,
                col_vars[col],
            ]
        )

    # AMO trên row variables
    add_amo_pairwise(
        cnf,
        row_vars,
        var_manager
    )

    # AMO trên column variables
    add_amo_pairwise(
        cnf,
        col_vars,
        var_manager
    )


# ============================================================
# HÀM CHỌN ENCODING
#
# Mọi AMO constraint của N-Queens
# đều đi qua hàm này.
# ============================================================

def add_amo(
    cnf,
    lits,
    encoding_name,
    var_manager
):

    if encoding_name == "Pairwise":

        add_amo_pairwise(
            cnf,
            lits,
            var_manager
        )

    elif encoding_name == "Sequential":

        add_amo_sequential(
            cnf,
            lits,
            var_manager
        )

    elif encoding_name == "Binary":

        add_amo_binary(
            cnf,
            lits,
            var_manager
        )

    elif encoding_name == "Commander":

        add_amo_commander(
            cnf,
            lits,
            var_manager
        )

    elif encoding_name == "Product":

        add_amo_product(
            cnf,
            lits,
            var_manager
        )

    else:

        raise ValueError(
            f"Unknown encoding: "
            f"{encoding_name}"
        )


# ============================================================
# TẠO CNF CHO N-QUEENS
# ============================================================

def build_nqueens_cnf(
    n,
    encoding_name
):

    cnf = CNF()

    # Biến gốc:
    #
    #   1 ... n^2
    #
    # Biến phụ bắt đầu:
    #
    #   n^2 + 1
    var_manager = AuxVarManager(
        first_aux_var=(
            n * n + 1
        )
    )


    # ========================================================
    # RÀNG BUỘC 1:
    # MỖI HÀNG CÓ CHÍNH XÁC 1 HẬU
    #
    # Exactly One
    #
    # =
    #
    # At Least One
    # +
    # At Most One
    # ========================================================

    for row in range(n):

        row_vars = []

        for col in range(n):

            row_vars.append(
                var_id(
                    row,
                    col,
                    n
                )
            )

        # At Least One
        cnf.append(
            row_vars
        )

        # At Most One
        add_amo(
            cnf,
            row_vars,
            encoding_name,
            var_manager
        )


    # ========================================================
    # RÀNG BUỘC 2:
    # MỖI CỘT CÓ CHÍNH XÁC 1 HẬU
    # ========================================================

    for col in range(n):

        col_vars = []

        for row in range(n):

            col_vars.append(
                var_id(
                    row,
                    col,
                    n
                )
            )

        # At Least One
        cnf.append(
            col_vars
        )

        # At Most One
        add_amo(
            cnf,
            col_vars,
            encoding_name,
            var_manager
        )


    # ========================================================
    # RÀNG BUỘC 3:
    # KHÔNG CÓ 2 HẬU TRÊN CÙNG ĐƯỜNG CHÉO "\"
    #
    # Các ô cùng đường chéo có:
    #
    #       row - col = constant
    # ========================================================

    diagonal_backslash = {}

    for row in range(n):

        for col in range(n):

            key = (
                row - col
            )

            if key not in diagonal_backslash:

                diagonal_backslash[key] = []

            diagonal_backslash[key].append(
                var_id(
                    row,
                    col,
                    n
                )
            )

    for diagonal in diagonal_backslash.values():

        if len(diagonal) > 1:

            add_amo(
                cnf,
                diagonal,
                encoding_name,
                var_manager
            )


    # ========================================================
    # RÀNG BUỘC 4:
    # KHÔNG CÓ 2 HẬU TRÊN CÙNG ĐƯỜNG CHÉO "/"
    #
    # Các ô cùng đường chéo có:
    #
    #       row + col = constant
    # ========================================================

    diagonal_slash = {}

    for row in range(n):

        for col in range(n):

            key = (
                row + col
            )

            if key not in diagonal_slash:

                diagonal_slash[key] = []

            diagonal_slash[key].append(
                var_id(
                    row,
                    col,
                    n
                )
            )

    for diagonal in diagonal_slash.values():

        if len(diagonal) > 1:

            add_amo(
                cnf,
                diagonal,
                encoding_name,
                var_manager
            )


    return cnf


# ============================================================
# WORKER
#
# Chạy trong process riêng.
#
# Mục đích:
# nếu SAT solver chạy quá TIMEOUT_SECONDS,
# process cha có thể terminate process này.
#
# Như vậy đây là HARD TIMEOUT.
# ============================================================

def sat_worker(
    n,
    encoding_name,
    result_queue
):

    try:

        # ====================================================
        # 1. ENCODING TIME
        # ====================================================

        encode_start = (
            time.perf_counter()
        )

        cnf = build_nqueens_cnf(
            n,
            encoding_name
        )

        encode_end = (
            time.perf_counter()
        )

        encode_time = (
            encode_end
            - encode_start
        )


        # ====================================================
        # SỐ BIẾN + SỐ CLAUSE
        # ====================================================

        variables = cnf.nv

        clauses = len(
            cnf.clauses
        )


        # ====================================================
        # 2. LOAD CNF VÀO GLUCOSE3
        # ====================================================

        load_start = (
            time.perf_counter()
        )

        solver = Glucose3(
            bootstrap_with=cnf.clauses
        )

        load_end = (
            time.perf_counter()
        )

        load_time = (
            load_end
            - load_start
        )


        # ====================================================
        # 3. SOLVE TIME
        # ====================================================

        solve_start = (
            time.perf_counter()
        )

        sat = solver.solve()

        solve_end = (
            time.perf_counter()
        )

        solve_time = (
            solve_end
            - solve_start
        )


        # ====================================================
        # STATUS
        # ====================================================

        if sat:

            status = "SAT"

        else:

            status = "UNSAT"


        solver.delete()


        # ====================================================
        # TOTAL TIME
        #
        # Total =
        #   Encode
        # + Load
        # + Solve
        # ====================================================

        total_time = (
            encode_time
            + load_time
            + solve_time
        )


        result_queue.put(
            {
                "N": n,

                "Encoding":
                    encoding_name,

                "Variables":
                    variables,

                "Clauses":
                    clauses,

                "Encode_Time":
                    encode_time,

                "Load_Time":
                    load_time,

                "Solve_Time":
                    solve_time,

                "Total_Time":
                    total_time,

                "Status":
                    status,
            }
        )


    except Exception as exc:

        result_queue.put(
            {
                "N": n,

                "Encoding":
                    encoding_name,

                "Variables":
                    None,

                "Clauses":
                    None,

                "Encode_Time":
                    None,

                "Load_Time":
                    None,

                "Solve_Time":
                    None,

                "Total_Time":
                    None,

                "Status":
                    "ERROR",

                "Message":
                    str(exc),
            }
        )


# ============================================================
# CHẠY 1 LẦN VỚI HARD TIMEOUT
# ============================================================

def run_once_with_timeout(
    n,
    encoding_name,
    timeout_seconds
):

    # Windows nên dùng spawn
    ctx = mp.get_context(
        "spawn"
    )

    result_queue = (
        ctx.Queue()
    )

    process = ctx.Process(
        target=sat_worker,
        args=(
            n,
            encoding_name,
            result_queue,
        )
    )

    wall_start = (
        time.perf_counter()
    )

    process.start()

    process.join(
        timeout_seconds
    )


    # ========================================================
    # TIMEOUT
    # ========================================================

    if process.is_alive():

        process.terminate()

        process.join()

        wall_end = (
            time.perf_counter()
        )

        return {
            "N":
                n,

            "Encoding":
                encoding_name,

            "Variables":
                None,

            "Clauses":
                None,

            "Encode_Time":
                None,

            "Load_Time":
                None,

            "Solve_Time":
                None,

            "Total_Time":
                wall_end
                - wall_start,

            "Status":
                "TIMEOUT",
        }


    # ========================================================
    # PROCESS KẾT THÚC BÌNH THƯỜNG
    # ========================================================

    if not result_queue.empty():

        return (
            result_queue.get()
        )


    # Nếu process chết nhưng không gửi kết quả
    return {
        "N":
            n,

        "Encoding":
            encoding_name,

        "Variables":
            None,

        "Clauses":
            None,

        "Encode_Time":
            None,

        "Load_Time":
            None,

        "Solve_Time":
            None,

        "Total_Time":
            None,

        "Status":
            "ERROR",
    }


# ============================================================
# HÀM MEDIAN AN TOÀN
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
# BENCHMARK TOÀN BỘ
# ============================================================

def benchmark_nqueens():

    raw_results = []

    median_results = []


    print()

    print(
        "=" * 90
    )

    print(
        "N-QUEENS SAT BENCHMARK"
    )

    print(
        "Solver: Glucose3"
    )

    print(
        "Encodings:"
    )

    for encoding in ENCODINGS:

        print(
            f"  - {encoding}"
        )

    print(
        f"Runs per case: {RUNS}"
    )

    print(
        f"Hard timeout: "
        f"{TIMEOUT_SECONDS}s"
    )

    print(
        "=" * 90
    )

    print()


    # ========================================================
    # CHẠY TỪNG ENCODING
    # ========================================================

    for encoding_name in ENCODINGS:

        print()

        print(
            "#" * 90
        )

        print(
            f"ENCODING: "
            f"{encoding_name}"
        )

        print(
            "#" * 90
        )

        print()


        for n in N_VALUES:

            run_results = []

            print(
                f"N = {n}"
            )


            # =================================================
            # 5 RUNS
            # =================================================

            for run in range(
                1,
                RUNS + 1
            ):

                print(
                    f"  Run "
                    f"{run}/{RUNS}...",
                    end=" ",
                    flush=True
                )

                result = (
                    run_once_with_timeout(
                        n,
                        encoding_name,
                        TIMEOUT_SECONDS
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


                status = (
                    result["Status"]
                )


                if status in [
                    "SAT",
                    "UNSAT",
                ]:

                    print(
                        f"{status} | "
                        f"Total = "
                        f"{result['Total_Time']:.6f}s"
                    )

                elif status == "TIMEOUT":

                    print(
                        f"TIMEOUT "
                        f"(>{TIMEOUT_SECONDS}s)"
                    )

                else:

                    print(
                        "ERROR"
                    )


            # =================================================
            # TÍNH MEDIAN
            # =================================================

            successful_runs = [
                r
                for r in run_results
                if r["Status"]
                in [
                    "SAT",
                    "UNSAT",
                ]
            ]


            # Nếu không có lần nào solve thành công
            if len(successful_runs) == 0:

                # Nếu có ít nhất một timeout
                if any(
                    r["Status"]
                    == "TIMEOUT"
                    for r in run_results
                ):

                    final_status = (
                        "TIMEOUT"
                    )

                    # Dùng median elapsed timeout
                    total_time = (
                        safe_median(
                            [
                                r[
                                    "Total_Time"
                                ]
                                for r
                                in run_results
                                if r[
                                    "Status"
                                ]
                                == "TIMEOUT"
                            ]
                        )
                    )

                else:

                    final_status = (
                        "ERROR"
                    )

                    total_time = None


                median_result = {
                    "N":
                        n,

                    "Encoding":
                        encoding_name,

                    "Variables":
                        None,

                    "Clauses":
                        None,

                    "Encode_Time":
                        None,

                    "Load_Time":
                        None,

                    "Solve_Time":
                        None,

                    "Total_Time":
                        total_time,

                    "Status":
                        final_status,
                }


            else:

                status_values = [
                    r["Status"]
                    for r
                    in successful_runs
                ]

                # Các run bình thường phải cùng kết quả.
                # Lấy status của run đầu tiên.
                final_status = (
                    status_values[0]
                )


                median_result = {
                    "N":
                        n,

                    "Encoding":
                        encoding_name,

                    "Variables":
                        int(
                            median(
                                [
                                    r[
                                        "Variables"
                                    ]
                                    for r
                                    in successful_runs
                                ]
                            )
                        ),

                    "Clauses":
                        int(
                            median(
                                [
                                    r[
                                        "Clauses"
                                    ]
                                    for r
                                    in successful_runs
                                ]
                            )
                        ),

                    "Encode_Time":
                        safe_median(
                            [
                                r[
                                    "Encode_Time"
                                ]
                                for r
                                in successful_runs
                            ]
                        ),

                    "Load_Time":
                        safe_median(
                            [
                                r[
                                    "Load_Time"
                                ]
                                for r
                                in successful_runs
                            ]
                        ),

                    "Solve_Time":
                        safe_median(
                            [
                                r[
                                    "Solve_Time"
                                ]
                                for r
                                in successful_runs
                            ]
                        ),

                    "Total_Time":
                        safe_median(
                            [
                                r[
                                    "Total_Time"
                                ]
                                for r
                                in successful_runs
                            ]
                        ),

                    "Status":
                        final_status,
                }


            median_results.append(
                median_result
            )

            print()


    # ========================================================
    # LƯU RAW RESULTS
    # ========================================================

    raw_file = (
        "benchmark_sat_runs.csv"
    )

    raw_fields = [
        "Encoding",
        "N",
        "Run",
        "Variables",
        "Clauses",
        "Encode_Time",
        "Load_Time",
        "Solve_Time",
        "Total_Time",
        "Status",
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
    # LƯU MEDIAN RESULTS
    # ========================================================

    median_file = (
        "benchmark_results_median.csv"
    )

    median_fields = [
        "Encoding",
        "N",
        "Variables",
        "Clauses",
        "Encode_Time",
        "Load_Time",
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
    # IN BẢNG KẾT QUẢ MEDIAN
    # ========================================================

    print()

    print(
        "=" * 120
    )

    print(
        "SAT BENCHMARK - "
        "MEDIAN OF 5 RUNS"
    )

    print(
        "=" * 120
    )

    print(
        f"{'Encoding':<16}"
        f"{'N':>6}"
        f"{'Variables':>12}"
        f"{'Clauses':>12}"
        f"{'Encode(s)':>14}"
        f"{'Load(s)':>14}"
        f"{'Solve(s)':>14}"
        f"{'Total(s)':>14}"
        f"{'Status':>12}"
    )

    print(
        "-" * 120
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

        clauses = (
            "-"
            if result[
                "Clauses"
            ] is None
            else str(
                result[
                    "Clauses"
                ]
            )
        )


        def fmt_time(value):

            if value is None:
                return "-"

            return (
                f"{value:.6f}"
            )


        print(
            f"{result['Encoding']:<16}"
            f"{result['N']:>6}"
            f"{variables:>12}"
            f"{clauses:>12}"
            f"{fmt_time(result['Encode_Time']):>14}"
            f"{fmt_time(result['Load_Time']):>14}"
            f"{fmt_time(result['Solve_Time']):>14}"
            f"{fmt_time(result['Total_Time']):>14}"
            f"{result['Status']:>12}"
        )


    print(
        "=" * 120
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
# MAIN
# ============================================================

if __name__ == "__main__":

    mp.freeze_support()

    benchmark_nqueens()