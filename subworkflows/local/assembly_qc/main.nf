//
// Assembly QC: QUAST statistics and Mash distance against the schema's reference
// genome (when there is one), gambitcore completeness, read depth over the
// isolate's own assembly and 7-gene MLST
//

include { QUAST             } from '../../../modules/nf-core/quast/main'
include { GAMBITCORE        } from '../../../modules/local/gambitcore/main'
include { BWA_INDEX         } from '../../../modules/nf-core/bwa/index/main'
include { BWA_MEM           } from '../../../modules/nf-core/bwa/mem/main'
include { MINIMAP2_ALIGN    } from '../../../modules/nf-core/minimap2/align/main'
include { SAMTOOLS_INDEX    } from '../../../modules/nf-core/samtools/index/main'
include { SAMTOOLS_COVERAGE } from '../../../modules/nf-core/samtools/coverage/main'
include { MLST              } from '../../../modules/nf-core/mlst/main'
include { MASH_DIST         } from '../../../modules/nf-core/mash/dist/main'

workflow ASSEMBLY_QC {

    take:
    ch_assembly  // channel: [ val(meta), path(fasta) ]
    ch_reads     // channel: [ val(meta), [ fastq ] ]
    ch_reference // channel: [ val(meta), [ fasta, fai, gff, gbff ] ]
    gambit_db    // path: GAMBIT database folder, or [] to skip gambitcore

    main:
    ch_assembly
        .join(ch_reference, remainder: true)
        .filter { _meta, fasta, _reference -> fasta != null }
        .multiMap { meta, fasta, reference ->
            assembly : [ meta, fasta ]
            reference: [ meta, reference ? reference[0] : [] ]
            gff      : [ meta, reference ? reference[2] : [] ]
        }
        .set { ch_quast }
    QUAST ( ch_quast.assembly, ch_quast.reference, ch_quast.gff )

    ch_assembly
        .join(ch_reference)
        .multiMap { meta, fasta, reference ->
            assembly : [ meta, fasta ]
            reference: reference[0]
        }
        .set { ch_mash }
    MASH_DIST ( ch_mash.assembly, ch_mash.reference )
    MLST ( ch_assembly )

    ch_gambitcore = channel.empty()
    if (gambit_db) {
        GAMBITCORE ( ch_assembly, gambit_db )
        ch_gambitcore = GAMBITCORE.out.tsv
    }

    ch_reads
        .join(ch_assembly)
        .branch { meta, _reads, _fasta ->
            illumina: meta.platform == 'illumina'
            nanopore: meta.platform == 'nanopore'
        }
        .set { ch_mapping }

    BWA_INDEX ( ch_mapping.illumina.map { meta, _reads, fasta -> [ meta, fasta ] } )
    ch_mapping.illumina
        .join(BWA_INDEX.out.index)
        .multiMap { meta, reads, fasta, index ->
            reads: [ meta, reads ]
            index: [ meta, index ]
            fasta: [ meta, fasta ]
        }
        .set { ch_bwa }
    BWA_MEM ( ch_bwa.reads, ch_bwa.index, ch_bwa.fasta, true )
    SAMTOOLS_INDEX ( BWA_MEM.out.bam )

    ch_mapping.nanopore
        .multiMap { meta, reads, fasta ->
            reads    : [ meta, reads ]
            reference: [ meta, fasta ]
        }
        .set { ch_minimap2 }
    MINIMAP2_ALIGN ( ch_minimap2.reads, ch_minimap2.reference, true, 'bai', false, false )

    BWA_MEM.out.bam
        .join(SAMTOOLS_INDEX.out.index)
        .mix(MINIMAP2_ALIGN.out.bam.join(MINIMAP2_ALIGN.out.index))
        .set { ch_bam }
    SAMTOOLS_COVERAGE ( ch_bam, [ [:], [], [] ] )

    emit:
    quast         = QUAST.out.tsv                 // channel: [ val(meta), path(tsv) ]
    coverage      = SAMTOOLS_COVERAGE.out.coverage // channel: [ val(meta), path(txt) ]
    gambitcore    = ch_gambitcore                 // channel: [ val(meta), path(tsv) ]
    mlst          = MLST.out.tsv                  // channel: [ val(meta), path(tsv) ]
    mash          = MASH_DIST.out.dist            // channel: [ val(meta), path(txt) ]
    multiqc_files = QUAST.out.tsv.map { _meta, tsv -> tsv } // channel: [ path ]
}
