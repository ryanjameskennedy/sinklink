//
// Variant calling against the schema's reference genome (Snippy for Illumina,
// minimap2 and Clair3 for Nanopore), then SNP distances between the isolates of
// each schema: a pseudogenome per isolate with low-depth, repeat and prophage
// regions masked, recombination removed with Gubbins and distances from snp-dists
//

include { SNIPPY_RUN                                } from '../../../modules/nf-core/snippy/run/main'
include { MINIMAP2_ALIGN as MINIMAP2_REFERENCE      } from '../../../modules/nf-core/minimap2/align/main'
include { CLAIR3                                    } from '../../../modules/nf-core/clair3/main'
include { NUCMER                                    } from '../../../modules/nf-core/nucmer/main'
include { PHISPY                                    } from '../../../modules/nf-core/phispy/main'
include { GAWK as GAWK_REFERENCE_CHROMOSOME         } from '../../../modules/nf-core/gawk/main'
include { GAWK as GAWK_REFERENCE_MASK               } from '../../../modules/nf-core/gawk/main'
include { MOSDEPTH                                  } from '../../../modules/nf-core/mosdepth/main'
include { GAWK as GAWK_SAMPLE_MASK                  } from '../../../modules/nf-core/gawk/main'
include { BCFTOOLS_VIEW                             } from '../../../modules/nf-core/bcftools/view/main'
include { BCFTOOLS_CONSENSUS                        } from '../../../modules/nf-core/bcftools/consensus/main'
include { GAWK as GAWK_PSEUDOGENOME                 } from '../../../modules/nf-core/gawk/main'
include { GAWK as GAWK_ALIGNMENT                    } from '../../../modules/nf-core/gawk/main'
include { GUBBINS                                   } from '../../../modules/nf-core/gubbins/main'
include { SNPDISTS                                  } from '../../../modules/nf-core/snpdists/main'

workflow VARIANT_CALLING {

    take:
    ch_reads     // channel: [ val(meta), [ fastq ] ]
    ch_reference // channel: [ val(meta), [ fasta, fai, gff, gbff ] ]
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

    ch_vcf = SNIPPY_RUN.out.vcf_gz.mix(CLAIR3.out.vcf)
    ch_bam = SNIPPY_RUN.out.bam
        .join(SNIPPY_RUN.out.bai)
        .mix(MINIMAP2_REFERENCE.out.bam.join(MINIMAP2_REFERENCE.out.index))

    //
    // Once per reference genome: its chromosome, and a mask of repeats (nucmer
    // self-alignment) and prophages (PhiSpy)
    //
    ch_reference
        .map { meta, reference -> [ [ id: meta.reference ], reference ] }
        .unique()
        .set { ch_genome }

    GAWK_REFERENCE_CHROMOSOME (
        ch_genome.map { genome, reference -> [ genome, reference[0], 'fa' ] },
        file("${projectDir}/assets/awk/first_record.awk", checkIfExists: true),
        false
    )
    ch_genome
        .join(GAWK_REFERENCE_CHROMOSOME.out.output)
        .map { genome, reference, chromosome -> [ genome, reference[0], chromosome ] }
        .set { ch_nucmer }
    NUCMER ( ch_nucmer )
    PHISPY ( ch_genome.map { genome, reference -> [ genome, reference[3] ] } )

    GAWK_REFERENCE_MASK (
        NUCMER.out.coords
            .join(PHISPY.out.coordinates)
            .map { genome, coords, prophages -> [ genome, [ coords, prophages ], 'bed' ] },
        file("${projectDir}/assets/awk/reference_mask.awk", checkIfExists: true),
        false
    )

    //
    // Per isolate: PASS substitutions applied to the reference, with regions
    // below --snp_min_depth and the reference's mask set to N; chromosome only
    //
    MOSDEPTH (
        ch_bam.map { meta, bam, bai -> [ meta, bam, bai, [] ] },
        [ [:], [] ],
        [ 'LOW', 'CALLABLE' ]
    )
    MOSDEPTH.out.quantized_bed
        .map { meta, low_depth -> [ meta.reference, meta, low_depth ] }
        .combine(GAWK_REFERENCE_MASK.out.output.map { genome, mask -> [ genome.id, mask ] }, by: 0)
        .map { _accession, meta, low_depth, mask -> [ meta, [ low_depth, mask ], 'bed' ] }
        .set { ch_sample_mask }
    GAWK_SAMPLE_MASK (
        ch_sample_mask,
        file("${projectDir}/assets/awk/sample_mask.awk", checkIfExists: true),
        false
    )

    BCFTOOLS_VIEW ( ch_vcf.map { meta, vcf -> [ meta, vcf, [] ] }, [], [], [] )
    BCFTOOLS_VIEW.out.vcf
        .join(BCFTOOLS_VIEW.out.index)
        .join(ch_reference)
        .join(GAWK_SAMPLE_MASK.out.output)
        .map { meta, vcf, tbi, reference, mask -> [ meta, vcf, tbi, reference[0], mask ] }
        .set { ch_consensus }
    BCFTOOLS_CONSENSUS ( ch_consensus )

    GAWK_PSEUDOGENOME (
        BCFTOOLS_CONSENSUS.out.fasta.map { meta, fasta -> [ meta, fasta, 'fa' ] },
        file("${projectDir}/assets/awk/pseudogenome.awk", checkIfExists: true),
        false
    )

    //
    // Per schema: the pseudogenomes and the reference chromosome in one alignment,
    // recombination removed with Gubbins (3 or more sequences), then snp-dists
    //
    GAWK_PSEUDOGENOME.out.output
        .map { meta, fasta -> [ [ id: meta.schema, reference: meta.reference ], fasta ] }
        .groupTuple()
        .map { group, fastas -> [ group.reference, group, fastas ] }
        .combine(GAWK_REFERENCE_CHROMOSOME.out.output.map { genome, chromosome -> [ genome.id, chromosome ] }, by: 0)
        .map { _accession, group, fastas, chromosome ->
            [ group + [ sequences: fastas.size() + 1 ], fastas + [ chromosome ], 'aln' ]
        }
        .set { ch_alignment }
    GAWK_ALIGNMENT (
        ch_alignment,
        file("${projectDir}/assets/awk/alignment.awk", checkIfExists: true),
        false
    )

    GAWK_ALIGNMENT.out.output
        .branch { meta, _alignment ->
            recombination: meta.sequences >= 3
            direct: true
        }
        .set { ch_aligned }
    GUBBINS ( ch_aligned.recombination.map { _meta, alignment -> alignment } )

    GUBBINS.out.fasta
        .flatten()
        .map { fasta -> [ fasta.name.tokenize('.')[0], fasta ] }
        .join(ch_aligned.recombination.map { meta, _alignment -> [ meta.id, meta ] })
        .map { _schema, fasta, meta -> [ meta + [ recombination_filtered: true ], fasta ] }
        .mix(ch_aligned.direct.map { meta, alignment -> [ meta + [ recombination_filtered: false ], alignment ] })
        .set { ch_snpdists }
    SNPDISTS ( ch_snpdists )

    emit:
    vcf          = ch_vcf                           // channel: [ val(meta), path(vcf.gz) ]
    pseudogenome = GAWK_PSEUDOGENOME.out.output     // channel: [ val(meta), path(fasta) ]
    snp_dists    = SNPDISTS.out.tsv                 // channel: [ val(meta), path(tsv) ]
}
