# Functional characterisation of letter-specific responses in time, space and current polarity using magnetoencephalography

This is an older study from Laura Gwilliams specifically examining the ability of MEG source localization to find responses along the gradient of low-level to high-level word processing that exists in the visual processing system.

The main motivation of the study was to:
- Assess whether MEG source methods can find the gradient of text-specific responses established in other studies (Tarkiainen et al 1999, Solomyak and Marantz 2009, Dehaene et al 2002, Thensen et al 2012)
- Determine whether constrained dipole orientations in MNE can affect the detection of these responses
- Test whether the methods for source localization are suitable for cross-subject designs

Notably they didn't use anatomical MRI data but rather the FreeSurfer average brain for source localization. It makes the study a little less applicable to our questions, but is still super valuable for methods.

## Goals

##### Regions of interest

The study wanted to look at the response of regions associated with "Type Two" response to words, as per Tarkiainen et al 1999, particularly in VWFA, letter-form area, and word-form area. They aimed to characterize location, timing, and functionality of these areas.

#### Developing a localizer for early letter-specific activity

The authors also wanted to adapt the Tarkiainen paradigm in English for a VWFA localizer, and to build a tool for finding fROIs for early letter-specific activity to later see whether neural populations are shared between parts of the system. The latter goal aimed at adapting the Solomyak and Marantz 2009 study's paradigm.

#### Determining the best source methods for studying the system

The paper focuses a lot on whether to use dipole-constrained source models that allow for signed activation values at locations on the cortical surface. They claim that the signed source estimates will allow for better discrimination of neural responses compared to unconstrained and unsigned estimates. They use a cluster-based permutation test to compare activity in different task conditions.

## Task & Methods

#### Tarkiainen replication

16 participants who were native english speakers, right handed, average age 24, 6/10 F/M were shown english adaptations of the original stimuli:

![1-s2 0-S105381191600166X-gr1](https://github.com/user-attachments/assets/3d8b866d-1e56-4f4b-b67c-3116c28165c3)

A combination of 4 noise levels x 4 categories + 4x symbol sequences at the lowest noise level were used, for a total of 20 stimulus possibilities. The categories included single-element letters, two-element english syllables, four letter english words, and a blank with pure noise. Symbol equivalents for each element number were presented only at the lowest noise as a control.

An abridged localizer using only the four-element and one-element items with highest and lowest noise levels was also tested. Only the replication subjects were, as in the original Tarkiainen study, asked to occasionally repeat the words/syllables/letters they saw verbally.

Replication: Stimuli were organized into blocks of category (0/1/2/4 elements) with symbols mixed in, and the stimuli were presented for 60ms with a 2s ITI. 5% of the trials had the query for a report of the stimulus, minus the pure noise block. Lasted around 40m

Abridged localizer: Stimulus order fully randomized across six blocks of presentation. Participants shown the same duration/ITI as the original experiment, each block lasting around 60s and lacking an overt task. Took around 6m total.

#### S&M Replication

This bit replicated a study consisting of a lexical decision making task with the following categories:

<img width="685" alt="Screenshot 2025-05-06 at 13 25 46" src="https://github.com/user-attachments/assets/ca1239da-f8ae-4015-90a0-0ece0000b387" />

with 265 real words and 265 non-words in which subjects would need to respond whether a stimulus was a word or not, with no feedback.

#### Analysis

Preprocessing:
- CALM (Adachi et al 2001) used for noise reduction
- Low-pass 40Hz filter
- Epoched from 200ms pre-stimulus-onset to 800ms post-stimulus-onset
- Rejected trials with 2000 fT PtP threshold, along with manual inspection
- Averaged epochs across condition for evoked
- Digitized head shape co-registered to FSaverage template data for source localization

Source space:
- ico-4 (icosahedron, 4mm spacing) source space created w/2562 vertices per hemi
- Boundary Element Model (BEM) computed at each vertex per hemi
- Inverse computed from forward and grand average activity across trials (across subjects)
- Two options for inverse orientation: signed fixed orientation (dipoled perpendicular to cortical surface), unsigned free orientation (allows dipole at each source to orient anywhere)

Produced a dynamic statistical parameter map (dSPM) with arbitrary units.

Source analysis:
- ran spatio-temporal permutation cluster tests over the time-windows (80–130 ms, 130–180 ms) and regions (occipital and temporal lobes) reported in Tarkiainen et al.'s results (tests used methodology from Maris and Oostenveld 2007)
- Regression analysis of source estimates against trial conditions + nuisance variables performed on the significant vertices from previous step, for every single time point. If a cluster in space of 10 vertices were significant (t test) for more than 20ms the t-values were summed resulting in a cluster-level statistic. That cluster-level value was compared against 10k permutations of the data for significance. Schematic below:

![1-s2 0-S105381191600166X-gr2](https://github.com/user-attachments/assets/45057b90-b795-4f40-8686-53f286b2edd1)

#### Results

###### Tarkiainen replication

Type One (not letter sensitive) response replicated, with response scaling according to noise (24 = max gaussian noise)
Type Two response (letters over symbols) response replicated

![1-s2 0-S105381191600166X-gr3](https://github.com/user-attachments/assets/2fe1aa92-df6c-470e-b868-a9325db2e26d)

###### Abridged localizer

No figure but the abridged localizer also seems to have produced good results in the data

###### S&M Replication

Didn't dive too deep into this yet but seems to have found a graded posterior-to-anterior response to varying degrees of complexity in the stimuli, supporting prior work suggesting a hierarchy of complexity in responses to words.

###### Signed vs Unsigned (Constrained vs Unconstrained) source estimates

They consistently found signed estimates to be more sensitive to the task structure and variables and provide a better localizer
