### HFT for top-down/bottom-up visual processing continued

This is a sort of continuation of the [Gordon et al 2017](Gordon%20et%20al%202017.md) paper, with a focus on the signaling of top-down expectation and bottom-up stimulus processing.

Similar to that paper, HFT was used with SWIFT and a cosmetic tag. Three experiments were conducted:

- Exp 1: Observing a sequence of house/face stimuli and either (A) pressing a button when a specific cued stimulus repeated itself a fixed number of time (B) pressing a button when a memorized pattern such as house-face-face-house was violated during the trial sequence
- Exp 2: Observing the same stimuli but asked to count the number of houses or faces while possibly performing another cognitively demanding task. Notable in that the SWIFT frequency was either 0.8 Hz or 1.2 Hz (Exp 1 is exclusively 1.2 Hz). Images within a trial could be "attended" or "unattended" depending on whether it was being actively counted. Some cycles would contain noise replacements for the face or house image (75-80% of cycles) to make the task hard.
- Exp 3: Old data from the [Gordon et al 2017](Gordon%20et%20al%202017.md) paper in which subjects counted faces/houses as in task 2, however in this case the proportion of one category to the other was varied systematically.
	- This differs from Exp 2 in that the faces/houses appear without a doubt in each cycle, and the only difference is whether or not it's the attended category.
	- Because in this old data expectation and attention were linked (the higher frequency category was always the attended one) Exp 2 was conducted to dissociate the frequency from the attended category via drop cycles

Multi-spectral phase coherence was used to quantify the degree to which a given intermodulation frequency was driven by the stimulus phase (MSPCstim) or the neural response phase of the primary tag frequencies (MSPCres). This can be thought of as whether or not the IM frequency is primarily driven by the stimulus itself, or whether it instead is driven by a circuit that is processing that stimulus.

Key findings:
- **Exp 1:** Expectation increased coherence with stimulus signals as compared to neural signals in IM components (unexpected stimulus trials showed lower coherence to stimulus than expected). This effect of expectation of a stimulus in the memorized sequence did not change coherence to neural signals.
- **Exp 2:** Attention to the image category (house/face) increased phase coherence to neural phase (higher than unattended images) and did not affect coherence to stimulus phase.
- **Exp 3**: A linear mixed-effects model showed significant interaction between expectation and attention for coherence to neural phase, but not to stimulus phase.

If we think of the IM components as signals of integration of top-down expectation and bottom-up attention, as discussed in the [Gordon et al 2017](Gordon%20et%20al%202017.md), then we can make sense of the results as follows:

Increasing stimulus coherence in the IM components with expectation means that the bottom-up stimulus information is becoming more heavily weighted (and correspondingly less weight is given to the top-down predictive signals) in strongly-predicted trials.

Conversely the decrease of phase coherence with neural tag frequencies in IM components when the image category is not attended indicates that attention to a category enhances the effect of those same predictive signals on the IM components and visual processing that underlie them.

All-in-all a quite cool paper, but I'd have to dig much, much deeper into the stats and methods to be sure of the veracity of the claims.