# GRP Image Classification — run `just` to list recipes.
#
# Override stored defaults with --set:
#   just --set limit 20 provenance
#   just --set jsonld_out data/output/foo.jsonld provenance
#   just rdfxml data/output/foo.jsonld data/output/foo.rdf
#
# Convert the pipeline provenance sample to RDF/XML:
#   just rdfxml-sample
#
# Sample (first 500 predictions → JSON-LD + RDF/XML):
#   just provenance-sample
#
# Full predictions CSV → JSON-LD → RDF/XML:
#   just provenance-all

set dotenv-load := true

python := "python"

predictions_csv := "data/output/predictions_test.csv"
images_csv      := "clip_data/images.csv"
template_jsonld := "provenance/pipeline_provenance_sample.jsonld"
template_rdfxml := "provenance/pipeline_provenance_sample.rdf"
jsonld_out      := "data/output/provenance.jsonld"
rdfxml_out      := "data/output/provenance.rdf"
training_run    := "train42"
limit           := ""

sample_limit  := "500"
sample_jsonld := "data/output/provenance_500_sample.jsonld"
sample_rdfxml := "data/output/provenance_500_sample.rdf"

model    := "models/yolo11n-cls-grp.pt"
data_dir := "clip_data"

# List available recipes
default:
    @just --list

# Install Python dependencies
install:
    {{ python }} -m pip install -r requirements.txt

# Generate JSON-LD provenance for predictions (optional: output, limit)
provenance output=jsonld_out limit=limit:
    {{ python }} scripts/generate_prediction_provenance.py \
        --predictions-csv "{{ predictions_csv }}" \
        --images-csv "{{ images_csv }}" \
        --template-jsonld "{{ template_jsonld }}" \
        --output "{{ output }}" \
        --training-run "{{ training_run }}" \
        {{ if limit != "" { "--limit " + limit } else { "" } }}

# Convert JSON-LD provenance to RDF/XML and validate triples
rdfxml input=jsonld_out output=rdfxml_out:
    {{ python }} scripts/convert_jsonld_to_rdfxml.py \
        --input "{{ input }}" \
        --output "{{ output }}"

# Convert provenance/pipeline_provenance_sample.jsonld to RDF/XML
rdfxml-sample: (rdfxml template_jsonld template_rdfxml)

# First 500 predictions → JSON-LD + RDF/XML (committed sample paths)
provenance-sample: (provenance sample_jsonld sample_limit) (rdfxml sample_jsonld sample_rdfxml)

# Full predictions CSV → JSON-LD → RDF/XML
provenance-all: provenance rdfxml

# Classify images with the fine-tuned YOLO model
classify output=predictions_csv:
    {{ python }} scripts/run_dataset_classification.py \
        --model "{{ model }}" \
        --data-dir "{{ data_dir }}" \
        --output "{{ output }}"

# Mermaid provenance diagram for one classificatory-status entity
diagram entity_id output="":
    {{ python }} scripts/generate_provenance_diagram.py \
        "{{ jsonld_out }}" \
        "{{ entity_id }}" \
        --wrap-md \
        {{ if output != "" { "-o \"" + output + "\"" } else { "" } }}
