//
// De novo assembly: SKESA or SPAdes for Illumina, Flye and Medaka for Nanopore.
// Every assembly is emitted uncompressed as <id>.fa so chewBBACA names it by sample.
//

include { SKESA                      } from '../../../modules/nf-core/skesa/main'
include { SPADES                     } from '../../../modules/nf-core/spades/main'
include { FLYE                       } from '../../../modules/nf-core/flye/main'
include { MEDAKA                     } from '../../../modules/nf-core/medaka/main'
include { GUNZIP as GUNZIP_FLYE      } from '../../../modules/nf-core/gunzip/main'
include { GUNZIP as GUNZIP_ASSEMBLY  } from '../../../modules/nf-core/gunzip/main'

workflow ASSEMBLY {

    take:
    ch_reads // channel: [ val(meta), [ fastq ] ]

    main:
    ch_reads
        .branch { meta, _reads ->
            illumina: meta.platform == 'illumina'
            nanopore: meta.platform == 'nanopore'
        }
        .set { ch_by_platform }

    ch_assembly = channel.empty()
    ch_gzipped  = channel.empty()

    if (params.assembler == 'spades') {
        SPADES ( ch_by_platform.illumina.map { meta, reads -> [ meta, reads, [], [] ] }, [], [] )
        ch_gzipped = ch_gzipped.mix(SPADES.out.contigs)
    } else {
        SKESA ( ch_by_platform.illumina )
        ch_assembly = ch_assembly.mix(SKESA.out.fasta)
    }

    FLYE ( ch_by_platform.nanopore, '--nano-hq' )
    GUNZIP_FLYE ( FLYE.out.fasta )
    MEDAKA ( ch_by_platform.nanopore.join(GUNZIP_FLYE.out.gunzip) )
    ch_gzipped = ch_gzipped.mix(MEDAKA.out.assembly)

    GUNZIP_ASSEMBLY ( ch_gzipped )
    ch_assembly = ch_assembly.mix(GUNZIP_ASSEMBLY.out.gunzip)

    emit:
    assembly = ch_assembly // channel: [ val(meta), path(fasta) ]
}
