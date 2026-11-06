//
// Optional read filtering and read QC: Trimmomatic and FastQC for Illumina,
// Filtlong and NanoPlot for Nanopore
//

include { TRIMMOMATIC } from '../../../modules/nf-core/trimmomatic/main'
include { FILTLONG    } from '../../../modules/nf-core/filtlong/main'
include { FASTQC      } from '../../../modules/nf-core/fastqc/main'
include { NANOPLOT    } from '../../../modules/nf-core/nanoplot/main'

workflow READ_PREPARATION {

    take:
    ch_reads // channel: [ val(meta), [ fastq ] ]

    main:
    ch_versions      = channel.empty()
    ch_multiqc_files = channel.empty()

    ch_reads
        .branch { meta, _reads ->
            illumina: meta.platform == 'illumina'
            nanopore: meta.platform == 'nanopore'
        }
        .set { ch_by_platform }

    ch_illumina = ch_by_platform.illumina
    if (params.trim) {
        TRIMMOMATIC ( ch_by_platform.illumina )
        ch_illumina      = TRIMMOMATIC.out.trimmed_reads
        ch_multiqc_files = ch_multiqc_files.mix(TRIMMOMATIC.out.out_log.map { _meta, log -> log })
    }

    ch_nanopore = ch_by_platform.nanopore
    if (params.filtlong) {
        FILTLONG ( ch_by_platform.nanopore.map { meta, reads -> [ meta, [], reads ] } )
        ch_nanopore = FILTLONG.out.reads
    }

    FASTQC ( ch_illumina )
    ch_versions      = ch_versions.mix(FASTQC.out.versions.first())
    ch_multiqc_files = ch_multiqc_files.mix(FASTQC.out.zip.map { _meta, zip -> zip })

    NANOPLOT ( ch_nanopore )
    ch_multiqc_files = ch_multiqc_files.mix(NANOPLOT.out.txt.map { _meta, txt -> txt })

    emit:
    reads         = ch_illumina.mix(ch_nanopore) // channel: [ val(meta), [ fastq ] ]
    multiqc_files = ch_multiqc_files             // channel: [ path ]
    versions      = ch_versions                  // channel: [ path(versions.yml) ]
}
