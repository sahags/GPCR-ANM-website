import os
import uuid
import zipfile
from flask import Flask, request, send_file, abort, send_from_directory
from werkzeug.utils import secure_filename

from gANM import gpcrANM  # <-- your file is gANM.py

app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
JOBS_DIR = os.path.join(BASE_DIR, "jobs")
os.makedirs(JOBS_DIR, exist_ok=True)

ALLOWED_EXT = {".pdb"}
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB

def allowed(filename: str) -> bool:
    return os.path.splitext(filename.lower())[1] in ALLOWED_EXT

@app.route("/", methods=["GET"])
def home():
    # Serve your index.html from the same folder
    return send_from_directory(BASE_DIR, "index.html")

@app.route("/styles.css", methods=["GET"])
def css():
    return send_from_directory(BASE_DIR, "styles.css")

@app.route("/fancy_background.png", methods=["GET"])
def bg():
    return send_from_directory(BASE_DIR, "fancy_background.png")

@app.route("/upload", methods=["POST"])
def upload():
    if "inactive" not in request.files or "active" not in request.files:
        abort(400, description="Please upload both inactive and active PDB files.")

    inactive_f = request.files["inactive"]
    active_f = request.files["active"]

    if inactive_f.filename == "" or active_f.filename == "":
        abort(400, description="Both files must be selected.")

    if not allowed(inactive_f.filename) or not allowed(active_f.filename):
        abort(400, description="Only .pdb files are allowed.")

    job_id = str(uuid.uuid4())
    job_dir = os.path.join(JOBS_DIR, job_id)
    os.makedirs(job_dir, exist_ok=True)

    inactive_name = secure_filename(inactive_f.filename)
    active_name = secure_filename(active_f.filename)
    inactive_base = os.path.splitext(inactive_name)[0]

    inactive_path = os.path.join(job_dir, f"inactive_{inactive_name}")
    active_path = os.path.join(job_dir, f"active_{active_name}")

    inactive_f.save(inactive_path)
    active_f.save(active_path)

    if os.path.getsize(inactive_path) > MAX_FILE_SIZE or os.path.getsize(active_path) > MAX_FILE_SIZE:
        abort(413, description="File too large.")

    # Run your guided ANM and write outputs into job_dir
    try:
        gpcrANM(
            inactive_pdb=inactive_path,
            active_pdb=active_path,
            cutoff=15.0,
            softening_factor=0.1,
            distance_threshold=2.0,
            outdir=job_dir,   # <-- requires the small gANM.py change above
            basename=inactive_base
        )
    except Exception as e:
        abort(500, description=f"ANM failed: {e}")

    out_pdb = os.path.join(job_dir, f"{inactive_base}_inactive.pdb")
    out_nmd = os.path.join(job_dir, f"{inactive_base}_transition.nmd")

    if not (os.path.exists(out_pdb) and os.path.exists(out_nmd)):
        abort(500, description="Output files were not produced.")

    zip_path = os.path.join(job_dir, f"{inactive_base}_gpcrANM_results.zip")
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.write(out_pdb, arcname=os.path.basename(out_pdb))
        zf.write(out_nmd, arcname=os.path.basename(out_nmd))

    return send_file(
        zip_path,
        as_attachment=True,
        download_name=f"{inactive_base}_GPCRanm_results.zip",
        mimetype="application/zip",
    )
@app.route("/upload_conventional", methods=["POST"])
def upload_conventional():
    if "structure" not in request.files:
        abort(400, description="Please upload a PDB file.")

    pdb_f = request.files["structure"]

    if pdb_f.filename == "":
        abort(400, description="No file selected.")

    if not allowed(pdb_f.filename):
        abort(400, description="Only .pdb files are allowed.")

    job_id = str(uuid.uuid4())
    job_dir = os.path.join(JOBS_DIR, job_id)
    os.makedirs(job_dir, exist_ok=True)

    pdb_name = secure_filename(pdb_f.filename)
    pdb_path = os.path.join(job_dir, f"structure_{pdb_name}")
    pdb_f.save(pdb_path)

    if os.path.getsize(pdb_path) > MAX_FILE_SIZE:
        abort(413, description="File too large.")

    # ---- Conventional ANM ----
    try:
        from prody import parsePDB, ANM, writeNMD, writePDB

        pro = parsePDB(pdb_path)
        calphas = pro.select("name CA")
        if calphas is None or calphas.numAtoms() == 0:
            abort(400, description="No C-alpha atoms found in the uploaded PDB.")

        anm = ANM("transition-conventional")
        anm.buildHessian(calphas)   # ProDy default cutoff
        anm.calcModes(n_modes=20)

        base_name = os.path.splitext(pdb_name)[0]
        out_pdb = os.path.join(job_dir, f"{base_name}_initial.pdb")
        out_nmd = os.path.join(job_dir, f"{base_name}_conventionalANM.nmd")

        # Write a PDB to pair with the NMD (CA atoms)
        writePDB(out_pdb, calphas)
        writeNMD(out_nmd, anm[:20], calphas)

    except Exception as e:
        abort(500, description=f"Conventional ANM failed: {e}")

    if not (os.path.exists(out_pdb) and os.path.exists(out_nmd)):
        abort(500, description="Output files were not produced.")

    zip_path = os.path.join(job_dir, f"{base_name}_conventionalANM_results.zip")
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.write(out_pdb, arcname=os.path.basename(out_pdb))
        zf.write(out_nmd, arcname=os.path.basename(out_nmd))

    return send_file(
        zip_path,
        as_attachment=True,
        download_name=f"{base_name}_conventionalANM_results.zip",
        mimetype="application/zip",
    )

@app.route("/output_web.mp4")
def video():
    return send_from_directory(BASE_DIR, "output_web.mp4", mimetype="video/mp4")
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
