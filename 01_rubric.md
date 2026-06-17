# Grade 9 IT — FreeCAD Phone Stand Assignment

## Auto-Gradable Rubric (100 points)

**Subject:** Information Technology
**Grade level:** Grade 9 (High school / intermediate)
**Assignment:** Design and model a phone stand in FreeCAD
**Submission format:** Single `.FCStd` file per student

---

## Section 1: Technical Execution (45 points)

| # | Criterion | Points | Auto-check |
|---|---|---|---|
| 1.1 | File submitted correctly (`.FCStd`, opens without error) | 5 | File integrity check on the FCStd zip archive |
| 1.2 | PartDesign Body container present | 5 | Object tree contains a `PartDesign::Body` |
| 1.3 | At least one sketch present | 5 | Sketch object exists with geometry |
| 1.4 | Sketch is fully constrained | 12 | Constraint-to-geometry ratio in Document.xml |
| 1.5 | 3D feature created (Pad / Pocket / Revolve) | 13 | Solid feature exists, not just a sketch |
| 1.6 | File saves cleanly (no broken references / errors) | 5 | No "Touched" flags on objects |

## Section 2: Parametric Modelling Technique (30 points)

| # | Criterion | Points | Auto-check |
|---|---|---|---|
| 2.1 | Used sketch-then-feature workflow | 10 | Feature links back to a sketch |
| 2.2 | Used appropriate constraint types (geometric + dimensional) | 10 | Mix of coincident/horizontal/vertical AND distance/radius |
| 2.3 | Used at least 2 different feature types | 5 | Feature tree variety (e.g. Pad + Fillet) |
| 2.4 | Objects renamed meaningfully | 5 | Labels not matching default Sketch001, Pad001, etc. |

## Section 3: Design Requirements (25 points)

| # | Criterion | Points | Auto-check |
|---|---|---|---|
| 3.1 | Overall dimensions within spec (≤ 150 × 100 × 100 mm) | 6 | Bounding box check from geometry |
| 3.2 | Phone slot/groove of appropriate width (8–15 mm) | 6 | Distance constraint in range |
| 3.3 | Stable base (footprint width ≥ 60 mm) | 7 | Base dimension check |
| 3.4 | Wall thickness sufficient for 3D printing (≥ 2 mm) | 6 | Minimum dimensional constraint check |

**Total: 100 points**

---

## Grade Bands

| % | Band |
|---|---|
| 85–100 | Excellent |
| 70–84 | Good |
| 55–69 | Satisfactory |
| 40–54 | Developing |
| Below 40 | Needs resubmission |

---

## Notes on the Rubric

**Why no creativity / aesthetic criteria?**
This rubric is fully auto-gradable. Aesthetic and creative aspects of the design are graded separately (or in a follow-up oral/written reflection), so that the script can produce consistent, objective marks across the whole class.

**Why heavy weighting on sketch constraint and 3D feature?**
These two criteria together (25 points) test whether the student understands the core idea of parametric CAD: a sketch is the basis for a feature, and a fully constrained sketch produces predictable geometry. A student who skips either has misunderstood the central concept.

**Why include "object renaming" for only 5 points?**
It's a habit-building criterion. In real-world CAD work, leaving everything as "Sketch001" and "Pad003" makes a file unreadable to anyone else. Five points is enough to nudge students towards good practice without dominating the mark.
