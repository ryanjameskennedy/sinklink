# The VASK study

sinklink was written for the VASK colonisation dataset:
`vask_colonisation_hidden.csv` lists 26 isolates (13 environmental, 13 airway)
in 9 suspected transmission groups.

```{note}
The file is not in the repository because it contains study patient
identifiers. Keep it outside version control (it is git-ignored) and pass it
to the pipeline with `--metadata`.
```

| Group          | Species                          | Isolates                               | Span     | Notes                                                                                |
| -------------- | -------------------------------- | -------------------------------------- | -------- | ------------------------------------------------------------------------------------ |
| Transmission_1 | _Enterobacter cloacae_ (complex) | 2 environment, 1 airway                | 59 days  | Lab labels differ ("cloacae" vs "cloacae complex"); confirm species from the genome  |
| Transmission_2 | _Stenotrophomonas maltophilia_   | 1 environment, 1 airway (same patient) | 5 days   | Sink positive before airway: the best fit for sink-to-patient spread                 |
| Transmission_3 | _Pseudomonas aeruginosa_         | 1 environment, 2 airway                | 338 days | Patient positive ~10 months before the sink; long span means more expected diversity |
| Transmission_4 | _Klebsiella oxytoca_             | 2 environment, 1 airway                | 357 days | Environmental isolates a year apart                                                  |
| Transmission_5 | _Klebsiella oxytoca_ (group)     | 1 environment, 1 airway (same patient) | 3 days   | Lab labels differ ("oxytoca" vs "oxytoca group")                                     |
| Transmission_6 | _Citrobacter freundii_           | 1 environment, 2 airway (same patient) | 3 days   | Sink and airway sampled on the same day: direction unknown                           |
| Transmission_7 | _Serratia marcescens_            | 1 environment, 3 airway                | 50 days  | Three patients                                                                       |
| Transmission_8 | _Pseudomonas aeruginosa_         | 2 environment, 1 airway                | 60 days  | Patient positive before the second sink                                              |
| Transmission_9 | _Klebsiella pneumoniae_          | 2 environment, 1 airway                | 68 days  | Sink and airway sampled on the same day; second sink later                           |

Several patients appear in more than one group (different species from the
same sites). All groups and species run together in one pipeline run; see
[running sinklink](../usage.md).

The columns are described under [metadata input](../usage.md#metadata-input).
Each group's species has its own page under
[species and thresholds](../species/index.md).
