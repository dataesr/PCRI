import zipfile, json, re, os
import pandas as pd, numpy as np
from config_path import PATH_WORK, PATH_ODS

# load json file in a zipfile
def unzip_zip(namezip, path, data, encode):
    if 'json' in data:
        with zipfile.ZipFile(f"{path}{namezip}", 'r', metadata_encoding=encode) as z:
            return json.load(z.open(data, 'r'))
    if 'csv' in data:
        with zipfile.ZipFile(f"{path}{namezip}", 'r', metadata_encoding=encode) as z:
            return pd.read_csv(z.open(data), low_memory=False, dtype='str')


#convert column of lists in strings column
def del_list_in_col(df, var_old:str, var_new:str):
    df[var_new] = None
    for i, row in df.iterrows():
        if row[var_old]!=[]:
            df.at[i, var_new] = "|".join(str(e) for e in row[var_old] if e is not None)
    return df.drop(var_old, axis=1)

def work_csv(df, file_csv_name):
    name = file_csv_name
    return df.to_csv(f"{PATH_WORK}{name}.csv", sep=';', na_rep='', encoding='utf-8', index=False)

def website_to_clean(web_var: str):
    pat=re.compile(r"((((https|http)://)?(www\.)?)([\w\d#@%;$()~_?=&]+\.)+([a-z]{2,3}){1}([\w\d:#@%/;$()~_?\+-=\\\.&]+))")
    y= re.search(pat, str(web_var))
    if y is not None:
        return y.group()
    
def columns_comparison(df, namefile):
    old_cols = np.load(f"data_files/{namefile}.npy").tolist()
    new_cols = df.columns.to_list()
    if any(set(new_cols) - set(old_cols)):
        print(f"- new cols: {set(new_cols) - set(old_cols)}")
    else:
        print("- no new columns")

def gps_col(df):
    print("#FCT gps_col")
    df=df.assign(gps_loc=None)
    for i,row in df.iterrows():
        if row.loc['location'].get('latitude') is not None:
            df.at[i, 'gps_loc'] = re.search(r'^-?\d+\.?\d{,5}', str(row.loc['location'].get('latitude')))[0]+ "," +re.search(r'^-?\d+\.?\d{,5}', str(row.loc['location'].get('longitude')))[0]
    return df.drop('location', axis=1).drop_duplicates()  

def num_to_string(var):
    try:
        float(var)
        return var.astype(int, errors='ignore').astype(str).replace('.0', '')
    except:
        return str(var).replace('.0', '')
    
def erc_role(df, projects):
    print("### ERC ROLE")
    proj_erc = projects.loc[projects.thema_code=='ERC', ['project_id', 'destination_code', 'action_code']]
    df = df.merge(proj_erc, how='left', on='project_id').drop_duplicates()
    df = df.assign(erc_role='partner')

    if 'app1' in globals():
        df.loc[(df.destination_code=='SyG')&((df.partnerType=='host')|(df.role=='coordinator')), 'erc_role'] = 'PI'
    elif 'part' in globals():
        df.loc[(df.destination_code=='SyG')&(df.partnerType=='beneficiary')&(pd.to_numeric(df.orderNumber, errors='coerce')<5.), 'erc_role'] = 'PI'
    
    df.loc[(df.destination_code!='SyG')&(df.role=='coordinator'), 'erc_role'] = 'PI'
    df.loc[(df.destination_code=='ERC-OTHERS'), 'erc_role'] = np.nan
    df = df.drop(columns=['destination_code', 'action_code']).drop_duplicates()       
    print(f"- size after erc_role: {len(df)}")
    return df

def bugs_excel(df, chemin, name_sheet):
    print("#FCT bugs_excel")
    chemin=f"{chemin}bugs_found.xlsx"
    if not os.path.exists(chemin):
        with pd.ExcelWriter(chemin) as writer:
            df.to_excel(writer, sheet_name=name_sheet)
    else:
        with pd.ExcelWriter(chemin, mode='a', if_sheet_exists='replace') as writer:
            df.to_excel(writer, sheet_name=name_sheet)

def order_columns(df, xl_sheetname):
    import pandas as pd
    xl_path = f"{PATH_ODS}colonnes_ordres_par_jeux_ods.xlsx"
    colorder = pd.read_excel(xl_path, sheet_name=xl_sheetname, dtype={'order':int})
    colorder=colorder.sort_values('order')
    colorder=colorder.vars.unique()
    return df.reindex(columns=colorder)


def zipfile_ods(df, file_export):
    import zipfile
    with zipfile.ZipFile(f'{PATH_ODS}{file_export}.zip', 'w', compression=zipfile.ZIP_DEFLATED) as z:
        with z.open(f'{file_export}.csv', 'w', force_zip64=True) as f:
            df.to_csv(f, sep=';', encoding='utf-8', index=False, na_rep='', decimal=".")


def entreprise_cat_cleaning(df):

    df.loc[(df.flag_entreprise==True)&(~df.groupe_id.isnull()), 'entities_id'] = df.groupe_id
    df.loc[(df.flag_entreprise==True)&(~df.groupe_id.isnull()), 'entities_name'] = df.groupe_name
    if 'groupe_acronym' in df.columns:
        df.loc[(df.flag_entreprise==True)&(~df.groupe_id.isnull())&(~df.entities_acronym.isnull()), 'entities_acronym'] = df.groupe_acronym
        df.loc[(df.flag_entreprise==True)&(~df.groupe_id.isnull())&(df.groupe_acronym.isnull()), 'entities_acronym'] = np.nan
    df.loc[(df.entities_id.str.contains('^gent', na=False))&(df.insee_cat_code.isnull()), 'insee_cat_code'] = 'GE'
    df.loc[(df.entities_id.str.contains('^gent', na=False))&(df.insee_cat_name.isnull()), 'insee_cat_name'] = 'Grandes entreprises'
    for i in ['groupe_id', 'groupe_name', 'groupe_acronym']:
        if i in df.columns:
            df = df.drop(columns=i)
    df = df.rename(columns={'insee_cat_code':'entreprise_type_code',
            'insee_cat_name':'entreprise_type_name'})
    return df

def tokenization(text):
    if isinstance(text, str):
        tokens = text.split()
        return tokens
