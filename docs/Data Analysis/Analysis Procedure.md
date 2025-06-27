# Rough outline of planned analyses

### Metrics of choice

FT Response:

Two options are seen in the literature. The SNR ($\frac{\mu_i}{\mu_{i-k, \dots , i-1, i+1,  \dots , i+k}}$, or the mean at bin $i$ divided by the mean of the neighboring bins with a possible skipped set of neighbors) and the Z-scored baseline-corrected metric used by Lochy et al 2015. The latter metric is not commonly used at all, and I've only seen it in the Olaf Hauk reproduction of that work with English stimuli and source localization. Based on the prevalence we will use the SNR.

Significant difference of FT response:

Cluster-based permutation tests are very well-established in the literature and provide a good way of comparing the difference of two sets of epochs against a bootstrapped null distribution. We will use these tests to establish where we can see significant differences **between different conditions for the same FFT bin, either a tag or IM**.

### Visual Word Form Area (VWFA)

- In one-word (1W) task:
  - Compute SNR in word and non-word conditions for each source
  - Candidate areas have a **SNR ratio of Word:Non-Word > 1** with significantly more activation in the word condition
  - Putative VWFA selected based on this ratio and anatomical location
  - Key question: **Which regions are selectively showing FT responses to words only?**
    - Secondary question: Does the tag of the word and non-word (F1/F2) affect SNR ratio? i.e. does the choice of tag frequency assignment affect the SNR ratio %%NK: Not sure what's meant by it, is it about the exact flicker value? Why is it for the non-word only? BG: Updated wording to be clearer: I meant does the choice of tag freq. assignment affect the SNR ratio, not the non-word tag in particular.%%
- In two-word (2W) task:
  - Partition trials by:
    - Non-Word / (Phrase + Non-phrase)
    - Non-Word in L/R hemi-field
    - Non-Word tagged F1/F2
  - For trials with matching frequency tag side (L/R) **Does our VWFA candidate still show the same selectivity, i.e. SNR ratio, as in the 1W task for words over non-words?**  %%NK: I think this is a lot to ask for, as VWFA is on the left (or at least stronger in LH than RH). I'd make it more neutral: confirm that the ROI identified as VWFA on the basis of 1-word condition is word-selective.%%
    - Possibility 1: VWFA is still just as selective for words as in the 1W condition. The SNR ratio from the 2W task is within a confidence interval of the 1W task ratio
    - Possibility 2: VWFA shows a lower ratio of Word:Non-Word SNR than in the 1W condition, but still > 1. Maybe the two halves are recognized together?
    - Possibility 3: VWFA Shows a lower ratio of W:NW SNR, below 1. In this case, panic?
   
### Lexical access and syntactic processing

- 1W Task:
  - As part of the selection for VWFA regions, looks for regions in posterior temporal lobe with similar pattern (W:NW SNR > 1, significant). These are possibilities for single-word lexical access.
- 2W Task:
  - Region(s) should show similar patterns to VWFA when using same partition of trials by hemi-field/tag freq/(non-)word, with non-word tags not represented but word tags represented %%NK: Not clear - are you looking for regions everywehere else in the brain with such properties? BG: Sorry, wasn't clear, candidate regions for lexical access should show the pattern. Regions that are responsible for syntactic processing may also.%%
  - Key question: **Which regions show both a selectively for words, as well as responses that differ when the two words form a phrase?**  %%NK: Paraphrased, but the same meaning I think: Of the word-selective ROIs identified in the previous step, are there any ROIs whose activity differs for Nonprase/Phrase condition (possibly even Nonword/Nonphrase/Phrase condition)?%%
    - "Responses that differ" could mean intermodulation responses only in the phrase condition for some region X.
    - Could also mean enhanced responses to F1 and F2 in region X when they combine? This may be the case if a region only performs lexical access for individual words but is gain-modulated by phrase %% NK: That's an interesting idea! One can also extend it to the phrase head specifically (ie 'table' in 'green table') - is the tag corresponding to the phrase head intensified in the phrase compared to nonphrase condition. Note that most heads will be the right word in the phrase condition in our stimuli, but I think that's ok as we can look at the right word in the nonword condition too%%
    - Possibility 1: Region X shows a 2W W:NW SNR ratio similar to the 1W condition. Whether the words form a phrase or not does not affect the strength of F1/F2 responses and so responses are similar between the phrase and non-phrase conditions. %%I don't think we would be comparing 2W and 1W condition here. Our syntactic composition questions are just 2W condition business. The 1W condition is to outline ROIs mostly%%
    - Possibility 2: Region X shows a 2W W:NW SNR ratio similar to the 1W condition. Whether the words form a phrase or not does not affect the strength of F1/F2 responses and so responses are similar between the phrase and non-phrase conditions.

Assuming that an intermodulation response **must be produced by syntactic processing** (which of course is not a given at all %%NK: Why not? what else can it be - semantic composition? BG: Possibly? I'm honestly not sure other than some attempt to integrate the two words into a single word. When writing this I think that's what I had in mind for idioms etc.%% ), we can list the possible outcomes for a given region. Note that "Phrase:Non-Phrase SNR ratio" indicates the ratio of the primary tags (F1/F2) between the phrase and non-phrase conditions. I.e. $\text{P:NP Ratio}_{F1} = \frac{\text{Phrase F1 SNR}}{\text{Non-Phrase F1 SNR}}$.

Note that the "SNR ratio" mentioned can also be thought of as as the sign of $\mu_A - \mu_B$: greater than one if positive and less than one if negative.

%%I havent't looked at the table, because I think we should be separating the step of identifying the ROIs on the basis of 1W condition and the analysis of 1W condition (ie extension of Hauk 2022) from the analysis and RQs of 2W condition%%

| Possibility | 1W W:NW SNR Ratio | 2W W:NW SNR Ratio | Phrase:Non-Phrase SNR ratio of words | IM Response | Takeaway                                                                                                                                                                            | Lexical Access? | Syntactic Processing? |
|-------------|-------------------|-------------------|--------------------------------------|-------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|-----------------|-----------------------|
| 1           | $>1$              | $\geq$ 1W         | $\geq 1$                             | Yes         | This region contains information for words (not non-words), but only integrates that information when the words form a phrase.                                                      | Yes or upstream | Yes or upstream       |
| 2           | $\approx 1$       | $> 1$             | $\geq 1$                             | Yes         | This region selectively responds to multiple word sequences, and is sensitive to syntax as well as $N_{words}>1$                                                                    | Upstream        | Yes or upstream       |
| 3           | $\approx 1$       | $\approx 1$       | $\geq 1$                             | Yes         | This region is responds selectively to syntactically-valid phrases, but does not contain stimulus information otherwise. Differs from (2) in that F1/F2 only appear in phrase cond. | Upstream        | Yes or upstream       |
| 4           | $\approx 1$       | $\approx 1$       | $\approx 1$                          | Yes         | This region only shows the IM response, no F1/F2. Could be downstream of a region integrating words?                                                                                | Upstream        | Upstream?             |
| 5           | $>1$              | $\geq$ 1W         | $\approx 1$                          | No          | This region selectively responds to words, and can respond to multiple words at once, but does not integrate the information about them.                                            | Yes or upstream | No                    |
| 6           | $>1$              | $\geq$ 1W         | Signif. $> 1$                        | No          | This region selectively responds to words, can respond to multiple, and is gain-modulated by syntax.                                                                                | Yes or upstream | No                    |
| Null        | $\approx 1$       | $\approx 1$       | $\approx 1$                          | No          | No response.                                                                                                                                                                        | No              | No                    |
  
