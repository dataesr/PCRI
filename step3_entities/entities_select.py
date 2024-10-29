import pandas as pd, numpy as np
from config_path import PATH_WORK
from step3_entities.ID_getSourceRef import *

def entities_tmp_create(entities_info, countries, ref):
    print("### create ENTITIES TMP pour ref")
    tab = entities_info.merge(countries[['countryCode', 'country_code_mapping', 'country_name_mapping', 'countryCode_parent']], how='left', on='countryCode')
    tmp1 = tab.merge(ref, how='inner', on=['generalPic','country_code_mapping'])
    print(f"longueur entities_info:{len(entities_info)}, longueur de tmp1:{len(tmp1)}, generalPic unique:{len(tmp1.generalPic.unique())}")
    tmp2 = tab.merge(tmp1[['generalPic','country_code_mapping']], how='left',on=['generalPic','country_code_mapping'], indicator=True).query('_merge=="left_only"').drop(columns=['_merge'])
    tmp2 = tmp2.merge(ref.drop(columns='country_code_mapping'), how='inner', on='generalPic')
    tmp1 = pd.concat([tmp1, tmp2], ignore_index=True)
    tmp = tab.merge(tmp1[['generalPic','country_code_mapping']], how='left',on=['generalPic','country_code_mapping'], indicator=True).query('_merge=="left_only"').drop(columns=['_merge'])
    return pd.concat([tmp1, tmp], ignore_index=True)

def entities_and_ref(ref, entities_tmp):
    entities_tmp = entities_tmp[['generalPic', 'legalName', 'businessName', 'country_code_mapping', 'countryCode_parent']]

    # a verifier puisque ref déjà ajouté dans entities_tmp_create()
    entities_tmp = entities_tmp.merge(ref, how='left', on = ['generalPic', 'country_code_mapping'])
    entities_tmp['id'] = entities_tmp.id.replace('', np.nan, regex = True)
    print(f"1 - After add ref to entities: {len(entities_tmp)}\n\n{entities_tmp.columns}")

    if any(entities_tmp.id.str.contains(';')):
        entities_tmp = entities_tmp.assign(id_extend=entities_tmp.id.str.split(';')).explode('id_extend').drop_duplicates()
        entities_size_to_keep = len(entities_tmp)
        print(f"2 - size entities si multi id -> entities_size_to_keep = {entities_size_to_keep}")
    return entities_tmp

def ID_entities_list(ref_source):
    ref = ref_source.loc[(ref_source.FP.str.contains('H20|HE|FP7'))&(~ref_source.id.isnull())].id.str.split(';').explode('id')
    lid=list(ref.drop_duplicates().sort_values())
    print(f"size lid:{len(lid)}")
    lid_source=sourcer_ID(lid)
    unknow_list = set(lid)-set([i['api_id'] for i in lid_source])
    print(f"id non sourcés :{len(unknow_list)}\n{unknow_list}")

    with open(f"{PATH_WORK}list_id_for_ref.pkl", 'wb') as fp:
        pd.to_pickle(lid, fp)
    return lid_source, unknow_list