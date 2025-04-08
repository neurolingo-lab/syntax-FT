The data processing pipeline is fully automated for the core, common steps leading to source space analysis. This majority of this pipeline heavily uses the `mne-bids-pipeline` tool, which helps automate everything so long as the data are in BIDS compatible format.

The pipeline can be chunked into several discrete processes, with each of those having steps within of processing the data:

```mermaid
flowchart TB
	subgraph prepro[Preprocessing]
		direction TB
		bads[Find bad channels] --> headpos[Estimate cHPI head position]
		headpos --> maxfilt[Maxwell filter signal]
		maxfilt --> ffilt[Filter line noises and cap frqeuencies]
		ffilt --> artifact[Remove artifacts based on ICA]
		artifact --> epoch[Epoch data and remove bad epochs]
	end
	
	subgraph sensor[Sensor space]
		direction TB
		evoked[Condition evoked] --> decode[Decode conditions pairs]
		evoked --> timefreq[Time-frequency decomp]
	end
	
	recon[FreeSurfer reconstruction]

	subgraph source[Source space]
		direction TB
		bem[BEM surfaces] --> bemsol[BEM solution]
		bemsol --> sourcespace[Source-space]
		sourcespace --> forward[Forward solution]
		forward --> inverse[Inverse solution]
	end
	prepro --> noisecov[Noise-covariance est.]
	noisecov --> sensor
	recon --> source
	sensor --> source
```

Each step in the pipeline saves intermediate results in the BIDS format for use in subsequent analyses. Those subsequent analyses will be detailed later on here once needed.