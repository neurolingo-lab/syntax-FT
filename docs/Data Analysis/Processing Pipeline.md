The data processing pipeline is fully automated for the core, common steps leading to source space analysis. This majority of this pipeline heavily uses the `mne-bids-pipeline` tool, which helps automate everything so long as the data are in BIDS compatible format.

The pipeline can be chunked into several discrete processes, with each of those having steps within of processing the data.

NB: Green segments run on the cluster, while blue segments run on a local machine. Red substeps indicate user intervention in the cluster pipeline is required.

```mermaid
---
config:
  theme: redux
  layout: elk
---
flowchart LR
 subgraph bids[Bids-ification of data]
    direction TB
    dcm2bids[Dicom to BIDS nii gz] --> mnebids[MNE-BIDS raw data conv]
 end
 subgraph prepro["Preprocessing"]
    direction TB
        headpos["Estimate cHPI head position"]
        bads["Find bad channels"]
        maxfilt["Maxwell filter signal"]
        ffilt["Filter line noises and cap frqeuencies"]
        ica["Compute ICA components and flag"]
        mansel("Manually reject ECG/EOG ICs")
        icfilt["Filter out selected ICs"]
        epoch["Epoch data and remove bad epochs"]
  end
 subgraph coreg["Co-registration"]
    direction TB
        align["cHPI position alignment"]
        reconall["Freesurfer recon-all"]
  end
 subgraph sensor["Sensor space"]
    direction TB
        snr["Compute SNR in channel PSDs"]
        evoked["Per-condition evoked"]
        plotsnr["Plot grand-mean SNR and per-channel"]
  end
 subgraph source["Source space"]
    direction TB
        bemsol["BEM solution"]
        bem["BEM surfaces"]
        sourcespace["Source-space"]
        forward["Forward solution"]
        inverse["Inverse solution"]
  end
    bads --> headpos
    headpos --> maxfilt
    maxfilt --> ffilt
    ffilt --> ica
    ica --> mansel
    mansel --> icfilt
    icfilt --> epoch
    reconall --> align
    evoked --> snr
    snr --> plotsnr
    bem --> bemsol
    bemsol --> sourcespace
    sourcespace --> forward
    forward --> inverse
    bids --> prepro
    prepro --> noisecov["Noise-covariance est."]
    prepro --> sensor
    noisecov --> source
    coreg --> source
     mansel:::userintStep
     prepro:::clusterSteps
     noisecov:::clusterSteps
     source:::clusterSteps
     coreg:::clusterSteps
     sensor:::localSteps
     bids:::localSteps
    classDef localSteps fill:#d1fdff
    classDef clusterSteps fill:#b9ffb2
    classDef userintStep fill:#ff4d48
    style align fill:#ff4d48

```

Each step in the pipeline saves intermediate results in the BIDS format for use in subsequent analyses. Those subsequent analyses will be detailed later on here once needed.
