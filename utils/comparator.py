def compare_ids(adit_ids, edi_ids):
    only_adit = sorted(adit_ids - edi_ids)
    only_edi = sorted(edi_ids - adit_ids)
    common = sorted(adit_ids & edi_ids)
    difference = sorted(
        [f"{id} (ADIT)" for id in only_adit] + 
        [f"{id} (EDI)" for id in only_edi]
    )

    return {
        "only_adit": only_adit,
        "only_edi": only_edi,
        "common": common,
        "difference": difference
    }