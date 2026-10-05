# ML Pipeline Provenance Questionnaire — GRP Image Classification

---

## 2) Document metadata

### 2.1 Questionnaire record
- What is the title of this pipeline documentation?
  - Answer: GRP Image Classification Pipeline Provenance Documentation
- From which file(s) can the completion time of this questionnaire be derived?
  - Answer: Git history of `pipeline_provenance_questionnaire.md` in this repository.
- Which repository/path stores this document?
  - Answer: `pipeline_provenance_questionnaire.md` in the `sari-image-classification` repository (`/Users/mromanello/Documents/uzh-sari/sari-image-classification/`).

### 2.2 Scope and intent
- What is the pipeline expected to do, in one sentence?
  - Answer: Classify images from the GRP (Graphische Sammlung) cultural heritage collection into eight visual-type categories (collage, drawing, handwritten document, machine-produced document, painting, photograph, print, unknown) using a fine-tuned YOLO classification model.
- Is this document covering a full pipeline or only a subset of steps?
  - Answer: Full pipeline, from data collection through annotation, model training, and batch prediction on the full dataset.

---

## 3) Project context

- What is the project name?
  - Answer: SARI Image Classification
- What is the project description?
  - Answer: A machine-learning pipeline that automatically classifies digitised images from the GRP (Graphische Sammlung ETH Zurich) cultural heritage collection into visual-type categories. The pipeline supports the Swiss Art Research Infrastructure (SARI) by enriching image metadata with predicted image types.
- What project URL provides further context?
  - Answer: https://universe.roboflow.com/sariimageannotation/grp-image-classification (annotation project); classification taxonomy guidelines at https://docs.google.com/presentation/d/17C8LQP0_mMth9kH3_mz7iJAH4nqMckNmvulq1g-tIYk/
- Who are the project actors (people/institutions), and which role do they play in the project?
  - Answer:
    - **Matteo Romanello** (UZH / SARI): Project lead, pipeline developer, model trainer, operator.
    - **Student assistant annotators** (mentioned in notebooks: Lukas, Mateo): Image annotators on Roboflow.
    - **Swiss Art Research Infrastructure (SARI)**: Institutional sponsor and user of the classification results.
    - **GTA Archive, ETH Zurich**: Data provider, operator of the IIIF image server (`iiif.gta.arch.ethz.ch`).

---

## 4) Pipeline overview

- What is the pipeline name?
  - Answer: GRP Image Classification Pipeline
- What is the overall pipeline type/category?
  - Answer: Image classification (supervised learning)
- From which file(s) can the pipeline-level activity timing be derived?
  - Answer: Save dates embedded in the YOLO checkpoints (`runs/classify/train42/weights/last.pt`, `models/yolo11n-cls-grp.pt`), elapsed training time in `runs/classify/train42/results.csv`, and git history of repository files (first commit of `data/output/predictions_test.csv`).
- What is the ordered list of steps in execution sequence?
  - Answer:
    1. **ImageDownload** — Download images from the IIIF server
    2. **Labelling** — Annotate a sample of images in Roboflow
    3. **ModelTraining** — Fine-tune a YOLO11n-cls model on the annotated dataset
    4. **Prediction** — Apply the trained model to the full GRP image dataset

---

## 5) Pipeline step questionnaire

### Step ImageDownload

#### A. Step identity
- What is the step name?
  - Answer: ImageDownload
- What is the step type?
  - Answer: DataTransformation
- What is the short human-readable description?
  - Answer: Download GRP images from the GTA IIIF server and store them locally as JPEG files, identified by a hash-based filename.

#### B. Time and context
- From which file(s) can this step's start time be derived?
  - Answer: `clip_data_test/log.txt` (download log with error records); file-system timestamps of downloaded images.
- From which file(s) can this step's end time be derived?
  - Answer: `clip_data_test/log.txt` (last entry); file-system timestamps of downloaded images.
- Which project does this step belong to?
  - Answer: SARI Image Classification / sari-iiif-clip-search (upstream project)
- Which previous step(s) must complete before this one?
  - Answer: None (first step).
- Which next step(s) depend on this one?
  - Answer: Labelling, Prediction.

#### C. Inputs and outputs
- Which input digital objects are consumed?
  - Answer:
    1. `images-20231206.csv` — CSV listing ~117,007 image records with IIIF URLs and local identifiers.
    2. `clip_data_test/images.csv` — Updated CSV listing ~59,827 image records with IIIF URLs and digital object URIs.
- For each input digital object: what is its type/kind, what does it contain, and where can it be accessed?
  - Answer:
    1. `images-20231206.csv`: CSV file; columns `iiif_url`, `id` (SARI resource URI), `localIdentifier` (hash-based filename). Located at `./images-20231206.csv`. A copy of https://raw.githubusercontent.com/swiss-art-research-net/sari-iiif-clip-search/46e07f7c31487c37954165218ad70be2bfb01a89/precomputedFeatures/grp/images.csv.
    2. `clip_data_test/images.csv`: CSV file; columns `iiif_url`, `digital_object`, `localIdentifier`. Located at `./clip_data_test/images.csv`.
- For each input digital object: is it part of a larger dataset?
  - Answer: Both CSV files are indexes pointing to the GRP digital collection hosted by the GTA Archive at ETH Zurich.
- For each input, what specific version/snapshot was used?
  - Answer:
    1. `images-20231206.csv`: Git commit `46e07f7c31487c37954165218ad70be2bfb01a89` of the `sari-iiif-clip-search` repository (snapshot from 2023-12-06).
    2. `clip_data_test/images.csv`: Version present in this repository (no explicit version tag).
- Which output digital objects are produced?
  - Answer: A directory of downloaded JPEG images stored in `./clip_data/images/` (gitignored), with hash-based filenames (e.g., `0000b5716da804138d730e6e937a184144c7ff10.jpg`).
- For each output digital object: what is its type/kind, what does it contain, and where can it be accessed?
  - Answer: Directory of JPEG image files; each file is a digitised image from the GRP collection, downloaded at a resolution of up to 640×640 pixels. Located at `./clip_data/images/`.
- For each output, what guarantees integrity/reproducibility?
  - Answer: The hash-based filenames (`localIdentifier`) serve as content identifiers. The source IIIF URLs in the CSV files enable re-downloading. Note: some IIIF URLs have been renamed (see `rename-iiif/rename-alias-map.yml` for the mapping).
- Is a log file produced?
  - Answer: Yes, `clip_data_test/log.txt` records download errors (HTTP 404/403 responses and retries exhausted).

#### D. Execution resources
- Which software executed this step?
  - Answer: `sari-iiif-clip-search` (Python package for downloading and processing IIIF images).
- For each software used: what version, commit hash, or release tag was used?
  - Answer: Source at `sari-iiif-clip-search` repository; the specific commit/version used is UNKNOWN. Python 3.10.17 (from the traceback in the log).
- For each software used: what is its role and where is the source located?
  - Answer: Downloads images from IIIF endpoints in parallel using `ThreadPoolExecutor`. Source: https://github.com/swiss-art-research-net/sari-iiif-clip-search.
- Which model artifact(s) are used?
  - Answer: N/A
- Which service/API/platform is used?
  - Answer: GTA IIIF Image API server at `https://iiif.gta.arch.ethz.ch/iiif/2/`.
- For each service/API/platform used: what is its type, endpoint, operator/maintainer, role, and version/configuration?
  - Answer: IIIF Image API v2; endpoint `https://iiif.gta.arch.ethz.ch/iiif/2/{image_id}/full/!640,640/0/default.jpg`; operated by the GTA Archive, ETH Zurich; provides the source images for the pipeline.
- What runtime environment details matter?
  - Answer: macOS (Darwin); Python 3.10.17; concurrent downloads via `ThreadPoolExecutor`.

#### E. Agents and responsibility
- Which human/institution actors are responsible for this step?
  - Answer: Matteo Romanello (operator); GTA Archive, ETH Zurich (data provider).
- What role did each actor play?
  - Answer: Matteo Romanello: operator (executed the download). GTA Archive: maintainer of the IIIF server and source images.
- Is there an approver or reviewer for this step's output?
  - Answer: N/A

---

### Step Labelling

#### A. Step identity
- What is the step name?
  - Answer: Labelling
- What is the step type?
  - Answer: Labelling
- What is the short human-readable description?
  - Answer: Manually annotate a sample of 2,183 GRP images into eight visual-type classes using the Roboflow annotation platform.

#### B. Time and context
- From which file(s) can this step's start time be derived?
  - Answer: Roboflow project creation timestamp (project created 2025-01-29 based on `project.list_versions()` output in `train_yolo_classification_model.ipynb`).
- From which file(s) can this step's end time be derived?
  - Answer: `grp-image-classification-dataset-v2/README.roboflow.txt` (dataset exported February 13, 2026).
- Which project does this step belong to?
  - Answer: SARI Image Classification
- Which previous step(s) must complete before this one?
  - Answer: ImageDownload (images must be available to upload to Roboflow).
- Which next step(s) depend on this one?
  - Answer: ModelTraining.

#### C. Inputs and outputs
- Which input digital objects are consumed?
  - Answer: A sample of images from `./clip_data/images/`, uploaded to Roboflow for annotation.
- For each input digital object: what is its type/kind, what does it contain, and where can it be accessed?
  - Answer: JPEG image files from the GRP collection, representing various visual types (drawings, photographs, documents, etc.). Sourced from `./clip_data/images/`.
- For each input digital object: is it part of a larger dataset?
  - Answer: Yes, the annotated sample is a subset of the full GRP image dataset (~131k images).
- For each input, what specific version/snapshot was used?
  - Answer: UNKNOWN (the specific subset selection criteria are not documented in this repository).
- Which output digital objects are produced?
  - Answer: Annotated dataset exported from Roboflow, stored at `./grp-image-classification-dataset-v2/`.
- For each output digital object: what is its type/kind, what does it contain, and where can it be accessed?
  - Answer: Roboflow classification dataset in folder format; 2,183 annotated images split into train (1,515), valid (367), and test (301) sets across 8 classes: collage (105), drawing (476), handwritten document (307), machine-produced document (269), painting (14), photograph (980), print (17), unknown (15). Located at `./grp-image-classification-dataset-v2/`. Also accessible at https://universe.roboflow.com/sariimageannotation/grp-image-classification.
- For each output, what guarantees integrity/reproducibility?
  - Answer: Roboflow dataset version 2 (exported 2026-02-13 9:56am); dataset README files (`README.roboflow.txt`, `README.dataset.txt`) document the export metadata. License: CC BY 4.0.
- Is a log file produced?
  - Answer: N/A (annotation activity is tracked within the Roboflow platform).

#### D. Execution resources
- Which software executed this step?
  - Answer: Roboflow annotation platform (web-based).
- For each software used: what version, commit hash, or release tag was used?
  - Answer: Roboflow platform (SaaS, version not tracked). Roboflow Python SDK used for dataset export.
- For each software used: what is its role and where is the source located?
  - Answer: Roboflow provides the annotation interface, dataset management, and export functionality. URL: https://roboflow.com.
- Which model artifact(s) are used?
  - Answer: N/A
- Which service/API/platform is used?
  - Answer: Roboflow (https://app.roboflow.com); workspace `sariimageannotation`, project `grp-image-classification`.
- For each service/API/platform used: what is its type, endpoint, operator/maintainer, role, and version/configuration?
  - Answer: Cloud-based annotation platform; endpoint: https://app.roboflow.com; operated by Roboflow Inc.; role: image annotation, dataset creation and export; project version 2.
- What runtime environment details matter?
  - Answer: Web browser for annotation; Python 3.12.10 with `roboflow` SDK for programmatic export (see `train_yolo_classification_model.ipynb`).

#### E. Agents and responsibility
- Which human/institution actors are responsible for this step?
  - Answer: Student assistant annotators (Lukas, Mateo, and potentially others); Matteo Romanello (supervision and review).
- What role did each actor play?
  - Answer: Student assistants: annotators. Matteo Romanello: author of annotation guidelines, reviewer, project lead.
- Is there an approver or reviewer for this step's output?
  - Answer: Matteo Romanello (reviewed annotations; annotation guidelines documented at https://docs.google.com/presentation/d/17C8LQP0_mMth9kH3_mz7iJAH4nqMckNmvulq1g-tIYk/).

---

### Step ModelTraining

#### A. Step identity
- What is the step name?
  - Answer: ModelTraining
- What is the step type?
  - Answer: ModelTraining
- What is the short human-readable description?
  - Answer: Fine-tune a pretrained YOLO11n-cls classification model on the annotated GRP dataset for 8-class image-type classification.

#### B. Time and context
- From which file(s) can this step's start time be derived?
  - Answer: `2026-02-13T10:09:06+01:00` (approximate). Derived by subtracting the elapsed training time logged in `runs/classify/train42/results.csv` (1517.9 seconds at epoch 44) from the save `date` embedded in `runs/classify/train42/weights/last.pt`. Epoch 1 finished ~34 seconds after start.
- From which file(s) can this step's end time be derived?
  - Answer: `2026-02-13T10:34:24+01:00`, the save `date` embedded in `runs/classify/train42/weights/last.pt` (written at the end of epoch 44, ~25 minutes total training time). Early stopping triggered at epoch 44 (patience=20, best result around epoch 24). Checkpoint dates carry no timezone; CET (`+01:00`) is assumed. File-system timestamps are not usable: they were reset when the repository was copied (2026-03-24).
- Which project does this step belong to?
  - Answer: SARI Image Classification
- Which previous step(s) must complete before this one?
  - Answer: Labelling (annotated dataset must be available).
- Which next step(s) depend on this one?
  - Answer: Prediction.

#### C. Inputs and outputs
- Which input digital objects are consumed?
  - Answer:
    1. Pretrained model: `yolo11n-cls.pt` (YOLO11 nano classification model, pretrained on ImageNet).
    2. Annotated dataset: `./grp-image-classification-dataset-v2/` (Roboflow export, folder format).
- For each input digital object: what is its type/kind, what does it contain, and where can it be accessed?
  - Answer:
    1. `yolo11n-cls.pt`: PyTorch model weights file; YOLO11 nano classification backbone pretrained on ImageNet. Located at `./yolo11n-cls.pt`. Source: Ultralytics model hub.
    2. `grp-image-classification-dataset-v2/`: Directory with train/valid/test image splits in 8 class folders (2,183 images total). Located at `./grp-image-classification-dataset-v2/`.
- For each input digital object: is it part of a larger dataset?
  - Answer:
    1. `yolo11n-cls.pt`: Part of the Ultralytics YOLO11 model family.
    2. The annotated dataset is a labelled subset of the full GRP image collection.
- For each input, what specific version/snapshot was used?
  - Answer:
    1. `yolo11n-cls.pt`: Ultralytics YOLO11 nano classification model (no specific version tag; compatible with Ultralytics 8.3.40).
    2. Dataset version 2 exported from Roboflow on 2026-02-13.
- Which output digital objects are produced?
  - Answer:
    1. Fine-tuned model: `./yolo11n-cls-grp.pt` (best checkpoint saved from training run `train42`).
    2. Training artifacts: `runs/classify/train42/` (including `results.csv`, `args.yaml`, `model_artifacts.json`, and `weights/best.pt`).
- For each output digital object: what is its type/kind, what does it contain, and where can it be accessed?
  - Answer:
    1. `yolo11n-cls-grp.pt`: PyTorch model weights; fine-tuned YOLO11n-cls model for 8-class GRP image classification. Located at `./yolo11n-cls-grp.pt`.
    2. `runs/classify/train42/results.csv`: CSV with per-epoch training metrics (loss, top-1/top-5 accuracy, learning rates). Located at `./runs/classify/train42/results.csv`.
    3. `runs/classify/train42/args.yaml`: Full training hyperparameter configuration. Located at `./runs/classify/train42/args.yaml`.
    4. `runs/classify/train42/model_artifacts.json`: Model metadata (class names, architecture, training args). Located at `./runs/classify/train42/model_artifacts.json`.
- For each output, what guarantees integrity/reproducibility?
  - Answer: Training configuration fully recorded in `args.yaml` (seed=0, deterministic=true). Model architecture and class names recorded in `model_artifacts.json`. Training metrics per epoch in `results.csv`. The training run name `train42` uniquely identifies this experiment.
- Is a log file produced?
  - Answer: Yes, `runs/classify/train42/results.csv` contains per-epoch metrics. Additional training logs are captured in the notebook output of `train_yolo_classification_model.ipynb`.

#### D. Execution resources
- Which software executed this step?
  - Answer: Ultralytics YOLO library; PyTorch; Python.
- For each software used: what version, commit hash, or release tag was used?
  - Answer: Ultralytics 8.3.40; PyTorch 2.9.1; Python 3.12.10.
- For each software used: what is its role and where is the source located?
  - Answer:
    - Ultralytics: Model training framework for YOLO models. Source: https://github.com/ultralytics/ultralytics. Role: training loop, data loading, augmentation, evaluation.
    - PyTorch: Deep learning backend. Source: https://pytorch.org.
    - Roboflow SDK: Used to download the annotated dataset programmatically. Source: https://github.com/roboflow/roboflow-python.
- Which model artifact(s) are used?
  - Answer: Input: `yolo11n-cls.pt` (pretrained). Output: `yolo11n-cls-grp.pt` (fine-tuned, saved from `runs/classify/train42/weights/best.pt`).
- Which service/API/platform is used?
  - Answer: Roboflow API (for dataset download during notebook execution).
- For each service/API/platform used: what is its type, endpoint, operator/maintainer, role, and version/configuration?
  - Answer: Roboflow API; endpoint: `https://api.roboflow.com`; operator: Roboflow Inc.; role: dataset download and versioning.
- What runtime environment details matter?
  - Answer: macOS (Darwin) on Apple M4 Pro; GPU acceleration via MPS (Metal Performance Shaders); Python 3.12.10; image size 640×640; batch size 16; 100 max epochs with patience 20 (early stopped at epoch 44). Training hyperparameters fully documented in `runs/classify/train42/args.yaml`.

#### E. Agents and responsibility
- Which human/institution actors are responsible for this step?
  - Answer: Matteo Romanello.
- What role did each actor play?
  - Answer: Author of the training notebook, model trainer, and operator.
- Is there an approver or reviewer for this step's output?
  - Answer: Matteo Romanello evaluated the model (93.69% top-1 accuracy, 99.67% top-5 accuracy on the test split) as documented in the notebook evaluation cell.

---

### Step Prediction

#### A. Step identity
- What is the step name?
  - Answer: Prediction
- What is the step type?
  - Answer: Prediction
- What is the short human-readable description?
  - Answer: Apply the fine-tuned YOLO classification model to the full GRP image dataset (~131k images) to produce per-image class predictions.

#### B. Time and context
- From which file(s) can this step's start time be derived?
  - Answer: No exact start time is recorded. Earliest possible start (`begin_of_the_begin`): `2026-02-13T10:47:26+01:00`, the save `date` embedded in the final model `models/yolo11n-cls-grp.pt`, which the prediction run used.
- From which file(s) can this step's end time be derived?
  - Answer: No exact end time is recorded. Latest possible end (`end_of_the_end`): `2026-03-24T10:14:33+01:00`, the date of git commit `a819865`, which first added `data/output/predictions_test.csv`. File-system timestamps of `predictions_test.csv` are not usable: they were reset when the repository was copied. Each classification inherits this time-span from the prediction run.
- Which project does this step belong to?
  - Answer: SARI Image Classification
- Which previous step(s) must complete before this one?
  - Answer: ModelTraining (trained model must be available); ImageDownload (images must be available locally).
- Which next step(s) depend on this one?
  - Answer: None (final pipeline step; predictions are consumed downstream by SARI knowledge graph integration processes).

#### C. Inputs and outputs
- Which input digital objects are consumed?
  - Answer:
    1. Fine-tuned model: `./yolo11n-cls-grp.pt`.
    2. Image dataset: `./clip_data/images/` directory containing the full GRP image collection.
- For each input digital object: what is its type/kind, what does it contain, and where can it be accessed?
  - Answer:
    1. `yolo11n-cls-grp.pt`: PyTorch model weights; fine-tuned YOLO11n-cls for 8-class image classification. Located at `./yolo11n-cls-grp.pt`.
    2. `clip_data/images/`: Directory of JPEG images (~131k files) from the GRP collection. Located at `./clip_data/images/` (gitignored).
- For each input digital object: is it part of a larger dataset?
  - Answer: The image directory is the full downloadable GRP image dataset (as indexed by `images-20231206.csv`).
- For each input, what specific version/snapshot was used?
  - Answer:
    1. `yolo11n-cls-grp.pt`: Fine-tuned model from training run `train42`.
    2. Image dataset: Snapshot downloaded from IIIF server (indexed by `images-20231206.csv`, git commit `46e07f7c`).
- Which output digital objects are produced?
  - Answer:
    1. `predictions_test.csv`: Main output with classification predictions (~131,656 rows).
    2. `predictions_test.csv.skipped.csv`: Log of images that could not be processed (2 entries).
- For each output digital object: what is its type/kind, what does it contain, and where can it be accessed?
  - Answer:
    1. `predictions_test.csv`: CSV file; columns: `absolute_image_path`, `image_file_name`, `top1_class`, `top1_confidence`, `top2_class`, `top2_confidence`, `top3_class`, `top3_confidence`. One row per successfully classified image. Located at `./predictions_test.csv`.
    2. `predictions_test.csv.skipped.csv`: CSV file; columns: `absolute_image_path`, `error`. Records images skipped due to corruption or decoding errors. Located at `./predictions_test.csv.skipped.csv`.
- For each output, what guarantees integrity/reproducibility?
  - Answer: The inference script (`run_dataset_classification.py`) supports resume functionality, ensuring all images are eventually processed. The model file and script are versioned in this repository. Deterministic ordering (images sorted alphabetically) ensures reproducible row order given the same input.
- Is a log file produced?
  - Answer: Yes, `predictions_test.csv.skipped.csv` logs images that failed during inference with error messages.

#### D. Execution resources
- Which software executed this step?
  - Answer: `run_dataset_classification.py` (custom Python script); Ultralytics YOLO library; tqdm.
- For each software used: what version, commit hash, or release tag was used?
  - Answer: Ultralytics 8.3.40; Python 3.12.10; PyTorch 2.9.1; tqdm (version UNKNOWN).
- For each software used: what is its role and where is the source located?
  - Answer:
    - `run_dataset_classification.py`: Orchestrates batch inference, handles resume, fault tolerance, and output writing. Located at `./run_dataset_classification.py`.
    - Ultralytics: Provides the `YOLO` model class and `predict()` method. Source: https://github.com/ultralytics/ultralytics.
    - tqdm: Provides progress bar. Source: https://github.com/tqdm/tqdm.
- Which model artifact(s) are used?
  - Answer: `./yolo11n-cls-grp.pt` (fine-tuned YOLO11n classification model, 1,536,272 parameters, 3.2 GFLOPs).
- Which service/API/platform is used?
  - Answer: N/A (inference runs entirely locally).
- For each service/API/platform used: what is its type, endpoint, operator/maintainer, role, and version/configuration?
  - Answer: N/A
- What runtime environment details matter?
  - Answer: macOS (Darwin) on Apple M4 Pro; MPS device for inference; batch size 64 (default); supported image extensions: `.jpg`, `.jpeg`, `.png`, `.bmp`, `.webp`, `.tif`, `.tiff`.

#### E. Agents and responsibility
- Which human/institution actors are responsible for this step?
  - Answer: Matteo Romanello.
- What role did each actor play?
  - Answer: Author of the inference script and operator of the prediction run.
- Is there an approver or reviewer for this step's output?
  - Answer: UNKNOWN
