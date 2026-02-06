# GPCR-Guided ANM Web Tool

A web-based application for performing **guided (state-dependent) and conventional Elastic Network Model (ANM)** analyses of **G-Protein Coupled Receptors (GPCRs)** using **ProDy**.

This project combines **scientific computing**, **backend development**, and a **clean web interface** to make advanced normal mode analysis accessible through a browser.

---

## 🚀 What this tool does

### Guided ANM (GPCR activation)
- Takes **inactive and active GPCR structures** as input
- Aligns structures and computes **distance-dependent spring softening**
- Builds a **state-aware Hessian matrix**
- Calculates low-frequency collective modes relevant to GPCR activation
- Outputs:
  - `*_initial.pdb`
  - `*_transition.nmd` (for VMD Normal Mode Wizard)

### Conventional ANM
- Takes a **single structure**
- Performs standard ProDy ANM
- Outputs:
  - `*_initial.pdb`
  - `*_conventionalANM.nmd`

Both workflows produce files directly usable in **VMD → Normal Mode Wizard**.

---

## 🧠 Scientific idea

Traditional ANM uses a **uniform spring constant** for all residue contacts.  
In contrast, the **guided ANM** implemented here:

- Computes pairwise Cα distance changes between inactive and active states
- Identifies contacts that significantly rearrange during activation
- Softens those interactions using a **distance-dependent force constant**
- Produces modes that better reflect the **functional transition** of GPCRs

This approach is particularly suitable for **conformationally driven signaling proteins**.

---

## 🖥️ Web interface

The web interface provides:
- Separate workflows for **guided** and **conventional** ANM
- File upload and validation
- Automatic result packaging and download
- Embedded GPCR activation animation for context

A **static demo** of the interface is hosted via GitHub Pages.

