process MAKE_PSEUDOGENOME {
    tag "$meta.id"
    label 'process_single'

    conda "${moduleDir}/environment.yml"
    container "${ workflow.containerEngine == 'singularity' && !task.ext.singularity_pull_docker_container ?
        'https://depot.galaxyproject.org/singularity/python:3.9--1' :
        'biocontainers/python:3.9--1' }"

    input:
    tuple val(meta), path(reference), path(vcf), path(depth)

    output:
    tuple val(meta), path("*.pseudogenome.fa") , emit: fasta
    tuple val(meta), path("*.pseudogenome.tsv"), emit: tsv
    tuple val("${task.process}"), val('python'), eval("python3 --version | sed 's/Python //'"), topic: versions, emit: versions_python

    when:
    task.ext.when == null || task.ext.when

    script:
    def args = task.ext.args ?: ''
    def prefix = task.ext.prefix ?: "${meta.id}"
    """
    make_pseudogenome.py \\
        --sample '${meta.id}' \\
        --reference ${reference} \\
        --vcf ${vcf} \\
        --depth ${depth} \\
        --prefix ${prefix} \\
        ${args}
    """

    stub:
    def prefix = task.ext.prefix ?: "${meta.id}"
    """
    printf '>${meta.id}\\nACGT\\n' > ${prefix}.pseudogenome.fa
    touch ${prefix}.pseudogenome.tsv
    """
}
