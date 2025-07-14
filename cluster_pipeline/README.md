# How to run this pipeline for a new subject via `mne-bids-pipeline`

## Step 1: Adding data to BIDS
Ingest subject raw MEG data into the BIDS dataset using `mne-bids`. You will need to take the raw data into the dataset via the following command:

```bash
mne_bids raw_to_bids --bids_root PATH/TO/BIDS/ROOT --subject_id SUBJECT --session_id SESSION --task TASK
```

This will add the scan to the BIDS dataset and all appropriate `.tsv` and `.json` files. You can also specify the acquisition if you have separate ones etc. See the [full documentation for mne_bids CLI](https://mne.tools/mne-bids/stable/generated/cli.html#mne-bids-raw-to-bids).

Next you will need to convert the DICOM file to the standard format for MNE using [`dcm2bids`](https://unfmontreal.github.io/Dcm2Bids/3.2.0/tutorial/first-steps/#populating-the-config-file), which can be done with the following command in the syntax dataset:

```bash
dcm2bids -d PATH/TO/DICOM.zip -p SUBJECT -c path/to/bids/root/code/folder --auto_extract_entities
```

This will result in either a temporary directory in your current working dir which contains `sub-SUBJECT` or a new folder in the BIDS root for your subject where the converted `.nii.gz` file is. 

If the file is in a temporary directory, go ahead and move the converted image and any `.json` files to the BIDS directory for that subject/session.

Next we will need to write the calibration and crosstalk files, if you have them, to the subject directory. MNE-BIDS supports this luckily:

```bash
mne_bids calibration_to_bids --file PATH/TO/CALFILE.dat --bids_root PATH/TO/BIDS/ROOT --subject_id SUBJECT --session_id SESSION
mne_bids crosstalk_to_bids --file PATH/TO/CROSSTALK.fif --bids_root PATH/TO/BIDS/ROOT --subject_id SUBJECT --session_id SESSION
```

Empty-room data must now be written to the BIDS dataset as well. You will add this data to a dummy subject called "emptyroom" (yes, I know, but this is the canonical way to do it in bids). The session ID will be a ISO-formatted date without any separators, e.g. March 5 2025 would become `20250305`.

```bash
mne_bids raw_to_bids --bids_root PATH/TO/BIDS/ROOT --subject_id emptyroom --session_id ISODATE
```

Now you are ready for the pipeline after one final step.

## Step 1.5: Adding in mini-block labels and correcting offset between triggers and photodiode

The initial step before ingesting data into the BIDS structure will be to correct the trigger-based events present in the file. The triggers sent correspond to the onset of every word pair or word within a mini-block, and we will need to label the initial stimulus in each mini-block based on this. Additionally there is a fixed offset between the time at which triggers arrive and when the display shows the stimulus in question.

We will also need to manually label the bad periods of the recording, including breaks and those
points where the subject moved too much.

The script below will handle the triggers and mini-block labels, while providing the user an opportunity to mark bad periods in the recording:

```bash
python ./scripts/analysis/01_miniblock_events.py --bids_root PATH/TO/BIDS/ROOT --subject_id SUBID_HERE --session_id SESSID_HERE --task TASKNAME_HERE --ev-offset -12 --overwrite-fif --overwrite-tsv --miniblock-events --show-channels --interactive --stepfix
```

A brief explanation of the arguments:
 - The `bids_root`, `subject_id`, `session_id`, `task`, and (not shown) optional `run` and `proc` parameters determine where in the BIDS structure the the raw data to be modified will be loaded from
 - The `ev-offset` parameter is the number of samples to shift the trigger signals before labelling events. This is because of the fixed delay between trigger delivery and when the stimulus is drawn. This value when sampling at 2 KHz is usually between -12 and -14
 - The `overwrite` flags tell the script it is ok to overwrite the BIDS data for that session with the new event labels and any new bad-labelled periods
 - the `show-channels` and `interactive` flags tell the script to launch an interactive viewer to inspect the triggers and label bad periods in the data.

Additional parameters are possibly necessary, and the user should consult the script file to see what is available.

After the script is launched, you should first check that the event labels exactly match the photodiode detection of stimulus onset, as reported by the upper-right corned square on the display. If they do not match exactly, quit the program (type N in the terminal or use CTRL + C) and change the `ev-offset` parameter so it does. Once the labels match the photodiode, you must then use the interactive annotation tool (pencil icon) to label periods of the recording where the data was bad (e.g. breaks or when the subject moved too much). **It is important to use a label name beginning with `BAD_`, as this is what the pipeline will use to exclude periods**.

After this, confirm the data are correct by typing `y` or `yes` in the terminal and hitting enter. The modified triggers should be saved.


## Step 2: FreeSurfer reconstruction via pipeline

Now you'll need to run the reconstruction step of the pipeline before aligning the fiducials. The pipeline batch script `freesurfer_sub.sh` will do this for you on a SLURM cluster, or alternatively you can run the following command:


```bash
mne_bids_pipeline --config PATH/TO/CONFIG/FILE.py --bids_root PATH/TO/BIDS/ROOT --subject_id SUBJECT --steps freesurfer
```

You must either define your own config file or use the one for the syntax project. 

This will create a FreeSurfer subjects directory in `bids_root/derivatives/freesurfer` which will be used going forwards.

Once the reconstruction is done, you should have a full folder tree of outputs called `sub-SUBJECT` in the above directory.

## Step 3: Coordinate frame alignment (fiducials)

You'll now need to correct the fiducials for the MRI image to match where they were set in the MEG recording. You will do this via the MNE coregistration GUI in Python using the script associated with this step:

```bash
python ./scripts/analysis/03_coreg_landmarks.py --subject SUBJECT --session SESSION --task TASK --bids_root PATH/TO/BIDS/ROOT
```

Note that this step **must be run away from the cluster**. This is because it requires a GUI to operate, and user input.

At this point correct the fiducial points automatically generated by FreeSurfer to make sure they accurately line up with the LPA/RPA/Nasion on the subject surfaces. This is critical, as the head transform will be computed by the pipeline and saved based on these points and the head traces!

Once you have corrected the positions, run the fitting yourself ("Fit Fiducials" in the right pane) and save the transform to **The file location and name pointed out by the command line**. It may be several lines up due to MNE verbosity, so be sure to scroll.

Once you've saved the transform file, close the viewer and the script will run to update the fiducials saved in the BIDS dataset.

With this your MRI data should be prepared for the final steps involving source reconstruction!

## Step 4: Preprocessing the data

> This step and onwards can be run on the cluster. The previous steps involved preparing the data in BIDS format for the pipeline, and are best run locally, but from here on out lots of compute will be involved. **Make sure to copy any new subject data to the cluster before running!**.

> A small bash utility script I wrote is in this folder, called `pipeline-submit`, which will allow for submitting multiple SLURM jobs such that one job will only begin if the previous one completes successfully. See the bottom of this page for details on how to use.

Now we will apply preprocessing steps to the data such as maxfiltering and filtering out line noise. 

### Quality checks, head position, Maxwell filtering, and ICA
First we will run data quality checks and compute the head position for maxfilter. These steps are two separate batch files, `01_dataquality_sub.sh` and `02_headpos_sub.sh`, which should be run in that order. The head position in particular takes a very long time to run.

Once you have the head position figured out, you can then run the maxfilter step in `03_maxfilter_sub.sh` to perform the signal subspace correction on your data. Like the head position calculation, this is a very slow operation. Particularly if you have a long recording.

You can now, after doing the filtering, perform a final notch filter and low/high-pass on the data (as specified in the pipeline config file). This is done together with the ICA fitting for your data, which will fit ICA components that you can then choose to accept/reject as EOG/ECG artifacts. The file `04_ica_sub.sh` performs all of these steps.

### Manually selecting ICA components to reject

**At this point, some manual intervention is required.** You should have been reading the log outputs from each of these steps as you ran them, and you will see that the last step will automatically mark some ICA components as bad due to artifacts. You will need to manually check these in the report file that the pipeline outputs. Note which components are truly artifacts, and then open up the `...proc-ica_components.tsv` file in `bids_root/derivatives/sub-SUBJECT/ses-SESSION/meg/`. Here you will go through the components one-by-one and make sure you agree with what it automatically included/excluded.

**NB: For recordings to date a maximum of 3 ICA components were excluded as artifacts to preserve the data. Please apply this policy going forward, or recompute the pipeline for existing subjects from this step onwards if you choose to reject more.**

Once you're happy with the components to regress out, save the changes to this file. You can now move on!

## Step 5: Regressing out components, epoching, and producing clean data

We will now make epochs from the data (again, check your pipeline config file to be sure your events are correct) and regress out the ICA components. The covariance matrix of the sensors will also be computed from empty-room data. **Make sure you imported the empty-room data correctly in the first step.**

This is done by the `05_ica_regress.sh` batch file, while will run the pipeline steps. This final operation will produce the `proc-clean_raw.fif` and `proc-clean_epo.fif` files needed for analysis by removing the components and doing any peak-to-peak channel rejection.

##  Step 6: Source space computation (forward/inverse models)

We will now compute the forward and inverse solutions for the data. This is also handled by the pipeline, provided everything to date has been run correctly. The script `06_source_space.sh` will run the appropriate steps for the subject.


## Step 7/8: Source and Sensor SNR computations and plots

Finally, we can run custom scripts to both compute the signal-to-noise ratio (SNR) in each space as well as plot the resulting per-subject data. Step 7 is the sensor space, and will be computed via `07_sensor_snr.sh` which saves outputs to a pickle file in the derivatives directory for `mne-bids-pipeline`, while step 8 is the source space and performs the same saving. 

Note that **the source SNR script will run the process twice, in one case morphing the subject's head surfaces to match the `fsaverage` template for group means**.

Plotting scripts are `07a_sensor_snr_plots.sh` and `08a_source_snr_plots.sh`, and will produce plots of the SNR saved to **a directory of your choice**. These scripts each take an argument `--plotpath` which points to where the images will be saved. The default is specific to my cluster directory structure, so you will need to add this flag and specify where you would like these plots to be produced in your own file system.

## Step 9: Group means and plots

Once a number of subjects have been run, `09_group_means.sh` will perform averages across all subjects for the frequency tag mini-blocks, as well as averages for each condition. The script averages for both the sensor and source space and saves these averaged data, and also will plot the data. **Unlike before, this step requires the `--plotpath` argument for saving both the data and the plots. Make sure to include it just as you did in step 7/8!**

At this point a full set of per-subject SNR data, as well as group mean SNR data, in the source and sensor spaces should be available for further analysis.

## Tips on running cluster pipelines

Each one of the batch scripts in this folder can be submitted as a separate job to the cluster. When running the scripts you must have an environment variable that specifies the subject and task that are being processed. This can be done via the `export` command in bash:

```bash
export PIPELINE_SUB=01 PIPELINE_TASK=syntaxIM
sbatch ./myscript.sh
```

The exported variables will then be passed along to the job. Because this pipeline involves several scripts that can be run sequentially, but are dependent on the outputs of one another, I have built a simple command line utility for doing the above and specifying multiple dependent steps:

```bash
pipeline-submit -e PIPELINE_SUB 01 -e PIPELINE_TASK syntaxIM -s ./myscript1.sh -s ./myscript2.sh
```

The above command ensures that both `myscript1.sh` and `myscript2.sh` will be given the correct environment variables, and also arranges for the job of `myscript2.sh` to run if and only if the job running `myscript1.sh` completes successfully.

The `pipeline-submit` command can take an arbitrary number of steps to run in sequence, so long as each step is separated by a new `-s` flag:

```bash
pipeline-submit -s ./myscript1.sh -s myscript2.sh -s myscript3.sh
```

In this case no environment variables would be exported, and the jobs would follow the order `myscript1.sh` --> `myscript2.sh` --> `myscript3.sh` in a fail-stop manner. If two scripts can be run in parallel to one another with no dependencies, they only need to follow the same `-s` flag:

```bash
pipeline-submit -s ./myscript_1a.sh ./myscript_1b.sh -s ./myscript2.sh
```

In the above case `myscript_1a.sh` and `myscript_1b.sh` would run at the same time, and would both need to complete before `myscript2.sh` could launch. If either job failed, the dependency wouldn't run.

### Running the syntaxIM pipeline

Given the above, it's quite easy to run the syntax pipeline in sequence and almost all steps can be submitted together. **It is important to note, however, that you must only run up to Step 4 at once, so the ICA components to remove can be selected and marked before going further!**. As long as this is obeyed, the pipeline can be run in two halves. Additionally, the FreeSurfer reconstruction step can be run in parallel to steps 1-4.