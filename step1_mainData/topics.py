# table topics'''

from constant_vars import ZIPNAME, FRAMEWORK
from config_path import PATH_SOURCE
import pandas as pd

def topics_divisions(chemin):
    from functions_shared import unzip_zip
    import pandas as pd

    data = unzip_zip(ZIPNAME, chemin, 'topics.json', 'utf8')
    print(f'1 - topics -> {len(data)}')
    topics = pd.DataFrame(data)[["topicCode","topicDescription"]].drop_duplicates() 

    # DIVISIONS 
    data = unzip_zip(ZIPNAME, chemin, 'topicLbDivisions.json', 'utf8')
    print(f'2 - divisions -> {len(data)}')

    df = pd.DataFrame(data).drop(['lastUpdateDate'], axis=1)
    df['tmp'] = np.where(df.isPrincipal == True, 1 , 0)
    table = pd.pivot_table(df,index=['topicCode'],columns=['divisionAbbreviation'],values=['tmp'],aggfunc=pd.Series.nunique,margins=True,dropna=True)
    if [table['tmp']['All']>1]==True:
        pd.DataFrame(table).to_csv("/he_data/traitement_topic_horizon.csv", sep=";", encoding="utf-8", na_rep="")
        print('3 - verifier les doublons topic/division isPrincipal dans he_data/traitement_topic_horizon.csv')

    df = df[df.isPrincipal == True]
    df = df.dropna(axis=1, how='all').drop(['lvl1Code','lvl1Description','isPrincipal','tmp'], axis=1).drop_duplicates()

    topics_divisions = df.merge(topics, how='left', on='topicCode')

    divisions = df[['lvl2Code', 'lvl2Description', 'lvl3Code', 'lvl3Description', 'lvl4Code', 'lvl4Description']].drop_duplicates()

#     with open(f"data_json/destination.json", 'r+', encoding='UTF-8') as fp:
#         data = json.load(fp)
    destination = pd.read_json(open('data_json/destination.json', 'r+', encoding='utf-8'))
    destination = pd.DataFrame(destination).drop(columns='dest_h20')

    ########################################################

    #ERC
    ERC = topics_divisions.loc[topics_divisions['lvl3Code']=="HORIZON.1.1", ['topicCode']].assign(thema_code='ERC')
    typ = ["POC", "COG", "STG", "ADG", "PERA", "SyG", "SJI"]

    for i in typ:
        ERC.loc[ERC.topicCode.str.contains(i), 'destination_code'] = i

    if any(pd.isna(ERC.destination_code.unique())):
        print(f'erc : destination_code à null après traitement\n{ERC[ERC.destination_code.isnull()].topicCode.unique()}')
        ERC.loc[ERC.destination_code.isnull(), 'destination_code'] = 'ERC-OTHERS'

    ############################################################################
    # MSCA
    MSCA = topics_divisions.loc[topics_divisions['lvl3Code']=="HORIZON.1.2", ['topicCode']].assign(thema_code='MSCA')
    typ = ["COFUND", "SE", "PF", "DN","CITIZENS"]

    for i in typ:
        MSCA.loc[MSCA.topicCode.str.contains(i), 'destination_code'] = i

    if any(pd.isna(MSCA.destination_code.unique())):
        print(f'MSCA : destination_code à null après traitement\n{MSCA[MSCA.destination_code.isnull()].topicCode.unique()}')
        MSCA.loc[MSCA.destination_code.isnull(), 'destination_code'] = 'MSCA-OTHERS'  

    #######################################################################################################""
    #INFRA
    INFRA = topics_divisions.loc[topics_divisions['lvl3Code']=="HORIZON.1.3", ['topicCode']].assign(thema_code='INFRA')
    inf={'EOSC':'INFRAEOSC',
    'DEV':'INFRADEV',
    'SERV':'INFRASERV',
    'TECH':'INFRATECH',
    '-NET-':'INFRANET'
    }

    for k,v in inf.items():
        INFRA.loc[INFRA.topicCode.str.contains(k), 'destination_code'] = v
    if any(pd.isna(INFRA.destination_code.unique())):
        print(f'INFRA : destination_code à null après traitement\n{INFRA[INFRA.destination_code.isnull()].topicCode.unique()}')
        INFRA.loc[INFRA.destination_code.isnull(), 'destination_code'] = 'DESTINATION-OTHERS'

    # ####################################################################################


    # # CLUSTER

    CLUSTER = topics_divisions.loc[(topics_divisions.lvl2Code=='HORIZON.2')&(topics_divisions.topicCode.str.contains('-CL\\d{1}-|-HLTH-', regex=True))]
    CLUSTER = CLUSTER[['topicCode']]

    CLUSTER['destination_code'] = CLUSTER['topicCode'].str.split('-').str.get(3)
    CLUSTER.loc[~CLUSTER.destination_code.isin(destination.destination_code.unique()), 'destination_code'] = np.nan

    cl={'-HLTH-':'HEALTH-OTHERS',
    '-CL2-':'CCSI-OTHERS',
    '-CL3-':'CSS-OTHERS',
    '-CL4-':'DIS-OTHERS',
    '-CL5-':'CEM-OTHERS',
    '-CL6-':'BIOENV-OTHERS'
    }
    for k,v in cl.items():
        CLUSTER.loc[(CLUSTER.destination_code.isnull())&(CLUSTER.topicCode.str.contains(k)), 'destination_code'] = v
    if any(pd.isna(CLUSTER.destination_code.unique())):
        print('CLUSTER : attention encore destination_code à null après traitement')

    CLUSTER['temp']=CLUSTER.topicCode.str.split('-').str.get(1)
    l_cluster=pd.DataFrame.from_dict({'HLTH':'CLUSTER 1', 'CL2':'CLUSTER 2', 'CL3':'CLUSTER 3', 'CL4':'CLUSTER 4','CL5':'CLUSTER 5', 'CL6':'CLUSTER 6'}, orient='index', columns=['thema_code']).reset_index()
    CLUSTER = CLUSTER.merge(l_cluster, how='left', left_on='temp', right_on='index').drop(columns=['index', 'temp'])

    mask=(CLUSTER.thema_code=='CLUSTER 4')
    CLUSTER.loc[mask&(CLUSTER.destination_code.isin(['RESILIENCE','TWIN'])), 'thema_code'] = CLUSTER.thema_code+'-Industry'
    CLUSTER.loc[mask&(CLUSTER.destination_code.isin(['DATA','DIGITAL','HUMAN'])), 'thema_code'] = CLUSTER.thema_code+'-Digital'
    CLUSTER.loc[mask&(CLUSTER.destination_code.isin(['SPACE'])), 'thema_code'] = CLUSTER.thema_code+'-Space'

    mask=(CLUSTER.thema_code=='CLUSTER 5')
    CLUSTER.loc[mask&(CLUSTER.destination_code.isin(['D'+str(i) for i in range(1, 2)])), 'thema_code'] = CLUSTER.thema_code+'-Climate'
    CLUSTER.loc[mask&(CLUSTER.destination_code.isin(['D'+str(i) for i in range(2, 5)])), 'thema_code'] = CLUSTER.thema_code+'-Energy'
    CLUSTER.loc[mask&(CLUSTER.destination_code.isin(['D'+str(i) for i in range(5, 7)])), 'thema_code'] = CLUSTER.thema_code+'-Mobility'


    ################################################################
    #### autres pilier 2


    # MISSION
    miss = (topics_divisions
            .loc[(topics_divisions.lvl2Code=='HORIZON.2')&(topics_divisions.topicCode.str.contains('MISS')),
                 ['topicCode','lvl3Code']]
            .assign(thema_code='MISSION'))

    m={"OCEAN":"HORIZON.2.6",
       "SOIL":"HORIZON.2.6",
       "CIT":"HORIZON.2.5",
       "CLIMA":"HORIZON.2.5",
       "CANCER":"HORIZON.2.1",
       "UNCAN":"HORIZON.2.1"}

    for k,v in m.items():
        pattern=str("^"+k)
        mask = (miss.topicCode.str.split('-').str[3].str.contains(pattern, na=True))
        miss.loc[mask, 'destination_code'] = k
        miss.loc[mask, 'programme_code'] = v

    miss.loc[miss.destination_code=="UNCAN", 'destination_code'] = "CANCER"

    if any((miss.thema_code=='MISSION')&(miss.destination_code.isnull())):
        miss.loc[miss.destination_code.isnull(), 'destination_code'] = 'MISS-OTHERS' 
        miss.loc[miss.programme_code.isnull(), 'programme_code'] = miss.lvl3Code 

    ########################################################################

    # JU-JTI
    spec={
    'JU':'JU-JTI',
    'JTI':'JU-JTI',
    'EUSPA':'EUSPA',
    'SESAR':'JU-JTI'
    }

    top = topics_divisions.loc[(topics_divisions.lvl2Code=='HORIZON.2')&(topics_divisions.topicCode.str.contains('|'.join([*spec]))), ['topicCode']]

    for k,v in spec.items():
        top.loc[top.topicCode.str.contains(k), 'thema_code'] = v
    if any(pd.isna(top.thema_code.unique())):
        print('top_hor2 : thema_code à null après traitement')

    top = top.assign(destination_code=np.nan)
    for i in ['SESAR', 'CLEAN-AVIATION', 'IHI', 'KDT', 'CBE', 'EDCTP3', 'EUROHPC', 'SNS', 'ER', 'Chips']:  
        pattern=str(i+"-")
        mask = (top.thema_code=='JU-JTI')&(top.destination_code.isnull())&(top.topicCode.str.contains(pattern))
        top.loc[mask, 'destination_code'] = i

    for i in ['CLEANH2']:  
        pattern=str("-"+i+"-")
        mask = (top.thema_code=='JU-JTI')&(top.destination_code.isnull())&(top.topicCode.str.contains(pattern))
        top.loc[mask, 'destination_code'] = i

    top.loc[top.destination_code=='KDT', 'destination_code'] = 'Chips'    

    top.loc[top.thema_code=='EUSPA', 'destination_code'] = 'EUSPA'


    if any(pd.isna(top.destination_code.unique())):
        print(f'top_hor2 : destination_code à null après traitement\n{top[top.destination_code.isnull()]}')
        top.loc[top.destination_code.isnull(), 'destination_code'] = 'DESTINATION-OTHERS'

    # #############################################################################################################
    # horizon 3
    HOR3 = topics_divisions.loc[topics_divisions.lvl2Code=='HORIZON.3', ['topicCode', 'lvl3Code']]

    spec={'PATHFINDER':'PATHFINDER',
    'BOOSTER':'TRANSITION',
    'TRANSITION':'TRANSITION',
    'ACCELERATOR':'ACCELERATOR',   
    'CONNECT':'CONNECT',
    'SCALEUP':'SCALEUP',
    'INNOVSMES':'INNOVSMES',   
    'CLIMATE':'KIC-CLIMATE',
    'DIGITAL':'KIC-DIGITAL',
    'HEALTH':'KIC-HEALTH',
    'FOOD':'KIC-FOOD',
    'MANUFACTURING':'KIC-MANUFACTURING',
    'URBANMOBILITY':'KIC-URBANMOBILITY',
    'RAWMATERIALS':'KIC-RAWMATERIALS',
    'INNOENERGY':'KIC-INNOENERGY',
    'CCSI':'KIC-CCSI'
    }


    for k,v in spec.items():
        HOR3.loc[HOR3.topicCode.str.contains(k), 'destination_code'] = v
    if any(pd.isna(HOR3.destination_code.unique())):
        print(f"HOR3 : destination_code à null après traitement\n{HOR3[HOR3.destination_code.isnull()].sort_values('topicCode').topicCode.unique()}")
        HOR3.loc[HOR3.destination_code.isnull(), 'destination_code'] = 'DESTINATION-OTHERS'
     #####################################################################################

    # horizon 4
    HOR4 = topics_divisions.loc[topics_divisions.lvl2Code=='HORIZON.4', ['topicCode', 'lvl3Code']]
    spec={
    'ACCESS':'ACCESS',
    'TALENTS':'TALENTS',
    'TECH':'INFRATECH',
    'COST':'COST',
    'EURATOM':'EURATOM',
    'GENDER':'GENDER',
    '-ERA-':'ERA'
    }

    for k,v in spec.items():
        HOR4.loc[HOR4.topicCode.str.contains(k), 'destination_code'] = v
    if any(pd.isna(HOR4.destination_code.unique())):
        print(f"HOR4 : destination_code à null après traitement\n{HOR4[HOR4.destination_code.isnull()].sort_values('topicCode').topicCode.unique()}")
        HOR4.loc[HOR4.destination_code.isnull(), 'destination_code'] = 'DESTINATION-OTHERS'

    # ########
    #thema_code pour HOR3 et 4
    tab = pd.concat([HOR3, HOR4], ignore_index=True)

    # autres themas que horizon 2
    thema_other={'HORIZON.1.3':'INFRA',
            'HORIZON.3.1':'EIC',
            'HORIZON.3.2':'EIE',
            'HORIZON.3.3':'EIT',
            'HORIZON.4.1':'Widening',
            'HORIZON.4.2':'ERA'}

    # remplir thema
    for k,v in thema_other.items():
        tab.loc[tab.lvl3Code==k, 'thema_code'] = v
    tab.drop(columns='lvl3Code', inplace=True)
    ##############################################################################

    # add niveau prog pilier
    horizon = (topics_divisions
               .rename(columns={"lvl2Code": "pilier_code", "lvl2Description": "pilier_name_en", "lvl3Code": "programme_code", 
                                "lvl3Description": "programme_name_en",'topicDescription': 'topic_name'})
              .drop(columns=['lvl4Code','lvl4Description', 'divisionAbbreviation', 'divisionDescription', 'framework'])) 


    #traitement des programmes hors mission
    tab = pd.concat([tab, CLUSTER, top, INFRA, ERC, MSCA], ignore_index=True)
    tab = tab.merge(horizon, how='inner', on='topicCode')
    tab = tab.mask(tab == '')

    # traitement niveau programme pour les MISSIONS
    miss = (miss
            .merge(horizon[['topicCode', 'topic_name']], how='left', on='topicCode')
            .merge(horizon[['pilier_code', 'pilier_name_en', 'programme_code', 'programme_name_en']], 
                   how='left', on='programme_code')
            .drop(columns='lvl3Code')
            .drop_duplicates())

    tab = pd.concat([tab, miss], ignore_index=True)  
    tab = tab.mask(tab == '')

    # traitement thema_code -> null
    reste = horizon.loc[~horizon.topicCode.isin(tab.topicCode.unique())]
    tab = pd.concat([tab, reste], ignore_index=True) 
    tab.loc[tab.thema_code.isnull(), 'thema_code'] = 'THEMA-OTHERS'

#     with open(f"data_json/thema.json", 'r+', encoding='UTF-8') as fp:
#         data = json.load(fp)
    thema_lib = pd.read_json(open('data_json/thema.json', 'r+', encoding='utf-8'))
    thema_lib = pd.DataFrame(thema_lib)

    tab = tab.merge(thema_lib, how='left', on='thema_code')
    tab.loc[tab.thema_name_en.isnull(), 'thema_name_en'] = tab.programme_name_en
    tab = tab.merge(destination, how='left', on='destination_code')

#     with open('data_json/programme_fr.json', 'r+', encoding='UTF-8') as fp:
#                 data = json.load(fp)
    data = pd.read_json(open('data_json/programme_fr.json', 'r+', encoding='utf-8'))
    data=pd.DataFrame(data)


    tab = tab.merge(data[['programme_code','programme_name_fr']], how='left',on='programme_code')
    tab = tab.merge(data[['pilier_code','pilier_name_fr']], how='left', on='pilier_code')

    tab.loc[(tab.thema_name_fr.isnull()), 'thema_name_fr'] = tab['programme_name_fr']

    if not tab.columns[tab.isnull().any()].empty:
        print(f"attention des cellules sont vides dans horizon: {tab.columns[tab.isnull().any()]}")


    for i in tab.columns:
        if tab[i].dtype == 'object':
            tab[i] = tab[i].map(str.strip, na_action='ignore')
        else:
            pass
    return tab



def merged_topics(df):
    topics= topics_divisions(f"{PATH_SOURCE}{FRAMEWORK}/")

    top_code = list(set(df.topicCode))
    top_code = [item for item in top_code if not(pd.isnull(item)) == True]
    topics = (topics[topics['topicCode'].isin(top_code)]
            .drop_duplicates())

    # création du champs DESTINATION = lib+code
    topics.loc[(topics.destination_code.str.contains('^HORIZON', regex=True)) | (topics.destination_code.isnull()), 'destination'] = topics.thema_code
    topics.loc[(topics.destination.isnull())&(~topics.destination_code.isnull())&(topics.destination_lib.isnull()), 'destination'] = topics.destination_code
    topics.loc[(topics.destination.isnull())&(~topics.destination_code.isnull())&
                (~topics.destination_code.str.replace('-',' ').isin(topics.destination_lib.str.upper())), 'destination'] = topics['destination_lib']+" - "+topics['destination_code']

    topics.loc[(topics.destination.isnull())&(~topics.destination_lib.isnull())&
                (topics.destination_code.str.replace('-',' ').isin(topics.destination_lib.str.upper())), 'destination'] = topics.destination_lib

    y=topics.loc[topics.destination.isnull(), ['destination_lib','destination_code', 'destination']].drop_duplicates()
    if len(y)>1:
        print(y)

    df = (df
            .merge(pd.DataFrame(topics), how='left', on='topicCode')
            .drop_duplicates()
            .drop(columns='destination_code')
            .rename(columns={'destination':'destination_code', 'topicCode':'topic_code'}))
    print(f"size merged after add topics: {len(df)}")


    if len(df[df['programme_code'].isnull()])>0:
        print(f"ATTENTION ! programme_code manquant")

    return df
    # topics.to_csv(f"{PATH_CONNECT}topics_current.csv", index=False, encoding="UTF-8", sep=";", na_rep='')