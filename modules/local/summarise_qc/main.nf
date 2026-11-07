process SUMMARISE_QC {
    tag "$meta.id"
    label 'process_single'

    conda "${moduleDir}/environment.yml"
    container "${ workflow.containerEngine == 'singularity' && !task.ext.singularity_pull_docker_container ?
        'https://depot.galaxyproject.org/singularity/python:3.9--1' :
        'biocontainers/python:3.9--1' }"

    input:
    tuple val(meta), path(assembly), path(quast), path(coverage), path(gambitcore), path(bracken), path(kraken_report), path(mlst)
    path schema_table
    path thresholds

    output:
    tuple val(meta), path("*.qc.tsv"), emit: tsv
    tuple val("${task.process}"), val('python'), eval("python3 --version | sed 's/Python //'"), topic: versions, emit: versions_python

    when:
    task.ext.when == null || task.ext.when

    script:
    def args = task.ext.args ?: ''
    def prefix = task.ext.prefix ?: "${meta.id}"
    """
    summarise_qc.py \\
        --id '${meta.id}' \\
        --platform '${meta.platform}' \\
        --schema '${meta.schema ?: ''}' \\
        --growth '${meta.growth ?: ''}' \\
        --transmission '${meta.transmission ?: ''}' \\
        --schemas ${schema_table} \\
        --thresholds ${thresholds} \\
        ${assembly ? "--assembly ${assembly}" : ''} \\
        ${quast ? "--quast ${quast}" : ''} \\
        ${coverage ? "--coverage ${coverage}" : ''} \\
        ${gambitcore ? "--gambitcore ${gambitcore}" : ''} \\
        ${bracken ? "--bracken ${bracken}" : ''} \\
        ${kraken_report ? "--kraken-report ${kraken_report}" : ''} \\
        ${mlst ? "--mlst ${mlst}" : ''} \\
        ${args} \\
        --output ${prefix}.qc.tsv
    """

    stub:
    def prefix = task.ext.prefix ?: "${meta.id}"
    """
    printf 'sample\\tqc_status\\n${meta.id}\\tpass\\n' > ${prefix}.qc.tsv
    """
}
