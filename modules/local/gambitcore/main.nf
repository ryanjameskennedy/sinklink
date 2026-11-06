process GAMBITCORE {
    tag "$meta.id"
    label 'process_low'

    container "docker.io/clinicalgenomicslund/gambitcore:0.0.2"

    input:
    tuple val(meta), path(fasta)
    path db

    output:
    tuple val(meta), path("*.gambitcore.tsv"), emit: tsv
    tuple val("${task.process}"), val('gambitcore'), eval("gambitcore --version 2>&1 | sed 's/^gambitcore //'"), topic: versions, emit: versions_gambitcore

    when:
    task.ext.when == null || task.ext.when

    script:
    def args = task.ext.args ?: ''
    def prefix = task.ext.prefix ?: "${meta.id}"
    """
    gambitcore \\
        ${db} \\
        ${fasta} \\
        ${args} \\
        > ${prefix}.gambitcore.tsv
    """

    stub:
    def prefix = task.ext.prefix ?: "${meta.id}"
    """
    touch ${prefix}.gambitcore.tsv
    """
}
