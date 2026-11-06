//
// chewBBACA AlleleCall, one job per schema with all of that schema's assemblies
//

include { CHEWBBACA_ALLELECALL } from '../../../modules/nf-core/chewbbaca/allelecall/main'

workflow ALLELE_CALLING {

    take:
    ch_assembly // channel: [ val(meta), path(fasta) ]
    schemas_dir // string: folder holding <schema>/alleles_rereffed

    main:
    ch_assembly
        .filter { meta, _fasta -> meta.schema }
        .map { meta, fasta -> [ meta.schema, fasta ] }
        .groupTuple()
        .map { schema, fastas -> [ schema, fastas, file("${schemas_dir}/${schema}/alleles_rereffed") ] }
        .filter { schema, _fastas, schema_dir ->
            if (!schema_dir.exists()) {
                log.warn("Schema ${schema} is not set up in ${schemas_dir} (run make ${schema}_all); its isolates are not allele called")
            }
            schema_dir.exists()
        }
        .multiMap { schema, fastas, schema_dir ->
            fasta : [ [ id: schema ], fastas ]
            schema: [ [ id: schema ], schema_dir ]
        }
        .set { ch_allelecall }

    CHEWBBACA_ALLELECALL ( ch_allelecall.fasta, ch_allelecall.schema )

    emit:
    alleles = CHEWBBACA_ALLELECALL.out.alleles // channel: [ val(meta), path(tsv) ]
    stats   = CHEWBBACA_ALLELECALL.out.stats   // channel: [ val(meta), path(tsv) ]
}
