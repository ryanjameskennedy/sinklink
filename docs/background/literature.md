# What the literature says

How to decide whether two bacterial isolates come from the same source.

## 1. Confirm the species from the genome first

Several of these organisms are species complexes that MALDI-TOF cannot reliably
separate. _K. oxytoca_ is often confused with _K. michiganensis_ and
_K. grimontii_ (Dabernig-Heinz et al. 2024); "_S. marcescens_" NICU outbreaks
have turned out to involve _S. sarumanii_ and _S. bockelmannii_; the
_E. cloacae_ complex contains many species; _S. maltophilia_ is a complex of 23
lineages (Gröschel et al. 2020). Isolates of different species cannot be the
same strain, and a scheme built for one species is not valid for another.

## 2. Use cgMLST or core-genome SNPs

cgMLST gives results comparable to SNP typing and is easier to standardise
between labs (Tönnies et al. 2021). SNPs give finer resolution for borderline
pairs. Seven-gene MLST can only exclude a link: isolates of the same sequence
type can still be unrelated.

## 3. There is no universal threshold

Each cut-off belongs to one species, one scheme and one allele-calling
software. Pipelines differ in how they call alleles, so counts for the same pair
can differ between tools. Near-identical profiles do not by themselves prove
transmission; epidemiological information is always needed (Tönnies et al.
2021). In the Graz _K. oxytoca_ sink outbreak, an unrelated isolate from the
same hospital and same ST was only 10 alleles from the outbreak cluster,
showing how narrow the gap can be (Dabernig-Heinz et al. 2024).

## 4. Account for how long the source was contaminated

Bacteria keep mutating while they persist in a sink, so the longer the interval
between samples, the more differences are expected even from a single source.
Fixed thresholds ignore mutation rate and duration of contamination (Duval,
Opatowski & Brisse 2023).

## 5. Sinks hold mixed, long-lived populations

A single drain can carry several strains of the same species, so one colony may
miss the strain that reached the patient; picking several colonies per sample
helps (Constantinides et al. 2020). Clones can persist in plumbing for years:
carbapenemase-producing _C. freundii_ clusters linked patients and drains from
2018 to 2021 (Hamerlinck et al. 2023).

## 6. Genomics cannot tell you the direction

In a review of ICU sink studies, sequencing linked sink and patient isolates in
about half of cases, but where timelines were clear they mostly showed
patient-to-sink spread; only 8 reports supported sink-to-patient spread.
Direction has to come from sampling dates, room layout and whether the patient
screened negative on admission.

Full citations are in the [references](../reference/references.md).
