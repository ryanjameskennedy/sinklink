# sinklink

*Did the sink infect the patient?*

sinklink tests whether bacteria isolated from a hospital sink (or another
environmental site) and from a patient belong to the same strain. Starting from
Illumina or Nanopore reads it QCs and assembles every isolate, confirms the
species, calls cgMLST/wgMLST alleles with chewBBACA and compares every pair of
isolates within each suspected transmission group against a published,
species-specific allele-difference threshold.

It is a Nextflow pipeline built on the [nf-core](https://nf-co.re) template
and nf-core modules, with tool choices and the asset Makefiles modelled on
[JASEN](https://github.com/genomic-medicine-sweden/JASEN). It runs on a single
server without a job scheduler.

## Where to start

- **New to the question?** Read the [background](background/index.md): why
  sinks matter, what the literature says and the VASK study.
- **Which threshold applies to my species, and where does it come from?** See
  [species and thresholds](species/index.md).
- **Running it for the first time?** Follow [installation](setup/install.md),
  then [running sinklink](usage.md). On thedonkey, see the
  [thedonkey profile](setup/thedonkey.md).
- **Reading the results?** See [output](output.md) and
  [interpreting the results](results/interpreting.md).

```{toctree}
:hidden:
:caption: Background
:maxdepth: 2

background/index
background/literature
background/vask
```

```{toctree}
:hidden:
:caption: Species and thresholds
:maxdepth: 2

species/index
```

```{toctree}
:hidden:
:caption: Setup
:maxdepth: 2

setup/install
setup/schemas
setup/databases
setup/thedonkey
```

```{toctree}
:hidden:
:caption: Running
:maxdepth: 2

usage
pipeline/steps
pipeline/qc
```

```{toctree}
:hidden:
:caption: Results
:maxdepth: 2

output
results/interpreting
results/caveats
```

```{toctree}
:hidden:
:caption: Reference
:maxdepth: 1

reference/parameters
reference/software
reference/references
```

```{toctree}
:hidden:
:caption: Development
:maxdepth: 1

development/contributing
development/changelog
```
