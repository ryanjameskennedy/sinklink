//
// Subworkflow with functionality specific to the sinklink pipeline
//

/*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    IMPORT FUNCTIONS / MODULES / SUBWORKFLOWS
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
*/

include { UTILS_NFSCHEMA_PLUGIN     } from '../../nf-core/utils_nfschema_plugin'
include { paramsSummaryMap          } from 'plugin/nf-schema'
include { samplesheetToList         } from 'plugin/nf-schema'
include { paramsHelp                } from 'plugin/nf-schema'
include { completionEmail           } from '../../nf-core/utils_nfcore_pipeline'
include { completionSummary         } from '../../nf-core/utils_nfcore_pipeline'
include { imNotification            } from '../../nf-core/utils_nfcore_pipeline'
include { UTILS_NFCORE_PIPELINE     } from '../../nf-core/utils_nfcore_pipeline'
include { UTILS_NEXTFLOW_PIPELINE   } from '../../nf-core/utils_nextflow_pipeline'

/*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    SUBWORKFLOW TO INITIALISE PIPELINE
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
*/

workflow PIPELINE_INITIALISATION {

    take:
    version           // boolean: Display version and exit
    validate_params   // boolean: Boolean whether to validate parameters against the schema at runtime
    monochrome_logs   // boolean: Do not use coloured log outputs
    nextflow_cli_args //   array: List of positional nextflow CLI args
    outdir            //  string: The output directory where the results will be saved
    input             //  string: Path to input samplesheet
    help              // boolean: Display help message and exit
    help_full         // boolean: Show the full help message
    show_hidden       // boolean: Show hidden parameters in the help message

    main:

    ch_versions = channel.empty()

    //
    // Print version and exit if required and dump pipeline parameters to JSON file
    //
    UTILS_NEXTFLOW_PIPELINE (
        version,
        true,
        outdir,
        workflow.profile.tokenize(',').intersect(['conda', 'mamba']).size() >= 1
    )

    //
    // Validate parameters and generate parameter summary to stdout
    //
    command = "nextflow run ${workflow.manifest.name} -profile <docker/singularity/.../institute> --input samplesheet.csv --metadata metadata.csv --kraken_db <KRAKEN_DB> --schemas_dir <SCHEMAS_DIR> --outdir <OUTDIR>"

    UTILS_NFSCHEMA_PLUGIN (
        workflow,
        validate_params,
        null,
        help,
        help_full,
        show_hidden,
        "",
        "",
        command
    )

    //
    // Check config provided to the pipeline
    //
    UTILS_NFCORE_PIPELINE (
        nextflow_cli_args
    )

    //
    // Create channel from input file provided through params.input, adding the
    // transmission group, growth, schema and expected genome size from params.metadata
    //
    def metadata     = readMetadata(params.metadata)
    def species_map  = readTsv(assetPath(params.species_map, 'species_map.tsv')).collectEntries { row -> [ row.growth, row.schema ] }
    def schema_table = readTsv(assetPath(params.schema_table, 'schemas.tsv')).collectEntries { row -> [ row.schema, row ] }

    channel
        .fromList(samplesheetToList(params.input, "${projectDir}/assets/schema_input.json"))
        .map { meta, fastq_1, fastq_2 ->
            validateInputSamplesheet(meta, fastq_1, fastq_2)
        }
        .map { meta, fastqs ->
            [ annotateSample(meta, metadata, species_map, schema_table), fastqs ]
        }
        .set { ch_samplesheet }

    emit:
    samplesheet = ch_samplesheet
    versions    = ch_versions
}

/*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    SUBWORKFLOW FOR PIPELINE COMPLETION
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
*/

workflow PIPELINE_COMPLETION {

    take:
    email           //  string: email address
    email_on_fail   //  string: email address sent on pipeline failure
    plaintext_email // boolean: Send plain-text email instead of HTML
    outdir          //    path: Path to output directory where results will be published
    monochrome_logs // boolean: Disable ANSI colour codes in log output
    hook_url        //  string: hook URL for notifications
    multiqc_report  //  string: Path to MultiQC report

    main:
    summary_params = paramsSummaryMap(workflow, parameters_schema: "nextflow_schema.json")
    def multiqc_reports = multiqc_report.toList()

    //
    // Completion email and summary
    //
    workflow.onComplete {
        if (email || email_on_fail) {
            completionEmail(
                summary_params,
                email,
                email_on_fail,
                plaintext_email,
                outdir,
                monochrome_logs,
                multiqc_reports.getVal(),
            )
        }

        completionSummary(monochrome_logs)
        if (hook_url) {
            imNotification(summary_params, hook_url)
        }
    }

    workflow.onError {
        log.error "Pipeline failed. Please refer to troubleshooting docs: https://nf-co.re/docs/usage/troubleshooting"
    }
}

/*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    FUNCTIONS
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
*/

//
// Validate channels from input samplesheet
//
def validateInputSamplesheet(meta, fastq_1, fastq_2) {
    if (meta.platform == 'nanopore' && fastq_2) {
        error("Please check input samplesheet -> Nanopore samples take fastq_1 only: ${meta.id}")
    }
    def single_end = !fastq_2
    def fastqs = single_end ? [ fastq_1 ] : [ fastq_1, fastq_2 ]
    return [ meta + [ single_end: single_end ], fastqs ]
}

//
// A table from --schema_table, --species_map or --qc_thresholds, or the copy in assets/
//
def assetPath(value, name) {
    return value ?: "${projectDir}/assets/${name}"
}

//
// The reference genome files for each sample whose schema has one: [ meta, [ fasta, fai, gff, gbff ] ]
//
def referenceChannel(ch_samples, references_dir) {
    return ch_samples
        .map { meta, _reads -> meta }
        .filter { meta -> meta.reference }
        .map { meta ->
            def prefix = "${references_dir}/${meta.reference}"
            [ meta, [ file("${prefix}.fasta"), file("${prefix}.fasta.fai"), file("${prefix}.gff"), file("${prefix}.gbff") ] ]
        }
        .filter { meta, files ->
            def missing = files.findAll { f -> !f.exists() }
            if (missing) {
                log.warn("Reference genome files ${missing*.name.join(', ')} for ${meta.id} are not in ${references_dir} (run make references); its reference-based steps are skipped")
            }
            !missing
        }
}

//
// Read a TSV file with a header into a list of maps
//
def readTsv(path) {
    return file(path, checkIfExists: true).splitCsv(header: true, sep: '\t')
}

//
// Read the study metadata (sample, transmission, growth, ...) keyed by sample
//
def readMetadata(path) {
    def rows = file(path, checkIfExists: true).splitCsv(header: true)
    def missing = [ 'sample', 'transmission', 'growth' ].findAll { column -> !rows || !rows[0].containsKey(column) }
    if (missing) {
        error("Please check the metadata file -> missing column(s): ${missing.join(', ')}")
    }
    return rows.collectEntries { row -> [ row.sample, row ] }
}

//
// Add the transmission group, growth label, schema, expected genome size and reference genome
// accession to a sample's meta map
//
def annotateSample(meta, metadata, species_map, schema_table) {
    def row = metadata[meta.id]
    if (!row) {
        log.warn("Sample ${meta.id} is not in the metadata file; it is assembled and QC'd only")
    }
    def growth = row?.growth ?: ''
    def schema = species_map[growth] ?: ''
    if (row && !schema) {
        log.warn("Sample ${meta.id} has no schema for growth '${growth}'; add it to the species map to call alleles")
    }
    def genome_size = ''
    if (schema) {
        def size_min = schema_table[schema].genome_size_min_mb as Double
        def size_max = schema_table[schema].genome_size_max_mb as Double
        genome_size = String.format('%.1fm', (size_min + size_max) / 2)
    }
    return meta + [
        transmission: row?.transmission ?: '',
        growth      : growth,
        schema      : schema,
        genome_size : genome_size,
        reference   : schema ? (schema_table[schema].reference ?: '') : '',
        mlst_scheme : schema ? (schema_table[schema].mlst_scheme ?: '') : ''
    ]
}

//
// Generate methods description for MultiQC
//
def toolCitationText() {
    def citation_text = [
            "Tools used in the workflow included:",
            params.skip_host_removal ? "" : "Deacon (Constantinides et al. 2025),",
            params.trim ? "Trimmomatic (Bolger et al. 2014)," : "",
            params.filtlong ? "Filtlong (Wick 2017)," : "",
            "FastQC (Andrews 2010),",
            "NanoPlot (De Coster et al. 2018),",
            "SKESA (Souvorov et al. 2018),",
            "Flye (Kolmogorov et al. 2019),",
            "Medaka (Oxford Nanopore Technologies),",
            "QUAST (Gurevich et al. 2013),",
            params.gambit_db ? "gambitcore with the GAMBIT database (Lumpe et al. 2023)," : "",
            "BWA (Li 2013),",
            "minimap2 (Li 2018),",
            "SAMtools (Danecek et al. 2021),",
            "mlst (Seemann),",
            "Kraken2 (Wood et al. 2019), Bracken (Lu et al. 2017),",
            params.references_dir ? "Mash (Ondov et al. 2016), skani (Shaw and Yu 2023)," : "",
            params.skip_variant_calling ? "" : "Snippy (Seemann 2015) with FreeBayes (Garrison and Marth 2012), Clair3 (Zheng et al. 2022), MUMmer (Marçais et al. 2018), PhiSpy (Akhter et al. 2012), mosdepth (Pedersen and Quinlan 2018), BCFtools (Danecek et al. 2021), Gubbins (Croucher et al. 2015), snp-dists (Seemann),",
            params.skip_chewbbaca ? "" : "chewBBACA (Silva et al. 2018),",
            params.skip_report ? "" : "Matplotlib (Hunter 2007),",
            "MultiQC (Ewels et al. 2016)",
            "."
        ].join(' ').trim()

    return citation_text
}

def toolBibliographyText() {
    def reference_text = [
            params.skip_host_removal ? "" : "<li>Constantinides B, Lees J, Crook DW. (2025) Deacon: fast sequence filtering and contaminant depletion. bioRxiv. doi: 10.1101/2025.06.09.658732</li>",
            params.trim ? "<li>Bolger AM, Lohse M, Usadel B. (2014) Trimmomatic: a flexible trimmer for Illumina sequence data. Bioinformatics 30(15):2114-2120. doi: 10.1093/bioinformatics/btu170</li>" : "",
            params.filtlong ? "<li>Wick R. (2017) Filtlong, URL: https://github.com/rrwick/Filtlong</li>" : "",
            "<li>Andrews S, (2010) FastQC, URL: https://www.bioinformatics.babraham.ac.uk/projects/fastqc/).</li>",
            "<li>De Coster W, et al. (2018) NanoPack: visualizing and processing long-read sequencing data. Bioinformatics 34(15):2666-2669. doi: 10.1093/bioinformatics/bty149</li>",
            "<li>Souvorov A, Agarwala R, Lipman DJ. (2018) SKESA: strategic k-mer extension for scrupulous assemblies. Genome Biol 19:153. doi: 10.1186/s13059-018-1540-z</li>",
            "<li>Kolmogorov M, et al. (2019) Assembly of long, error-prone reads using repeat graphs. Nat Biotechnol 37:540-546. doi: 10.1038/s41587-019-0072-8</li>",
            "<li>Gurevich A, et al. (2013) QUAST: quality assessment tool for genome assemblies. Bioinformatics 29(8):1072-1075. doi: 10.1093/bioinformatics/btt086</li>",
            "<li>Li H. (2018) Minimap2: pairwise alignment for nucleotide sequences. Bioinformatics 34(18):3094-3100. doi: 10.1093/bioinformatics/bty191</li>",
            "<li>Danecek P, et al. (2021) Twelve years of SAMtools and BCFtools. GigaScience 10(2):giab008. doi: 10.1093/gigascience/giab008</li>",
            "<li>Wood DE, Lu J, Langmead B. (2019) Improved metagenomic analysis with Kraken 2. Genome Biol 20:257. doi: 10.1186/s13059-019-1891-0</li>",
            "<li>Lu J, et al. (2017) Bracken: estimating species abundance in metagenomics data. PeerJ Comput Sci 3:e104. doi: 10.7717/peerj-cs.104</li>",
            params.references_dir ? "<li>Ondov BD, et al. (2016) Mash: fast genome and metagenome distance estimation using MinHash. Genome Biol 17:132. doi: 10.1186/s13059-016-0997-x</li>" : "",
            params.references_dir ? "<li>Shaw J, Yu YW. (2023) Fast and robust metagenomic sequence comparison through sparse chaining with skani. Nat Methods 20:1661-1665. doi: 10.1038/s41592-023-02018-3</li>" : "",
            params.skip_variant_calling ? "" : "<li>Seemann T. (2015) Snippy: fast bacterial variant calling from NGS reads, URL: https://github.com/tseemann/snippy</li>",
            params.skip_variant_calling ? "" : "<li>Garrison E, Marth G. (2012) Haplotype-based variant detection from short-read sequencing. arXiv:1207.3907</li>",
            params.skip_variant_calling ? "" : "<li>Zheng Z, et al. (2022) Symphonizing pileup and full-alignment for deep learning-based long-read variant calling. Nat Comput Sci 2:797-803. doi: 10.1038/s43588-022-00387-x</li>",
            params.skip_variant_calling ? "" : "<li>Marçais G, et al. (2018) MUMmer4: A fast and versatile genome alignment system. PLoS Comput Biol 14(1):e1005944. doi: 10.1371/journal.pcbi.1005944</li>",
            params.skip_variant_calling ? "" : "<li>Akhter S, Aziz RK, Edwards RA. (2012) PhiSpy: a novel algorithm for finding prophages in bacterial genomes that combines similarity- and composition-based strategies. Nucleic Acids Res 40(16):e126. doi: 10.1093/nar/gks406</li>",
            params.skip_variant_calling ? "" : "<li>Pedersen BS, Quinlan AR. (2018) Mosdepth: quick coverage calculation for genomes and exomes. Bioinformatics 34(5):867-868. doi: 10.1093/bioinformatics/btx699</li>",
            params.skip_variant_calling ? "" : "<li>Croucher NJ, et al. (2015) Rapid phylogenetic analysis of large samples of recombinant bacterial whole genome sequences using Gubbins. Nucleic Acids Res 43(3):e15. doi: 10.1093/nar/gku1196</li>",
            params.skip_variant_calling ? "" : "<li>Seemann T. snp-dists: pairwise SNP distance matrix from a FASTA sequence alignment, URL: https://github.com/tseemann/snp-dists</li>",
            params.skip_chewbbaca ? "" : "<li>Silva M, et al. (2018) chewBBACA: A complete suite for gene-by-gene schema creation and strain identification. Microb Genom 4(3):e000166. doi: 10.1099/mgen.0.000166</li>",
            params.skip_report ? "" : "<li>Hunter JD. (2007) Matplotlib: A 2D graphics environment. Comput Sci Eng 9(3):90-95. doi: 10.1109/MCSE.2007.55</li>",
            "<li>Ewels, P., Magnusson, M., Lundin, S., & Käller, M. (2016). MultiQC: summarize analysis results for multiple tools and samples in a single report. Bioinformatics , 32(19), 3047–3048. doi: /10.1093/bioinformatics/btw354</li>"
        ].join(' ').trim()

    return reference_text
}

def methodsDescriptionText(mqc_methods_yaml) {
    // Convert  to a named map so can be used as with familiar NXF ${workflow} variable syntax in the MultiQC YML file
    def meta = [:]
    meta.workflow = workflow.toMap()
    meta["manifest_map"] = workflow.manifest.toMap()

    // Pipeline DOI
    if (meta.manifest_map.doi) {
        // Using a loop to handle multiple DOIs
        // Removing `https://doi.org/` to handle pipelines using DOIs vs DOI resolvers
        // Removing ` ` since the manifest.doi is a string and not a proper list
        def temp_doi_ref = ""
        def manifest_doi = meta.manifest_map.doi.tokenize(",")
        manifest_doi.each { doi_ref ->
            temp_doi_ref += "(doi: <a href=\'https://doi.org/${doi_ref.replace("https://doi.org/", "").replace(" ", "")}\'>${doi_ref.replace("https://doi.org/", "").replace(" ", "")}</a>), "
        }
        meta["doi_text"] = temp_doi_ref.substring(0, temp_doi_ref.length() - 2)
    } else meta["doi_text"] = ""
    meta["nodoi_text"] = meta.manifest_map.doi ? "" : "<li>If available, make sure to update the text to include the Zenodo DOI of version of the pipeline used. </li>"

    // Tool references
    meta["tool_citations"] = toolCitationText().replaceAll(", \\.", ".").replaceAll("\\. \\.", ".").replaceAll(", \\.", ".")
    meta["tool_bibliography"] = toolBibliographyText()


    def methods_text = mqc_methods_yaml.text

    def engine =  new groovy.text.SimpleTemplateEngine()
    def description_html = engine.createTemplate(methods_text).make(meta)

    return description_html.toString()
}
