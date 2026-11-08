/*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    IMPORT MODULES / SUBWORKFLOWS / FUNCTIONS
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
*/
include { MULTIQC                } from '../modules/nf-core/multiqc/main'
include { SUMMARISE_QC           } from '../modules/local/summarise_qc/main'
include { CHECK_DISTANCES        } from '../modules/local/check_distances/main'
include { READ_PREPARATION       } from '../subworkflows/local/read_preparation'
include { ASSEMBLY               } from '../subworkflows/local/assembly'
include { ASSEMBLY_QC            } from '../subworkflows/local/assembly_qc'
include { SPECIES_CHECK          } from '../subworkflows/local/species_check'
include { ALLELE_CALLING         } from '../subworkflows/local/allele_calling'
include { paramsSummaryMap       } from 'plugin/nf-schema'
include { paramsSummaryMultiqc   } from '../subworkflows/nf-core/utils_nfcore_pipeline'
include { softwareVersionsToYAML } from '../subworkflows/nf-core/utils_nfcore_pipeline'
include { methodsDescriptionText } from '../subworkflows/local/utils_nfcore_sinklink_pipeline'
include { assetPath              } from '../subworkflows/local/utils_nfcore_sinklink_pipeline'
include { referenceChannel       } from '../subworkflows/local/utils_nfcore_sinklink_pipeline'

/*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    RUN MAIN WORKFLOW
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
*/

workflow SINKLINK {

    take:
    ch_samplesheet // channel: [ val(meta), [ fastq ] ] read in from --input
    main:

    ch_versions      = channel.empty()
    ch_multiqc_files = channel.empty()

    ch_schema_table = file(assetPath(params.schema_table, 'schemas.tsv'), checkIfExists: true)
    ch_species_map  = file(assetPath(params.species_map, 'species_map.tsv'), checkIfExists: true)
    ch_thresholds   = file(assetPath(params.qc_thresholds, 'qc_thresholds.tsv'), checkIfExists: true)
    ch_metadata     = file(params.metadata, checkIfExists: true)
    ch_gambit_db    = params.gambit_db ? file(params.gambit_db, checkIfExists: true) : []

    if (!params.skip_host_removal && !params.deacon_index) {
        error("--deacon_index is required for human read removal; set it or use --skip_host_removal")
    }
    ch_deacon_index = params.skip_host_removal ? [] : file(params.deacon_index, checkIfExists: true)

    if (!params.skip_variant_calling && !params.references_dir) {
        error("--references_dir is required for variant calling; set it or use --skip_variant_calling")
    }
    ch_reference = params.references_dir ?
        referenceChannel(ch_samplesheet, params.references_dir) :
        channel.empty()

    //
    // SUBWORKFLOW: Human read removal, optional read filtering and read QC
    //
    READ_PREPARATION ( ch_samplesheet, ch_deacon_index )
    ch_reads         = READ_PREPARATION.out.reads
    ch_versions      = ch_versions.mix(READ_PREPARATION.out.versions)
    ch_multiqc_files = ch_multiqc_files.mix(READ_PREPARATION.out.multiqc_files)

    //
    // SUBWORKFLOW: De novo assembly
    //
    ASSEMBLY ( ch_reads )
    ch_assembly = ASSEMBLY.out.assembly

    //
    // SUBWORKFLOW: Assembly QC, read depth and 7-gene MLST
    //
    ASSEMBLY_QC ( ch_assembly, ch_reads, ch_reference, ch_gambit_db )
    ch_multiqc_files = ch_multiqc_files.mix(ASSEMBLY_QC.out.multiqc_files)

    //
    // SUBWORKFLOW: Read-based species check
    //
    SPECIES_CHECK ( ch_reads, file(params.kraken_db, checkIfExists: true) )
    ch_kraken_report = SPECIES_CHECK.out.kraken_report
    ch_bracken       = SPECIES_CHECK.out.bracken
    ch_multiqc_files = ch_multiqc_files.mix(SPECIES_CHECK.out.multiqc_files)

    //
    // MODULE: Read and assembly QC summary per isolate, then one table for all
    //
    ch_reads
        .map { meta, _reads -> [ meta ] }
        .join(ch_assembly, remainder: true)
        .join(ASSEMBLY_QC.out.quast, remainder: true)
        .join(ASSEMBLY_QC.out.coverage, remainder: true)
        .join(ASSEMBLY_QC.out.gambitcore, remainder: true)
        .join(ch_bracken, remainder: true)
        .join(ch_kraken_report, remainder: true)
        .join(ASSEMBLY_QC.out.mlst, remainder: true)
        .join(ASSEMBLY_QC.out.mash, remainder: true)
        .map { row -> row.collect { item -> item == null ? [] : item } }
        .set { ch_qc_input }

    SUMMARISE_QC ( ch_qc_input, ch_schema_table, ch_thresholds )

    SUMMARISE_QC.out.tsv
        .map { _meta, tsv -> tsv }
        .collectFile(
            name: 'qc_summary.tsv',
            keepHeader: true,
            skip: 1,
            sort: { tsv -> tsv.name },
            storeDir: "${params.outdir}/summary"
        )
        .set { ch_qc_summary }

    //
    // SUBWORKFLOW: chewBBACA allele calling, then distances within transmission groups
    //
    if (!params.skip_chewbbaca) {
        if (!params.schemas_dir) {
            error("--schemas_dir is required for allele calling; set it or use --skip_chewbbaca")
        }
        ALLELE_CALLING ( ch_assembly, params.schemas_dir )

        CHECK_DISTANCES (
            ch_metadata,
            ch_qc_summary,
            ALLELE_CALLING.out.alleles.map { _meta, tsv -> tsv }.collect().ifEmpty([]),
            ch_schema_table,
            ch_species_map
        )
    }

    //
    // Collate and save software versions
    //
    def topic_versions = Channel.topic("versions")
        .distinct()
        .branch { entry ->
            versions_file: entry instanceof Path
            versions_tuple: true
        }

    def topic_versions_string = topic_versions.versions_tuple
        .map { process, tool, version ->
            [ process[process.lastIndexOf(':')+1..-1], "  ${tool}: ${version}" ]
        }
        .groupTuple(by:0)
        .map { process, tool_versions ->
            tool_versions.unique().sort()
            "${process}:\n${tool_versions.join('\n')}"
        }

    softwareVersionsToYAML(ch_versions.mix(topic_versions.versions_file))
        .mix(topic_versions_string)
        .collectFile(
            storeDir: "${params.outdir}/pipeline_info",
            name:  'sinklink_software_'  + 'mqc_'  + 'versions.yml',
            sort: true,
            newLine: true
        ).set { ch_collated_versions }


    //
    // MODULE: MultiQC
    //
    ch_multiqc_config        = channel.fromPath(
        "$projectDir/assets/multiqc_config.yml", checkIfExists: true)
    ch_multiqc_custom_config = params.multiqc_config ?
        channel.fromPath(params.multiqc_config, checkIfExists: true) :
        channel.empty()
    ch_multiqc_logo          = params.multiqc_logo ?
        channel.fromPath(params.multiqc_logo, checkIfExists: true) :
        channel.empty()

    summary_params      = paramsSummaryMap(
        workflow, parameters_schema: "nextflow_schema.json")
    ch_workflow_summary = channel.value(paramsSummaryMultiqc(summary_params))
    ch_multiqc_files = ch_multiqc_files.mix(
        ch_workflow_summary.collectFile(name: 'workflow_summary_mqc.yaml'))
    ch_multiqc_custom_methods_description = params.multiqc_methods_description ?
        file(params.multiqc_methods_description, checkIfExists: true) :
        file("$projectDir/assets/methods_description_template.yml", checkIfExists: true)
    ch_methods_description                = channel.value(
        methodsDescriptionText(ch_multiqc_custom_methods_description))

    ch_multiqc_files = ch_multiqc_files.mix(ch_collated_versions)
    ch_multiqc_files = ch_multiqc_files.mix(
        ch_methods_description.collectFile(
            name: 'methods_description_mqc.yaml',
            sort: true
        )
    )

    MULTIQC (
        ch_multiqc_files.collect(),
        ch_multiqc_config.toList(),
        ch_multiqc_custom_config.toList(),
        ch_multiqc_logo.toList(),
        [],
        []
    )

    emit:multiqc_report = MULTIQC.out.report.toList() // channel: /path/to/multiqc_report.html
    versions       = ch_versions                 // channel: [ path(versions.yml) ]

}

/*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    THE END
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
*/
