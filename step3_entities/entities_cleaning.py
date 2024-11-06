import pandas as pd, numpy as np

def entities_clean(entities_tmp):
    print("### ENTITIES TMP cleaning name")
    if any(entities_tmp.loc[(entities_tmp.legalName.str.contains("\\00",  na=True))]):
        print(entities_tmp.loc[(entities_tmp.legalName.str.contains("\\00",  na=True))].legalName)

    x=entities_tmp.loc[(entities_tmp.businessName.str.contains("00",  na=True))]
    for i, row in x.iterrows():
        try:
            x.at[i, 'entities_acronym_source'] = row.businessName.replace("\\", "\\u").encode().decode('unicode_escape')
        except:
            x.at[i, 'entities_acronym_source'] = np.nan
    entities_tmp = entities_tmp.loc[~entities_tmp.generalPic.isin(x.generalPic.unique())]
    entities_tmp = pd.concat([entities_tmp, x], ignore_index=True)

    entities_tmp.loc[entities_tmp.entities_acronym_source.str.contains('^\\d+$', na=True), 'entities_acronym_source'] = None
    entities_tmp.loc[entities_tmp.entities_acronym_source.isnull(), 'entities_acronym_source'] = entities_tmp.businessName

    entities_tmp = entities_tmp.assign(entities_name_source = entities_tmp.legalName)

    print(f"- size entities_tmp: {len(entities_tmp)}")

    liste=['entities_name_source', 'entities_acronym_source']
    for i in liste:
        entities_tmp[i] = entities_tmp[i].apply(lambda x: x.capitalize().strip() if isinstance(x, str) else x)
        
    entities_tmp.loc[entities_tmp.entities_name.isnull(), 'entities_name'] = entities_tmp.entities_name_source
    entities_tmp.loc[(entities_tmp.id.isnull())&(entities_tmp.entities_acronym.isnull()), 'entities_acronym'] = entities_tmp.entities_acronym_source

    return entities_tmp

def entities_check_null(entities_tmp):
    print("\n## check entities null")
    for i in ['entities_name', 'entities_id']:
        if len(entities_tmp[entities_tmp[i].isnull()])>0:
            print(f"{len(entities_tmp[entities_tmp[i].isnull()])} {i} manquants\n {entities_tmp[entities_tmp[i].isnull()]}") 

    test=entities_tmp[['entities_id','entities_name', 'entities_acronym']].drop_duplicates()
    test['nb']=test.groupby(['entities_id','entities_name'], dropna=False)['entities_acronym'].transform('count')
    acro_to_delete=test[test.nb>1].entities_id.unique()
    if acro_to_delete.size>0:
        print(acro_to_delete)

    if any(test.entities_id.isnull())|any(test.entities_id=='nan'):
        print(f"{test.loc[(test.entities_id.isnull())|(test.entities_id=='nan')]}")


def entities_info_add(entities_tmp, entities_info):
    print("\n### entities_info + entities_tmp")
    entities_info = (entities_info
        .merge(entities_tmp[['generalPic', 'id', 'ZONAGE', 'id_m', 'siren', 'id_secondaire',
                        'entities_id',  'entities_name', 'entities_acronym', 
                        'entities_name_source', 'entities_acronym_source', 
                        'insee_cat_code', 'insee_cat_name', 
                        'paysage_category', 'paysage_category_id',  'paysage_cj_name', 
                        'ror_category', 'category_woven', 'cj_code',  'sector',  
                        'siret_closeDate',  'siren_cj', 'groupe_sector', 'cat_an']],
        how='inner', on='generalPic'))
    print(f"- size entities_info + entities_tmp: {len(entities_info)}")
    return entities_info

def add_fix_countries(entities_info, countries):
    print("\n### entities_info + countries")
    #ajout des infos country à participants_info
    entities_info = (entities_info
                    .merge(countries[['countryCode', 'country_code_mapping', 'country_name_mapping', 'country_code']], how='left', on='countryCode'))
        
    # correction des ecoles françaises à l'etranger
    l=['951736453','996825642','994591926','996825642','953002303', '998384626', '879924055']
    entities_info.loc[entities_info.generalPic.isin(l), 'country_code'] = 'FRA'
    cc = countries.drop(columns=['countryCode', 'country_name_mapping','country_code_mapping']).drop_duplicates()
    entities_info = (entities_info
                    .merge(cc, how='left', on='country_code')
                    .rename(columns={'ZONAGE':'extra_joint_organization'})
                    .drop(columns=['countryCode_parent',  'lastUpdateDate'])
                    .drop_duplicates())

    print(f"- longueur entities_info après ajout calculated_country : {len(entities_info)}\n{entities_info.columns}\n- columns with Nan\n {entities_info.columns[entities_info.isnull().any()]}")
    return entities_info