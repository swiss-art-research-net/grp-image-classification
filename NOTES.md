## Apply YOLO model to the entire dataset

Write a Python script to apply the trained YOLO model (at `./yolo11n-cls-grp.pt`) to the entire GRP dataset that can be found here `./clip_data`.

The script should have the following characteristics:
- Have a command-line interface
- Process images by batches; the batch size should be configurable
- Display a progress bar (use the `tqdm` library) 
- Offer the possibility to stop the processing and to resume it from where it was left
- the output file should be a tabular file (csv or parquet) containing the following information:
    - absolute image path
    - image file name
    - top-1 class
    - confidence score for top-1 class
    - top-2 class
    - confidence score for top-2 class
    - top-3 class
    - confidence score for top-3 class

## Create provenance information for this pipeline

Create a JSON-LD provenance file describing the grp image classification pipeline according to the formats and templates of PROVOLONE, documented at https://raw.githubusercontent.com/swiss-art-research-net/docs/refs/heads/master/docs/ordea-report/4_provolone_recipes.md.

The file `provenance/pipeline_provenance_questionnaire.md` contains detailed information about the pipeline; you should use information in this file to create the JSON-LD provenance graph. 

For now, document only the model training and prediction steps; for the image classification predictions, document the provenance of the first 10 rows in the file `predictions_test.csv`.  

## Write a script to produce provenance metadata for all predictions

```
# Query to retrieve the DigitalObject URI given the IIIF manifest base URI
# SPARQL endpoint: https://researchportal.gta.arch.ethz.ch/sparql

PREFIX la:     <https://linked.art/ns/terms/>
PREFIX crmdig: <http://www.ics.forth.gr/isl/CRMdig/>

SELECT ?do
WHERE {
  ?do a crmdig:D1_Digital_Object ;
      la:digitally_available_via/la:access_point <https://iiif.gta.arch.ethz.ch/iiif/2/208619> .
}
```