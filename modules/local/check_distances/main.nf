process CHECK_DISTANCES {
    label 'process_single'

    conda "${moduleDir}/environment.yml"
    container "${ workflow.containerEngine in ['singularity', 'apptainer'] && !task.ext.singularity_pull_docker_container ?
        'https://depot.galaxyproject.org/singularity/python:3.9--1' :
        'biocontainers/python:3.9--1' }"

    input:
    path metadata
    path qc_summary
    path alleles, stageAs: "alleles/*"
    path pseudogenomes, stageAs: "pseudogenomes/*"
    path schema_table
    path species_map

    output:
    path "allele_qc.tsv"         , emit: allele_qc
    path "pairwise_distances.tsv", emit: pairwise
    path "group_summary.tsv"     , emit: summary
    tuple val("${task.process}"), val('python'), eval("python3 --version | sed 's/Python //'"), topic: versions, emit: versions_python

    when:
    task.ext.when == null || task.ext.when

    script:
    def args = task.ext.args ?: ''
    """
    check_distances.py \\
        --samplesheet ${metadata} \\
        ${alleles ? '--alleles alleles/*' : ''} \\
        ${pseudogenomes ? '--pseudogenomes pseudogenomes/*' : ''} \\
        --species-map ${species_map} \\
        --schemas ${schema_table} \\
        --qc-summary ${qc_summary} \\
        --outdir . \\
        ${args}
    """

    stub:
    """
    touch allele_qc.tsv pairwise_distances.tsv group_summary.tsv
    """
}
