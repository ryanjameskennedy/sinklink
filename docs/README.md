# sinklink: Documentation

The documentation is published at <https://sinklink.readthedocs.io> and built
from this folder with Sphinx and MyST:

```bash
pip install -r docs/requirements.txt
sphinx-build -W -b html docs docs/_build/html
```

- [usage.md](usage.md): samplesheet, metadata and how to run the pipeline
- [output.md](output.md): what the pipeline writes
