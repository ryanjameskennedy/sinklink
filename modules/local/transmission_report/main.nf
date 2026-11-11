process TRANSMISSION_REPORT {
    label 'process_single'

    conda "${moduleDir}/environment.yml"
    container "${ workflow.containerEngine in ['singularity', 'apptainer'] && !task.ext.singularity_pull_docker_container ?
        'https://community-cr-prod.seqera.io/docker/registry/v2/blobs/sha256/bd/bd02c52167bdc5d0ac62b9a0053b56598dc696c9c52611c879f979ac09095d07/data' :
        'community.wave.seqera.io/library/python_matplotlib-base:79ffa5718e82136c' }"

    input:
    path pairwise
    path summary
    path allele_qc
    path qc_summary
    path metadata
    path schema_table
    path qc_thresholds

    output:
    path "report/transmission_report.html", emit: html
    path "report/table1.tsv"              , emit: table
    path "report/figures/*"               , emit: figures, optional: true
    tuple val("${task.process}"), val('python'), eval("python3 --version | sed 's/Python //'"), topic: versions, emit: versions_python
    tuple val("${task.process}"), val('matplotlib'), eval("python3 -c 'import matplotlib; print(matplotlib.__version__)'"), topic: versions, emit: versions_matplotlib

    when:
    task.ext.when == null || task.ext.when

    script:
    def args = task.ext.args ?: ''
    """
    export MPLCONFIGDIR="\$PWD/.matplotlib"

    transmission_report.py \\
        --pairs ${pairwise} \\
        --groups ${summary} \\
        --allele-qc ${allele_qc} \\
        --qc-summary ${qc_summary} \\
        --metadata ${metadata} \\
        --schemas ${schema_table} \\
        --qc-thresholds ${qc_thresholds} \\
        --pipeline-version ${workflow.manifest.version} \\
        --outdir report \\
        ${args}
    """

    stub:
    """
    mkdir -p report/figures
    touch report/transmission_report.html report/table1.tsv
    """
}
