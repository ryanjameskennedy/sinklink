//
// Variant calling against the schema's reference genome: Snippy (BWA-MEM and
// FreeBayes) for Illumina, minimap2 and Clair3 for Nanopore, then a masked
// pseudogenome per isolate for pairwise SNP distances
//

include { SNIPPY_RUN                           } from '../../../modules/nf-core/snippy/run/main'
include { MINIMAP2_ALIGN as MINIMAP2_REFERENCE } from '../../../modules/nf-core/minimap2/align/main'
include { CLAIR3                               } from '../../../modules/nf-core/clair3/main'
include { SAMTOOLS_DEPTH                       } from '../../../modules/nf-core/samtools/depth/main'
include { MAKE_PSEUDOGENOME                    } from '../../../modules/local/make_pseudogenome/main'

workflow VARIANT_CALLING {

    take:
    ch_reads     // channel: [ val(meta), [ fastq ] ]
    ch_reference // channel: [ val(meta), [ fasta, fai, gff ] ]
    clair3_model // string: Clair3 model bundled in its container

    main:
    ch_reads
        .join(ch_reference)
        .branch { meta, _reads, _reference ->
            illumina: meta.platform == 'illumina'
            nanopore: meta.platform == 'nanopore'
        }
        .set { ch_input }

    ch_input.illumina
        .multiMap { meta, reads, reference ->
            reads    : [ meta, reads ]
            reference: reference[0]
        }
        .set { ch_snippy }
    SNIPPY_RUN ( ch_snippy.reads, ch_snippy.reference )

    ch_input.nanopore
        .multiMap { meta, reads, reference ->
            reads    : [ meta, reads ]
            reference: [ meta, reference[0] ]
        }
        .set { ch_minimap2 }
    MINIMAP2_REFERENCE ( ch_minimap2.reads, ch_minimap2.reference, true, 'bai', false, false )

    MINIMAP2_REFERENCE.out.bam
        .join(MINIMAP2_REFERENCE.out.index)
        .join(ch_reference)
        .multiMap { meta, bam, bai, reference ->
            bam      : [ meta, bam, bai, clair3_model, [], 'ont' ]
            reference: [ meta, reference[0] ]
            index    : [ meta, reference[1] ]
        }
        .set { ch_clair3 }
    CLAIR3 ( ch_clair3.bam, ch_clair3.reference, ch_clair3.index )

    SNIPPY_RUN.out.bam
        .join(SNIPPY_RUN.out.bai)
        .mix(MINIMAP2_REFERENCE.out.bam.join(MINIMAP2_REFERENCE.out.index))
        .map { meta, bam, bai -> [ meta, bam, bai, [] ] }
        .set { ch_depth }
    SAMTOOLS_DEPTH ( ch_depth )

    ch_vcf = SNIPPY_RUN.out.vcf_gz.mix(CLAIR3.out.vcf)

    ch_reference
        .map { meta, reference -> [ meta, reference[0] ] }
        .join(ch_vcf)
        .join(SAMTOOLS_DEPTH.out.tsv)
        .set { ch_pseudogenome }
    MAKE_PSEUDOGENOME ( ch_pseudogenome )

    emit:
    vcf          = ch_vcf                       // channel: [ val(meta), path(vcf.gz) ]
    pseudogenome = MAKE_PSEUDOGENOME.out.fasta  // channel: [ val(meta), path(fasta) ]
    stats        = MAKE_PSEUDOGENOME.out.tsv    // channel: [ val(meta), path(tsv) ]
}
