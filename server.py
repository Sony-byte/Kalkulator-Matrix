import numpy as np
from flask import Flask, jsonify, request
from flask_cors import CORS

app = Flask(__name__)
CORS(app)


def fmt_mat(arr):
    arr = np.where(np.abs(arr) < 1e-10, 0.0, arr)
    return np.array2string(np.round(arr, 4), suppress_small=True)


def langkah_obe(matrix):
    A = np.where(np.abs(np.array(matrix, dtype=float)) < 1e-10, 0.0, np.array(matrix, dtype=float))
    rows, cols = A.shape
    lead = 0
    no = 1
    steps = [{"judul": "Matriks Awal", "penjelasan": "", "matriks": fmt_mat(A)}]

    for r in range(rows):
        if lead >= cols:
            break
        i = r
        while abs(A[i, lead]) < 1e-10:
            i += 1
            if i == rows:
                i = r
                lead += 1
                if cols == lead:
                    steps.append({"judul": "Hasil Akhir RREF", "penjelasan": "", "matriks": fmt_mat(A)})
                    return A, steps

        if i != r:
            A[[i, r]] = A[[r, i]]
            steps.append({
                "judul": f"Langkah {no}: Tukar Baris {r + 1} ↔ Baris {i + 1}",
                "penjelasan": "",
                "matriks": fmt_mat(A),
            })
            no += 1

        pivot = A[r, lead]
        if abs(pivot - 1.0) > 1e-10:
            A[r] = A[r] / pivot
            steps.append({
                "judul": f"Langkah {no}: Skala Baris {r + 1}",
                "penjelasan": f"R{r + 1} = R{r + 1} / ({pivot:.4f})",
                "matriks": fmt_mat(A),
            })
            no += 1

        for k in range(rows):
            if k != r and abs(A[k, lead]) > 1e-10:
                faktor = A[k, lead]
                A[k] = A[k] - faktor * A[r]
                steps.append({
                    "judul": f"Langkah {no}: Eliminasi Baris {k + 1}",
                    "penjelasan": f"R{k + 1} = R{k + 1} - ({faktor:.4f}) * R{r + 1}",
                    "matriks": fmt_mat(A),
                })
                no += 1

        lead += 1

    steps.append({"judul": "Hasil Akhir RREF", "penjelasan": "", "matriks": fmt_mat(A)})
    return A, steps


def hitung_spl(A, b):
    A = np.array(A, dtype=float)
    b = np.array(b, dtype=float).flatten()
    _, n = A.shape
    aug = np.hstack([A, b.reshape(-1, 1)])
    rref, steps = langkah_obe(aug)
    rank_A = int(np.linalg.matrix_rank(A))
    rank_aug = int(np.linalg.matrix_rank(aug))

    info = f"Rank(A) = {rank_A}, Rank([A|b]) = {rank_aug}, Jumlah variabel = {n}."
    if rank_A < rank_aug:
        steps.append({"judul": "Kesimpulan SPL", "penjelasan": f"{info} Tidak ada solusi (inkonsisten)."})
    elif rank_A < n:
        steps.append({"judul": "Kesimpulan SPL", "penjelasan": f"{info} Solusi tak hingga (derajat kebebasan = {n - rank_A})."})
    else:
        sol_text = ", ".join([f"x{i + 1} = {rref[i, n]:.4f}" for i in range(n)])
        steps.append({"judul": "Solusi Tunggal", "penjelasan": f"{info} Hasil: {sol_text}"})
    return steps


def hitung_invers(A):
    A = np.array(A, dtype=float)
    n, m = A.shape
    if n != m:
        raise ValueError("Matriks harus persegi untuk memiliki invers.")
    det = float(np.linalg.det(A))
    if abs(det) < 1e-10:
        raise ValueError("Determinan = 0 (matriks singular), invers tidak ada.")
    aug = np.hstack([A, np.eye(n)])
    rref, steps = langkah_obe(aug)
    inv = np.where(np.abs(rref[:, n:]) < 1e-10, 0.0, rref[:, n:])
    steps.insert(0, {"judul": "Cek Determinan", "penjelasan": f"det(A) = {det:.4f} ≠ 0 (memiliki invers)."})
    steps.append({"judul": "Matriks Invers A⁻¹", "penjelasan": "", "matriks": fmt_mat(inv)})
    return inv, steps


def hitung_cramer(A, b):
    A = np.array(A, dtype=float)
    b = np.array(b, dtype=float).flatten()
    n, m = A.shape
    if n != m or len(b) != n:
        raise ValueError("Aturan Cramer membutuhkan matriks A persegi (n x n) dan vektor b panjang n.")
    det_A = float(np.linalg.det(A))
    if abs(det_A) < 1e-10:
        raise ValueError("det(A) = 0, Aturan Cramer tidak dapat digunakan.")

    steps = [{"judul": "Langkah 1: Determinan Utama", "penjelasan": f"det(A) = {det_A:.4f}"}]
    for i in range(n):
        A_i = A.copy()
        A_i[:, i] = b
        det_i = float(np.linalg.det(A_i))
        xi = det_i / det_A
        steps.append({
            "judul": f"Variabel x{i + 1} (Kolom {i + 1} diganti b)",
            "penjelasan": f"det(A_{i + 1}) = {det_i:.4f} → x{i + 1} = {det_i:.4f} / {det_A:.4f} = {xi:.4f}",
            "matriks": fmt_mat(A_i),
        })
    return steps


def hitung_norma(v):
    v = np.array(v, dtype=float)
    l1 = float(np.sum(np.abs(v)))
    l2 = float(np.linalg.norm(v, ord=2))
    linf = float(np.max(np.abs(v)))
    return [
        {
            "judul": "Norma L1 (Manhattan)",
            "penjelasan": f"{' + '.join([f'|{x:.4f}|' for x in v])} = {l1:.4f}",
        },
        {
            "judul": "Norma L2 (Euclidean)",
            "penjelasan": f"sqrt({' + '.join([f'({x:.4f})²' for x in v])}) = {l2:.4f}",
        },
        {
            "judul": "Norma L-infinity",
            "penjelasan": f"max({', '.join([f'|{x:.4f}|' for x in v])}) = {linf:.4f}",
        },
    ]


def hitung_titik(pts):
    pts = np.array(pts, dtype=float)
    k, dim = pts.shape
    steps = []
    rentang_lines = []
    for d in range(dim):
        mn, mx = float(np.min(pts[:, d])), float(np.max(pts[:, d]))
        rentang_lines.append(f"Sumbu {d + 1}: max ({mx:.4f}) - min ({mn:.4f}) = {mx - mn:.4f}")
    steps.append({"judul": "1. Rentang per Sumbu", "penjelasan": "<br>".join(rentang_lines)})

    jarak_lines = []
    jarak_maks = 0.0
    pasangan = None
    for i in range(k):
        for j in range(i + 1, k):
            dist = float(np.linalg.norm(pts[i] - pts[j]))
            jarak_lines.append(f"d(P{i + 1}, P{j + 1}) = {dist:.4f}")
            if dist > jarak_maks:
                jarak_maks = dist
                pasangan = (i + 1, j + 1)

    if pasangan:
        jarak_lines.append(f"<strong>Jarak maksimum: {jarak_maks:.4f} (antara P{pasangan[0]} dan P{pasangan[1]})</strong>")
    else:
        jarak_lines.append("Hanya 1 titik, jarak antar pasangan = 0.0000")

    steps.append({"judul": "2. Jarak Euclidean Antar Titik", "penjelasan": "<br>".join(jarak_lines)})
    return steps


def hitung_operasi(data):
    op = data.get("op_type")
    if op in ("tambah", "kurang"):
        A = np.array(data["A"], dtype=float)
        B = np.array(data["B"], dtype=float)
        if A.shape != B.shape:
            raise ValueError("Ukuran matriks A dan B harus sama.")
        hasil = (A + B) if op == "tambah" else (A - B)
        simbol = "+" if op == "tambah" else "-"
        return [
            {"judul": "Matriks A", "penjelasan": "", "matriks": fmt_mat(A)},
            {"judul": "Matriks B", "penjelasan": "", "matriks": fmt_mat(B)},
            {"judul": f"Hasil A {simbol} B", "penjelasan": "Operasi dilakukan elemen per elemen.", "matriks": fmt_mat(hasil)},
        ]
    if op == "kali":
        A = np.array(data["A"], dtype=float)
        B = np.array(data["B"], dtype=float)
        if A.shape[1] != B.shape[0]:
            raise ValueError("Jumlah kolom A harus sama dengan jumlah baris B.")
        rincian = []
        for i in range(A.shape[0]):
            for j in range(B.shape[1]):
                suku = " + ".join([f"({A[i, k]:.2f}*{B[k, j]:.2f})" for k in range(A.shape[1])])
                rincian.append(f"C[{i + 1},{j + 1}] = {suku} = {np.dot(A[i, :], B[:, j]):.4f}")
        return [
            {"judul": "Rincian Perkalian Baris × Kolom", "penjelasan": "<br>".join(rincian)},
            {"judul": "Hasil A × B", "penjelasan": "", "matriks": fmt_mat(A @ B)},
        ]
    if op == "bagi":
        A = np.array(data["A"], dtype=float)
        B = np.array(data["B"], dtype=float)
        if B.shape[0] != B.shape[1] or A.shape[1] != B.shape[0]:
            raise ValueError("B harus persegi (n x n) dan kolom A harus sama dengan n untuk A * B⁻¹.")
        inv_B, inv_steps = hitung_invers(B)
        return inv_steps + [
            {"judul": "Hasil A × B⁻¹", "penjelasan": "", "matriks": fmt_mat(A @ inv_B)}
        ]
    if op == "transpose":
        A = np.array(data["A"], dtype=float)
        return [
            {"judul": "Matriks Awal A", "penjelasan": "", "matriks": fmt_mat(A)},
            {"judul": "Hasil Transpose Aᵀ", "penjelasan": "Baris pada A menjadi kolom pada Aᵀ.", "matriks": fmt_mat(A.T)},
        ]
    if op == "determinan":
        A = np.array(data["A"], dtype=float)
        if A.shape[0] != A.shape[1]:
            raise ValueError("Determinan hanya berlaku untuk matriks persegi.")
        det = float(np.linalg.det(A))
        return [
            {"judul": "Matriks A", "penjelasan": "", "matriks": fmt_mat(A)},
            {"judul": "Nilai Determinan", "penjelasan": f"det(A) = {det:.4f}"},
        ]
    raise ValueError("Jenis operasi tidak dikenal.")


@app.route("/api/hitung", methods=["POST"])
def api_hitung():
    try:
        data = request.get_json(force=True)
        mode = data.get("mode")
        if mode == "obe":
            _, steps = langkah_obe(data["A"])
        elif mode == "spl":
            steps = hitung_spl(data["A"], data["b"])
        elif mode == "invers":
            _, steps = hitung_invers(data["A"])
        elif mode == "cramer":
            steps = hitung_cramer(data["A"], data["b"])
        elif mode == "norma":
            steps = hitung_norma(data["v"])
        elif mode == "titik":
            steps = hitung_titik(data["points"])
        elif mode == "operasi":
            steps = hitung_operasi(data)
        else:
            return jsonify({"error": "Mode tidak dikenali."}), 400
        return jsonify({"steps": steps})
    except Exception as exc:
        return jsonify({"error": str(exc)}), 400


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)