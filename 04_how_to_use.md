# How to Use the FreeCAD Auto-Grader

A practical guide for marking Grade 9 IT phone stand submissions.

---

## What's in this bundle

| File | Purpose |
|---|---|
| `01_rubric.md` | The 100-point rubric (clean reference for the project) |
| `02_phone_stand_rubric.docx` | Same rubric formatted as a Word document — print or share with students |
| `03_grade_freecad.py` | The Python auto-grading script |
| `04_how_to_use.md` | This guide |
| `05_sample_submission.FCStd` | A real student submission used during development |

---

## Quick start

### 1. One-off check on a single submission

```bash
python3 03_grade_freecad.py path/to/student.FCStd
```

You'll get a per-criterion breakdown printed to the terminal, plus a total and grade band.

### 2. Batch-grade a whole class

Put all submissions in one folder, then run:

```bash
python3 03_grade_freecad.py path/to/submissions/
```

The script will:
- Print each student's report to the terminal
- Write a `grade_summary.csv` file you can open in Excel or import into your gradebook

---

## Requirements

- **Python 3** (any version from 3.7 onward)
- **No FreeCAD installation needed** — the script reads the XML inside the `.FCStd` zip directly

That's it. The script uses only Python's standard library, so there's nothing to `pip install`.

---

## Suggested classroom workflow

1. **Set up a collection folder** in OneDrive / Teams / wherever you collect work
2. **Tell students to name their file** as `surname_firstname.FCStd` — keeps the CSV tidy
3. **Download all submissions** to a local folder once the deadline passes
4. **Run the script on the folder** — takes a few seconds for a class of 30
5. **Open the CSV** in Excel, paste the column you want into your gradebook
6. **Spot-check 3–5 files** manually in FreeCAD to make sure the script's calls match your professional judgement
7. **Use the per-criterion comments** when giving feedback to students who lost points

---

## What the script is good at

- Catching students who skipped the 3D feature step (very common)
- Distinguishing well-constrained sketches from under-constrained ones
- Detecting whether students linked features back to sketches properly
- Flagging files that weren't recomputed before saving
- Producing a consistent, defensible mark across many submissions

## What the script can't do

- **Judge design quality, creativity, or elegance** — you'd need to look at the model for that
- **Verify the actual 3D shape matches the assignment brief** — it can measure constraints but not "does this look like a phone stand?"
- **Detect cheating or copying** — students could submit very similar files and the script wouldn't notice. (FreeCAD's file metadata can help here — file size and feature counts won't be identical for genuinely independent work.)

For these dimensions, do a quick visual pass through 5–10 files in FreeCAD itself.

---

## Customising the rubric

The rubric criteria and point values live in `03_grade_freecad.py` itself, in the `grade_submission()` function. Each criterion is a labelled block of code. To tweak:

- **Change point values**: edit the `max_points` argument in the relevant `RubricResult(...)` call
- **Add a new criterion**: copy an existing block, change the check logic and the section label
- **Remove a criterion**: comment out or delete the relevant block
- **Adjust the constraint-ratio thresholds** (e.g. how strict "fully constrained" is): edit the `if ratio >= ...` thresholds in section 1.4

Always re-test on a known-good file after changing the script.

---

## Calibrating before first use

Before running on a real class, recommended steps:

1. Build a **gold-standard reference model** in FreeCAD yourself — the way you'd want a student to do it
2. Run the script on it and confirm it scores at or near 100
3. Build a **deliberately mediocre version** (sketch only, no Pad) and confirm it scores low
4. Build a **partial version** (Pad done, but under-constrained sketch) and confirm it lands mid-range
5. Tweak thresholds if any of those don't match your professional judgement

This 30-minute calibration step is worth it because all 30 students will be scored against those thresholds.

---

## Troubleshooting

**"No identifiable constraints" on a file you know has constraints**
The XML format varies slightly between FreeCAD versions. Open the `Document.xml` inside the `.FCStd` (rename to `.zip`, unzip) and check the constraint element naming. The script looks for elements tagged `Constrain` with a `Type` attribute.

**Script crashes on a file**
A corrupted `.FCStd` will cause the open step to fail; the script reports this and skips the file. Students should re-save their submission in FreeCAD.

**Scores feel too harsh or too lenient**
This is normal on the first run. Adjust the thresholds (e.g. drop the constraint ratio threshold from 2.5 to 2.0, or change a max_points value). The script is designed to be edited.

---

## Extending the script

Things you could add later:

- **HTML or PDF report output** instead of plain terminal text (useful for student feedback)
- **A FreeCAD macro version** of the script — runs inside FreeCAD itself, giving access to exact 3D measurements (volume, surface area, wall thickness) instead of estimates
- **An anti-cheating heuristic** — flag pairs of submissions with suspiciously similar feature trees
- **Microsoft Forms / Power Automate integration** — feed scores directly into Teams gradebook

Happy to help build any of these when you're ready.
