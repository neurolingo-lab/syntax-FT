# Rough outline of planned analyses

### Visual Word Form Area (VWFA)

- In one-word (1W) task:
  - Compute SNR in word and non-word conditions for each source
  - Candidate areas have a **SNR ratio of Word:Non-Word > 1** with substantially (meaning TBD) and significantly more activation in the word condition
  - Putative VWFA selected based on this ratio and anatomical location
  - Key question: **Which regions are selectively showing FT responses to words only?**
    - Secondary question: Does the tag of the non-word (F1/F2) affect SNR ratio?
- In two-word (2W) task:
  - Partition trials by:
    - Non-Word / (Phrase + Non-phrase)
    - Non-Word in L/R hemi-field
    - Non-Word tagged F1/F2
  - For trials with matching frequency tag side (L/R) **Does our VWFA candidate still show the same selectivity, i.e. SNR ratio, as in the 1W task for words over non-words?**
    - Possibility 1: VWFA is still just as selective for words as in the 1W condition. The SNR ratio from the 2W task is within a confidence interval of the 1W task ratio
    - Possibility 2: VWFA shows a lower ratio of Word:Non-Word SNR than in the 1W condition, but still > 1. Maybe the two halves are recognized together?
    - Possibility 3: VWFA Shows a lower ratio of W:NW SNR, below 1. In this case, panic?
   
### Lexical access and syntactic processing

- 1W Task:
  - As part of the selection for VWFA regions, looks for regions in posterior temporal lobe with similar pattern (W:NW SNR > 1, significant). These are possibilities for single-word lexical access.
- 2W Task:
  - Region(s) should show similar patterns to VWFA when using same parition of trials by hemi-field/tag freq/(non-)word, with non-word tags not represented but word tags represented
  - Key question: **Which regions show both a selectively for words, as well as responses that differ when the two words form a phrase?**
    - "Responses that differ" could mean intermodulation responses only in the phrase condition for some region X.
    - Could also mean enhanced responses to F1 and F2 in region X when they combine? This may be the case if a region only performs lexical access for individual words but is gain-modulated by phrase
    - Possibility 1: Region X shows a 2W W:NW SNR ratio similar to the 1W condition. Whether the words form a phrase or not does not affect the strength of F1/F2 responses and so responses are similar between the phrase and non-phrase conditions.
    - Possibility 2: Region X shows a 2W W:NW SNR ratio similar to the 1W condition. Whether the words form a phrase or not does not affect the strength of F1/F2 responses and so responses are similar between the phrase and non-phrase conditions.

Assuming that an intermodulation response **must be produced by syntactic processing** (which of course is not a given at all), we can list the possible outcomes for a given region. Note that "Phrase:Non-Phrase SNR ratio" indicates the ratio of the primary tags (F1/F2) between the phrase and non-phrase conditions. I.e. $\text{P:NP Ratio}_{F1} = \frac{\text{Phrase F1 SNR}}{\text{Non-Phrase F1 SNR}}$.

| Possibility | 1W W:NW SNR Ratio | 2W W:NW SNR Ratio | Phrase:Non-Phrase SNR ratio of words | IM Response | Takeaway                                                                                                                                                                            | Lexical Access? | Syntactic Processing? |
|-------------|-------------------|-------------------|--------------------------------------|-------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|-----------------|-----------------------|
| 1           | $>1$              | $\geq$ 1W         | $\geq 1$                             | Yes         | This region contains information for words (not non-words), but only integrates that information when the words form a phrase.                                                      | Yes or upstream | Yes or upstream       |
| 2           | $\approx 1$       | $> 1$             | $\geq 1$                             | Yes         | This region selectively responds to multiple word sequences, and is sensitive to syntax as well as $N_{words}>1$                                                                    | Upstream        | Yes or upstream       |
| 3           | $\approx 1$       | $\approx 1$       | $\geq 1$                             | Yes         | This region is responds selectively to syntactically-valid phrases, but does not contain stimulus information otherwise. Differs from (2) in that F1/F2 only appear in phrase cond. | Upstream        | Yes or upstream       |
| 4           | $\approx 1$       | $\approx 1$       | $\approx 1$                          | Yes         | This region only shows the IM response, no F1/F2. Could be downstream of a region integrating words?                                                                                | Upstream        | Upstream?             |
| 5           | $>1$              | $\geq$ 1W         | $\approx 1$                          | No          | This region selectively responds to words, and can respond to multiple words at once, but does not integrate the information about them.                                            | Yes or upstream | No                    |
| 6           | $>1$              | $\geq$ 1W         | Signif. $> 1$                        | No          | This region selectively responds to words, can respond to multiple, and is gain-modulated by syntax.                                                                                | Yes or upstream | No                    |
| Null        | $\approx 1$       | $\approx 1$       | $\approx 1$                          | No          | No response.                                                                                                                                                                        | No              | No                    |
  
