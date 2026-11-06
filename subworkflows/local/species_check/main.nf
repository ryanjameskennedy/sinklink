//
// Read-based species check with Kraken2 and Bracken
//

include { KRAKEN2_KRAKEN2 } from '../../../modules/nf-core/kraken2/kraken2/main'
include { BRACKEN_BRACKEN } from '../../../modules/nf-core/bracken/bracken/main'

workflow SPECIES_CHECK {

    take:
    ch_reads  // channel: [ val(meta), [ fastq ] ]
    kraken_db // path: Kraken2/Bracken database folder

    main:
    KRAKEN2_KRAKEN2 ( ch_reads, kraken_db, false, false )
    BRACKEN_BRACKEN ( KRAKEN2_KRAKEN2.out.report, kraken_db )

    emit:
    kraken_report = KRAKEN2_KRAKEN2.out.report    // channel: [ val(meta), path(txt) ]
    bracken       = BRACKEN_BRACKEN.out.reports   // channel: [ val(meta), path(tsv) ]
    multiqc_files = KRAKEN2_KRAKEN2.out.report.map { _meta, report -> report } // channel: [ path ]
}
