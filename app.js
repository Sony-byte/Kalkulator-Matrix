const API_URL = "http://127.0.0.1:5000/api/hitung";

const state = {
  mode: "obe",
  rows: 3,
  cols: 3,
  opType: "tambah", // tambah | kurang | kali | bagi | transpose | determinan
  numPoints: 4,
  dimPoints: 2
};

const MODE_INFO = {
  obe: {
    title: "1. Aturan OBE (RREF)",
    desc: "Mengubah matriks ke bentuk Eselon Baris Tereduksi dengan langkah baris elementer."
  },
  spl: {
    title: "2. Resolusi SPL (Ax = b)",
    desc: "Menyelesaikan sistem persamaan linear berdasarkan matriks koefisien A dan vektor b."
  },
  invers: {
    title: "3. Matriks Invers",
    desc: "Mencari invers matriks persegi menggunakan metode Gauss-Jordan [A | I]."
  },
  cramer: {
    title: "4. Aturan Cramer",
    desc: "Menyelesaikan SPL persegi dengan perbandingan determinan det(A_i) / det(A)."
  },
  norma: {
    title: "5. Norma Vektor",
    desc: "Menghitung norma L1 (Manhattan), L2 (Euclidean), dan L-infinity."
  },
  titik: {
    title: "6. Jangkauan Titik",
    desc: "Menghitung rentang tiap sumbu (max - min) serta jarak Euclidean maksimum antar titik."
  },
  operasi: {
    title: "7. Operasi Matriks",
    desc: "Penjumlahan, pengurangan, perkalian, pembagian (A * B^-1), transpose, dan determinan."
  }
};

function renderWorkspace() {
  const controls = document.getElementById("dynamicControls");
  const workspace = document.getElementById("inputWorkspace");
  controls.innerHTML = "";
  workspace.innerHTML = "";

  if (state.mode === "obe") {
    addDimControl(controls, "Baris", state.rows, (v) => { state.rows = v; renderWorkspace(); });
    addDimControl(controls, "Kolom", state.cols, (v) => { state.cols = v; renderWorkspace(); });
    workspace.appendChild(buildMatrixBlock("Matriks A", "matA", state.rows, state.cols));
  } else if (state.mode === "spl" || state.mode === "cramer") {
    addDimControl(controls, "Persamaan / Baris", state.rows, (v) => {
      state.rows = v;
      if (state.mode === "cramer") state.cols = v;
      renderWorkspace();
    });
    if (state.mode === "spl") {
      addDimControl(controls, "Variabel / Kolom", state.cols, (v) => { state.cols = v; renderWorkspace(); });
    } else {
      state.cols = state.rows;
    }
    workspace.appendChild(buildMatrixBlock("Matriks Koefisien A", "matA", state.rows, state.cols));
    workspace.appendChild(buildMatrixBlock("Vektor Konstanta b", "vecB", state.rows, 1));
  } else if (state.mode === "invers") {
    addDimControl(controls, "Ukuran Persegi (n x n)", state.rows, (v) => {
      state.rows = v;
      state.cols = v;
      renderWorkspace();
    });
    workspace.appendChild(buildMatrixBlock("Matriks Persegi A", "matA", state.rows, state.rows));
  } else if (state.mode === "norma") {
    addDimControl(controls, "Panjang Vektor", state.cols, (v) => { state.cols = v; renderWorkspace(); });
    workspace.appendChild(buildMatrixBlock("Vektor v", "vecV", 1, state.cols));
  } else if (state.mode === "titik") {
    addDimControl(controls, "Jumlah Titik", state.numPoints, (v) => { state.numPoints = v; renderWorkspace(); });
    addDimControl(controls, "Dimensi", state.dimPoints, (v) => { state.dimPoints = v; renderWorkspace(); });
    workspace.appendChild(buildMatrixBlock("Daftar Titik (tiap baris = 1 titik)", "pts", state.numPoints, state.dimPoints));
  } else if (state.mode === "operasi") {
    const selectWrap = document.createElement("div");
    selectWrap.className = "control-group";
    selectWrap.innerHTML = `
      <label for="opSelect">Operasi:</label>
      <select id="opSelect">
        <option value="tambah">Penjumlahan (A + B)</option>
        <option value="kurang">Pengurangan (A - B)</option>
        <option value="kali">Perkalian (A x B)</option>
        <option value="bagi">Pembagian (A * B^-1)</option>
        <option value="transpose">Transpose (A^T)</option>
        <option value="determinan">Determinan det(A)</option>
      </select>
    `;
    controls.appendChild(selectWrap);
    const sel = selectWrap.querySelector("select");
    sel.value = state.opType;
    sel.addEventListener("change", (e) => {
      state.opType = e.target.value;
      renderWorkspace();
    });

    if (["tambah", "kurang"].includes(state.opType)) {
      addDimControl(controls, "Baris", state.rows, (v) => { state.rows = v; renderWorkspace(); });
      addDimControl(controls, "Kolom", state.cols, (v) => { state.cols = v; renderWorkspace(); });
      workspace.appendChild(buildMatrixBlock("Matriks A", "matA", state.rows, state.cols));
      workspace.appendChild(buildMatrixBlock("Matriks B", "matB", state.rows, state.cols));
    } else if (state.opType === "kali") {
      addDimControl(controls, "Baris A", state.rows, (v) => { state.rows = v; renderWorkspace(); });
      addDimControl(controls, "Kolom A (= Baris B)", state.cols, (v) => { state.cols = v; renderWorkspace(); });
      addDimControl(controls, "Kolom B", state.numPoints, (v) => { state.numPoints = v; renderWorkspace(); });
      workspace.appendChild(buildMatrixBlock("Matriks A", "matA", state.rows, state.cols));
      workspace.appendChild(buildMatrixBlock("Matriks B", "matB", state.cols, state.numPoints));
    } else if (state.opType === "bagi") {
      addDimControl(controls, "Baris A", state.rows, (v) => { state.rows = v; renderWorkspace(); });
      addDimControl(controls, "Ukuran B (n x n = Kolom A)", state.cols, (v) => { state.cols = v; renderWorkspace(); });
      workspace.appendChild(buildMatrixBlock("Matriks A", "matA", state.rows, state.cols));
      workspace.appendChild(buildMatrixBlock("Matriks B (Persegi)", "matB", state.cols, state.cols));
    } else if (state.opType === "transpose") {
      addDimControl(controls, "Baris A", state.rows, (v) => { state.rows = v; renderWorkspace(); });
      addDimControl(controls, "Kolom A", state.cols, (v) => { state.cols = v; renderWorkspace(); });
      workspace.appendChild(buildMatrixBlock("Matriks A", "matA", state.rows, state.cols));
    } else if (state.opType === "determinan") {
      addDimControl(controls, "Ukuran Persegi (n x n)", state.rows, (v) => { state.rows = v; renderWorkspace(); });
      workspace.appendChild(buildMatrixBlock("Matriks Persegi A", "matA", state.rows, state.rows));
    }
  }
}

function addDimControl(parent, label, value, onChange) {
  const wrap = document.createElement("div");
  wrap.className = "control-group";
  const input = document.createElement("input");
  input.type = "number";
  input.min = 1;
  input.max = 6;
  input.value = value;
  input.addEventListener("change", () => {
    const parsed = Math.max(1, Math.min(6, parseInt(input.value || "1", 10)));
    input.value = parsed;
    onChange(parsed);
  });
  const lbl = document.createElement("label");
  lbl.textContent = label + ":";
  wrap.append(lbl, input);
  parent.appendChild(wrap);
}

function buildMatrixBlock(title, idPrefix, r, c) {
  const block = document.createElement("div");
  block.className = "matrix-block";
  const heading = document.createElement("h4");
  heading.textContent = title;
  const grid = document.createElement("div");
  grid.className = "matrix-grid";
  grid.style.gridTemplateColumns = `repeat(${c}, auto)`;

  for (let i = 0; i < r; i++) {
    for (let j = 0; j < c; j++) {
      const inp = document.createElement("input");
      inp.type = "text";
      inp.className = "cell-input";
      inp.dataset.group = idPrefix;
      inp.dataset.row = i;
      inp.dataset.col = j;
      inp.value = "0";
      block.dataset.rows = r;
      block.dataset.cols = c;
      grid.appendChild(inp);
    }
  }

  block.append(heading, grid);
  return block;
}

function readMatrix(idPrefix, r, c) {
  const mat = [];
  for (let i = 0; i < r; i++) {
    const row = [];
    for (let j = 0; j < c; j++) {
      const el = document.querySelector(`.cell-input[data-group="${idPrefix}"][data-row="${i}"][data-col="${j}"]`);
      const val = parseFloat((el?.value || "0").replace(",", "."));
      if (Number.isNaN(val)) {
        throw new Error(`Input tidak valid pada ${idPrefix} baris ${i + 1}, kolom ${j + 1}.`);
      }
      row.push(val);
    }
    mat.push(row);
  }
  return mat;
}

function fillValues(idPrefix, data) {
  data.forEach((row, i) => {
    row.forEach((val, j) => {
      const el = document.querySelector(`.cell-input[data-group="${idPrefix}"][data-row="${i}"][data-col="${j}"]`);
      if (el) el.value = String(val);
    });
  });
}

function isiContoh() {
  if (state.mode === "obe") {
    state.rows = 3; state.cols = 3; renderWorkspace();
    fillValues("matA", [[2, 4, -2], [4, 9, -3], [-2, -3, 7]]);
  } else if (state.mode === "spl" || state.mode === "cramer") {
    state.rows = 3; state.cols = 3; renderWorkspace();
    fillValues("matA", [[2, 1, -1], [-3, -1, 2], [-2, 1, 2]]);
    fillValues("vecB", [[8], [-11], [-3]]);
  } else if (state.mode === "invers") {
    state.rows = 3; state.cols = 3; renderWorkspace();
    fillValues("matA", [[2, 1, -1], [-3, -1, 2], [-2, 1, 2]]);
  } else if (state.mode === "norma") {
    state.cols = 3; renderWorkspace();
    fillValues("vecV", [[3, -4, 12]]);
  } else if (state.mode === "titik") {
    state.numPoints = 4; state.dimPoints = 2; renderWorkspace();
    fillValues("pts", [[1, 2], [4, 6], [-2, 5], [3, -1]]);
  } else if (state.mode === "operasi") {
    state.rows = 2; state.cols = 2; state.numPoints = 2; renderWorkspace();
    fillValues("matA", [[1, 2], [3, 4]]);
    fillValues("matB", [[2, 0], [1, 2]]);
  }
}

function renderOutput(payload) {
  const out = document.getElementById("outputContainer");
  out.innerHTML = "";
  if (payload.error) {
    out.innerHTML = `<div class="error-box">${payload.error}</div>`;
    return;
  }
  (payload.steps || []).forEach((step) => {
    const box = document.createElement("div");
    box.className = "step-box";
    box.innerHTML = `<strong>${step.judul}</strong><div>${step.penjelasan || ""}</div>`;
    if (step.matriks) {
      const pre = document.createElement("pre");
      pre.className = "matrix-view";
      pre.textContent = step.matriks;
      box.appendChild(pre);
    }
    out.appendChild(box);
  });
}

async function hitung() {
  const out = document.getElementById("outputContainer");
  try {
    let bodyData = { mode: state.mode };

    if (state.mode === "obe") {
      bodyData.A = readMatrix("matA", state.rows, state.cols);
    } else if (state.mode === "spl" || state.mode === "cramer") {
      bodyData.A = readMatrix("matA", state.rows, state.cols);
      bodyData.b = readMatrix("vecB", state.rows, 1).map((r) => r[0]);
    } else if (state.mode === "invers") {
      bodyData.A = readMatrix("matA", state.rows, state.rows);
    } else if (state.mode === "norma") {
      bodyData.v = readMatrix("vecV", 1, state.cols)[0];
    } else if (state.mode === "titik") {
      bodyData.points = readMatrix("pts", state.numPoints, state.dimPoints);
    } else if (state.mode === "operasi") {
      bodyData.op_type = state.opType;
      if (["tambah", "kurang"].includes(state.opType)) {
        bodyData.A = readMatrix("matA", state.rows, state.cols);
        bodyData.B = readMatrix("matB", state.rows, state.cols);
      } else if (state.opType === "kali") {
        bodyData.A = readMatrix("matA", state.rows, state.cols);
        bodyData.B = readMatrix("matB", state.cols, state.numPoints);
      } else if (state.opType === "bagi") {
        bodyData.A = readMatrix("matA", state.rows, state.cols);
        bodyData.B = readMatrix("matB", state.cols, state.cols);
      } else if (state.opType === "transpose") {
        bodyData.A = readMatrix("matA", state.rows, state.cols);
      } else if (state.opType === "determinan") {
        bodyData.A = readMatrix("matA", state.rows, state.rows);
      }
    }

    out.innerHTML = `<p class="placeholder-text">Menghitung di server Python...</p>`;
    const res = await fetch(API_URL, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(bodyData)
    });
    const data = await res.json();
    renderOutput(data);
  } catch (err) {
    renderOutput({ error: err.message });
  }
}

document.querySelectorAll(".menu-btn").forEach((btn) => {
  btn.addEventListener("click", () => {
    document.querySelectorAll(".menu-btn").forEach((b) => b.classList.remove("active"));
    btn.classList.add("active");
    state.mode = btn.dataset.mode;
    document.getElementById("modeTitle").textContent = MODE_INFO[state.mode].title;
    document.getElementById("modeDesc").textContent = MODE_INFO[state.mode].desc;
    renderWorkspace();
  });
});

document.getElementById("btnContoh").addEventListener("click", isiContoh);
document.getElementById("btnReset").addEventListener("click", renderWorkspace);
document.getElementById("btnHitung").addEventListener("click", hitung);

renderWorkspace();