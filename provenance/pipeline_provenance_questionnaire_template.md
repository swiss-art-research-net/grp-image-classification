# ML Pipeline Provenance Questionnaire Template

Use this template to document any machine learning processing pipeline in a way that supports automatic provenance generation.

The questions are designed to capture the entities, process steps, resources, and outputs needed for provenance-ready ML pipeline documentation.

---

## 1) How to use this template

Answer each question as concretely as possible.

- Prefer stable names, repository links, and explicit actor roles.
- If something does not apply, write `N/A` (do not leave blank).
- If unknown at authoring time, write `UNKNOWN`.
- For activity timing, always indicate the source files from which timing can be derived.

---

## 2) Document metadata

### 2.1 Questionnaire record
- What is the title of this pipeline documentation?
  - Answer:
- From which file(s) can the completion time of this questionnaire be derived?
  - Answer:
- Which repository/path stores this document?
  - Answer:

### 2.2 Scope and intent
- What is the pipeline expected to do, in one sentence?
  - Answer:
- Is this document covering a full pipeline or only a subset of steps?
  - Answer:

---

## 3) Project context

- What is the project name?
  - Answer:
- What is the project description?
  - Answer:
- What project URL provides further context?
  - Answer:
- Who are the project actors (people/institutions), and which role do they play in the project?
  - Answer:
---

## 4) Pipeline overview

- What is the pipeline name?
  - Answer:
- What is the overall pipeline type/category?
  - Answer:
- From which file(s) can the pipeline-level activity timing be derived?
  - Answer:
- What is the ordered list of steps in execution sequence?
  - Answer:

---

## 5) Pipeline step questionnaire (repeat per step)

Copy this section for each step in your pipeline.  
If the same digital object, software, or service appears in multiple steps, repeat only what changed and reference the previous step where it was first described.

### Step [STEP_NAME]

#### A. Step identity
- What is the step name?
  - Answer:
- What is the step type (`Labelling`, `ModelTraining`, `Prediction`, `DataTransformation`, `DataAnalysis`, or other)?
  - Answer:
- What is the short human-readable description?
  - Answer:

#### B. Time and context
- From which file(s) can this step's start time be derived?
  - Answer:
- From which file(s) can this step's end time be derived?
  - Answer:
- Which project does this step belong to?
  - Answer:
- Which previous step(s) must complete before this one?
  - Answer:
- Which next step(s) depend on this one?
  - Answer:

#### C. Inputs and outputs
- Which input digital objects are consumed?
  - Answer:
- For each input digital object: what is its type/kind, what does it contain, and where can it be accessed (URL/path)?
  - Answer:
- For each input digital object: is it part of a larger dataset? If yes, which one?
  - Answer:
- For each input, what specific version/snapshot was used?
  - Answer:
- Which output digital objects are produced?
  - Answer:
- For each output digital object: what is its type/kind, what does it contain, and where can it be accessed (URL/path)?
  - Answer:
- For each output, what guarantees integrity/reproducibility (checksum, commit, immutable storage location)?
  - Answer:
- Is a log file produced? If yes, what is it called and where is it stored?
  - Answer:

#### D. Execution resources
- Which software executed this step?
  - Answer:
- For each software used: what version, commit hash, or release tag was used?
  - Answer:
- For each software used: what is its role in this step, and where is the source/executable located (URL/path)?
  - Answer:
- Which model artifact(s) are used (if applicable)?
  - Answer:
- Which service/API/platform is used (if applicable)?
  - Answer:
- For each service/API/platform used: what is its type, endpoint (if applicable), operator/maintainer, role, and version/configuration?
  - Answer:
- What runtime environment details matter (OS, container image, hardware, GPU)?
  - Answer:

#### E. Agents and responsibility
- Which human/institution actors are responsible for this step?
  - Answer:
- What role did each actor play (author, annotator, reviewer, maintainer, operator)?
  - Answer:
- Is there an approver or reviewer for this step's output?
  - Answer:

