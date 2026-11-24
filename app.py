
from flask import Flask, render_template, request, jsonify
import math

app = Flask(__name__)


# ==========================================
# FUNGSI DASAR MATRIKS
# ==========================================

EPS = 1e-10


def validate_matrix(A):
    if not A or not A[0]:
        raise ValueError("Matriks tidak boleh kosong.")

    cols = len(A[0])

    if any(len(row) != cols for row in A):
        raise ValueError("Jumlah kolom setiap baris harus sama.")

    if not all(math.isfinite(float(x)) for row in A for x in row):
        raise ValueError("Matriks harus berisi angka yang valid.")


def clean(x):
    x = float(x)
    if abs(x) < EPS:
        return 0.0
    return round(x, 8)


def format_matrix(A):
    return [[clean(x) for x in row] for row in A]


def determinant(A):
    validate_matrix(A)

    n = len(A)

    if n != len(A[0]):
        raise ValueError("Determinan hanya berlaku untuk matriks persegi.")

    M = [list(map(float, row)) for row in A]
    det = 1.0

    for i in range(n):
        pivot = max(range(i, n), key=lambda r: abs(M[r][i]))

        if abs(M[pivot][i]) < EPS:
            return 0.0

        if pivot != i:
            M[i], M[pivot] = M[pivot], M[i]
            det *= -1

        p = M[i][i]
        det *= p

        for j in range(i + 1, n):
            factor = M[j][i] / p

            for k in range(i + 1, n):
                M[j][k] -= factor * M[i][k]

    return clean(det)


# ==========================================
# OPERASI BARIS ELEMENTER (OBE)
# ==========================================

def gauss_jordan(A):
    validate_matrix(A)

    M = [list(map(float, row)) for row in A]
    rows = len(M)
    cols = len(M[0])

    steps = [{"description": "Matriks awal", "matrix": format_matrix(M)}]

    pivot_row = 0
    pivot_columns = []

    for col in range(cols):

        if pivot_row >= rows:
            break

        pivot = max(
            range(pivot_row, rows),
            key=lambda r: abs(M[r][col])
        )

        if abs(M[pivot][col]) < EPS:
            continue

        if pivot != pivot_row:
            M[pivot], M[pivot_row] = M[pivot_row], M[pivot]
            steps.append({
                "description": f"Tukar baris B{pivot_row + 1} dengan B{pivot + 1}",
                "matrix": format_matrix(M)
            })

        p = M[pivot_row][col]

        if abs(p - 1) > EPS:
            M[pivot_row] = [x / p for x in M[pivot_row]]

            steps.append({
                "description": f"B{pivot_row + 1} dibagi {clean(p)}",
                "matrix": format_matrix(M)
            })

        for r in range(rows):
            if r == pivot_row:
                continue

            factor = M[r][col]

            if abs(factor) > EPS:
                M[r] = [
                    M[r][c] - factor * M[pivot_row][c]
                    for c in range(cols)
                ]

                steps.append({
                    "description": (
                        f"B{r + 1} = B{r + 1} - "
                        f"({clean(factor)}) × B{pivot_row + 1}"
                    ),
                    "matrix": format_matrix(M)
                })

        pivot_columns.append(col)
        pivot_row += 1

    M = [
        [0.0 if abs(x) < EPS else x for x in row]
        for row in M
    ]

    steps.append({
        "description": "Hasil akhir bentuk eselon baris tereduksi (RREF)",
        "matrix": format_matrix(M)
    })

    return M, steps, pivot_columns


# ==========================================
# 1. OBE
# ==========================================

def hitung_obe(A):
    R, steps, pivots = gauss_jordan(A)

    return {
        "hasil": format_matrix(R),
        "langkah": steps,
        "pivot": [p + 1 for p in pivots]
    }


# ==========================================
# 2. SISTEM PERSAMAAN LINEAR
# ==========================================

def hitung_spl(A, b):
    validate_matrix(A)

    rows = len(A)
    cols = len(A[0])

    if len(b) != rows:
        raise ValueError("Jumlah nilai B harus sama dengan jumlah baris A.")

    augmented = [
        list(map(float, A[i])) + [float(b[i])]
        for i in range(rows)
    ]

    R, steps, pivots = gauss_jordan(augmented)

    # Cek sistem tidak konsisten
    for row in R:
        if all(abs(x) < EPS for x in row[:-1]) and abs(row[-1]) > EPS:
            return {
                "jenis": "Tidak memiliki solusi",
                "hasil": None,
                "langkah": steps
            }

    variable_pivots = [p for p in pivots if p < cols]

    if len(variable_pivots) < cols:
        free_vars = [
            f"x{i + 1}"
            for i in range(cols)
            if i not in variable_pivots
        ]

        return {
            "jenis": "Memiliki tak hingga banyak solusi",
            "hasil": format_matrix(R),
            "variabel_bebas": free_vars,
            "langkah": steps
        }

    solution = [0.0] * cols

    for i, p in enumerate(pivots):
        if p < cols:
            solution[p] = R[i][-1]

    return {
        "jenis": "Solusi tunggal",
        "hasil": {
            f"x{i + 1}": clean(value)
            for i, value in enumerate(solution)
        },
        "langkah": steps
    }


# ==========================================
# 3. INVERS MATRIKS
# ==========================================

def hitung_invers(A):
    validate_matrix(A)

    n = len(A)

    if n != len(A[0]):
        raise ValueError("Matriks harus berbentuk persegi.")

    if abs(determinant(A)) < EPS:
        raise ValueError("Invers tidak ada karena determinan = 0.")

    augmented = [
        list(map(float, A[i])) +
        [1.0 if i == j else 0.0 for j in range(n)]
        for i in range(n)
    ]

    R, steps, pivots = gauss_jordan(augmented)

    invers = [row[n:] for row in R]

    return {
        "determinan": determinant(A),
        "hasil": format_matrix(invers),
        "langkah": steps
    }


# ==========================================
# 4. ATURAN CRAMER
# ==========================================

def hitung_cramer(A, b):
    validate_matrix(A)

    n = len(A)

    if n != len(A[0]):
        raise ValueError("Matriks A harus berbentuk persegi.")

    if len(b) != n:
        raise ValueError("Jumlah nilai B tidak sesuai.")

    D = determinant(A)

    if abs(D) < EPS:
        raise ValueError(
            "Aturan Cramer tidak dapat digunakan karena determinan A = 0."
        )

    hasil = {}
    detail = []

    for i in range(n):
        Ai = [row[:] for row in A]

        for j in range(n):
            Ai[j][i] = b[j]

        Di = determinant(Ai)
        xi = Di / D

        hasil[f"x{i + 1}"] = clean(xi)

        detail.append({
            "variabel": f"x{i + 1}",
            "determinan": clean(Di),
            "perhitungan": f"{clean(Di)} / {clean(D)}",
            "hasil": clean(xi)
        })

    return {
        "determinan_A": clean(D),
        "hasil": hasil,
        "langkah": detail
    }


# ==========================================
# 5. NORMA VEKTOR
# ==========================================

def hitung_norma(v, jenis):
    if not v:
        raise ValueError("Vektor tidak boleh kosong.")

    v = list(map(float, v))

    if not all(math.isfinite(x) for x in v):
        raise ValueError("Vektor harus berisi angka valid.")

    if jenis == "L1":
        hasil = sum(abs(x) for x in v)

    elif jenis == "L2":
        hasil = math.sqrt(sum(x ** 2 for x in v))

    elif jenis == "Linf":
        hasil = max(abs(x) for x in v)

    else:
        raise ValueError("Jenis norma tidak dikenal.")

    return {
        "vektor": [clean(x) for x in v],
        "jenis": jenis,
        "hasil": clean(hasil)
    }


# ==========================================
# 6. JARAK ANTARA DUA TITIK
# ==========================================

def hitung_jarak(P, Q):
    if not P or len(P) != len(Q):
        raise ValueError("Kedua titik harus memiliki dimensi yang sama.")

    P = list(map(float, P))
    Q = list(map(float, Q))

    if not all(math.isfinite(x) for x in P + Q):
        raise ValueError("Koordinat harus berupa angka valid.")

    selisih = [Q[i] - P[i] for i in range(len(P))]

    jarak = math.sqrt(sum(x ** 2 for x in selisih))

    return {
        "titik_P": P,
        "titik_Q": Q,
        "selisih": [clean(x) for x in selisih],
        "hasil": clean(jarak)
    }


# ==========================================
# ROUTE WEBSITE
# ==========================================

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/hitung", methods=["POST"])
def hitung():
    try:
        data = request.get_json()

        jenis = data.get("jenis")

        if jenis == "obe":
            hasil = hitung_obe(data["A"])

        elif jenis == "spl":
            hasil = hitung_spl(data["A"], data["b"])

        elif jenis == "invers":
            hasil = hitung_invers(data["A"])

        elif jenis == "cramer":
            hasil = hitung_cramer(data["A"], data["b"])

        elif jenis == "norma":
            hasil = hitung_norma(data["v"], data["norma"])

        elif jenis == "jarak":
            hasil = hitung_jarak(data["P"], data["Q"])

        else:
            raise ValueError("Pilihan perhitungan tidak tersedia.")

        return jsonify({
            "success": True,
            "hasil": hasil
        })

    except (ValueError, KeyError, TypeError, ZeroDivisionError) as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 400

    except Exception:
        return jsonify({
            "success": False,
            "error": "Terjadi kesalahan dalam proses perhitungan."
        }), 500


if __name__ == "__main__":
    app.run(debug=True)
