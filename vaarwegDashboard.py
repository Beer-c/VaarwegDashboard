# -*- coding: utf-8 -*-
"""
Created on Fri Oct  4 09:08:52 2024

Dashboard vaarwegtellingen

@author: Berend Feddes PZH
"""

import streamlit as st
from streamlit_folium import st_folium
import pandas as pd
from pyogrio import read_dataframe
from pyogrio import write_dataframe
import folium
import numpy as np


APP_TITLE = 'Vaarwegtellingen'
APP_SUBTITLE = 'Provincie Zuid-Holland'
APP_TEXT = 'Bij verschillende bruggen zijn in de periode 2022-2025 vaartuigtellingen uitgevoerd als onderdeel van een pilot. Van deze metingen zijn hier de gemiddelden berekend, per maand en per seizoen. Het onderscheid tussen beroeps en recreatievaart is alleen gebaseerd op de lengte van het schip (langer of korter dan 37m) en is dus een benadering. Omdat de pilot een experimenteel karakter had is de data (soms) sterk gefragmenteerd. In het algemeen mag worden uitgegaan van een lichte onderschatting van het aantal passages (orde grootte 10%).'

def kalender(jaar):
    start_date = date(jaar, 1, 1)
    end_date   = date(jaar, 12, 31)

    df_index = pd.date_range(start_date, end_date, freq='D')
    df =pd.DataFrame(columns = ['maand','weekdag','dagsoort'], index = df_index)
    df['maand'] = df_index.month
    df['weekdag']= df_index.weekday
    df['dagsoort'] = np.select([df.weekdag<5],['WD'],'WK')
    return df.groupby(['maand','dagsoort']).size().reset_index(level=[1]).rename(columns={0:'#dagen'})
        
def kalenderTabel(df_totaal, jaar):
    df_kalender = kalender(jaar)
    df_kalender['maandnr'] = df_kalender.index
    df_totaal['maandnr'] = df_totaal.index
    df_meetres= df_kalender.merge(df_totaal, how = 'left', left_on=['dagsoort','maandnr'],
    right_on=['dagsoort','maandnr']).fillna(0)
    df_meetres = df_meetres.rename(columns={"maandnr": "maand"})
    df_meetres['meetdagen %'] = (df_meetres['meetdagen']/df_meetres['#dagen']*100).round(1)
    df_meetres[['meetdagen','meetdagen %','totaal']]= df_meetres[['meetdagen','meetdagen %','totaal']].astype(int)
    df_meetres = df_meetres [['maand','dagsoort','#dagen','meetdagen','meetdagen %','totaal','gem/dag']]
    return df_meetres    
        
def display_metrics(label, value):
    st.metric(label=label+": ", value=value)
    
def display_brug(df_brug):
    bridge_name = st.sidebar.selectbox('Brug',df_brug.bridge_name,10)
    bridge_id = df_brug.id.loc[df_brug['bridge_name']==bridge_name]
    return int(bridge_id), bridge_name
    
def display_tijd_filters():
    jaar = st.sidebar.selectbox('Jaar', jaar_lijst,len(jaar_lijst)-1)
    t_interval = st.sidebar.radio('Periode',['maand','seizoen'])
    return jaar, t_interval

def display_groepeer():
    groepeer = st.sidebar.radio('Groepeer totalen bij',['dagsoort','dagdeel','geen'])
    groepeer = None if groepeer=='geen' else groepeer
    return groepeer

def display_stack():
    stack = st.sidebar.radio('Kolommen',['stapelen','naast elkaar'])
    return (stack=='stapelen')

def display_grafiek_totaal(df, Xas, vaart, Zas, stack):
    
    # selecteer de waarnemingen in de goedgekeurde weken
    df = df[df.vaart==vaart]
    
    voorwaarde = [Xas] if Zas is None else [Xas,Zas]   
    df_group = pd.DataFrame({'count' : df.groupby(voorwaarde).size()}).reset_index()
    df_group = legenda(df_group)
    #st.write(df_group)
    st.bar_chart(df_group, x= Xas, y= 'count', y_label= 'totaal aantal schepen', color = Zas, stack=stack)
    
def display_grafiek_gem(df, jaar, Xas, vaart, Zas, stack):
           
    # selecteer de waarnemingen in de goedgekeurde weken
    df = df[df.vaart==vaart]
    
    # bepaal totaal aantal schepen per maand per WD/WK
    df_totaal = df[['dagsoort','bridge_id']].groupby(['dagsoort', pd.Grouper(level=0, freq='M')]).agg({'bridge_id':'size'}).reset_index()
    
    # bepaal totaal aantal meetdagen per maand per WD/WK
    df['datum']= df.index.normalize()
    df_uniek= df.drop_duplicates(subset=['datum'])
    df_aantal = df_uniek.groupby(['dagsoort', pd.Grouper(level=0, freq='M')]).agg({'bridge_id':'size'}).reset_index()
    df_totaal = df_totaal.merge(df_aantal, how='left', on = ['dagsoort','Timestamp'])
    df_totaal = df_totaal.rename(columns={"bridge_id_x": "totaal", "bridge_id_y": "meetdagen"})
    
    # bereken het gemiddelde per maand per WD/WK
    df_totaal['gem/dag'] = (df_totaal.totaal / df_totaal.meetdagen).round(1) 
    df_totaal['maand'] = df_totaal.Timestamp.dt.month
        
    # Voeg het seizoen toe per WD/WK
    df_totaal['seizoen'] = df_totaal['maand']
    df_totaal['seizoen'] = df_totaal['seizoen'].replace([1,2,3,4,5,6,7,8,9,10,11,12], [0,0,0,1,1,1,2,2,3,3,4,4])
      
    if Xas == 'seizoen':
        #df_seizoen = pd.DataFrame({'gem': df_totaal.groupby(['seizoen','dagsoort'])['gem'].mean().round(1)}) 
        df_seizoen = pd.DataFrame({'meetdagen': df_totaal.groupby(['seizoen','dagsoort'])['meetdagen'].sum(),
                                   'totaal': df_totaal.groupby(['seizoen','dagsoort'])['totaal'].sum(),
                                   'gem/dag': df_totaal.groupby(['seizoen','dagsoort'])['gem/dag'].mean().round(1)
                                   })
        df_totaal= df_seizoen.reset_index(level=['seizoen','dagsoort'])

    if Xas == 'maand':    
        #df_totaal = kalenderTabel(df_totaal, jaar)          
        #df_totaal = legenda (df_totaal)
        st.bar_chart(df_totaal, x= Xas, y= 'gem/dag', y_label= ' gem aantal schepen per dag', color= 'dagsoort',stack=stack)
        df_totaal.index = df_totaal.maand if (Xas == 'maand') else df_totaal.seizoen
        df_totaal = df_totaal.drop(columns=['Timestamp','maand','seizoen']) if Xas == ('maand') else df_totaal.drop(columns=['seizoen'])
        st.write(df_totaal)

def pod_kleur(val):
    color = 'green' if int(val) else 'red'
    return f'background-color: {color}'

    
def display_pod_data(df, bridge_id, jaar):
    if df.shape[0] == 0:
        st.write('geen boat sense data beschikbaar voor', jaar)
        
    else:     
        pods = df.pod.unique()
        aantal_pods = len(pods)
        cols = st.columns(aantal_pods)
        col = 0
        
        for pod in pods:
            start = str(jaar)+'-01-01'
            end =   str(jaar)+'-12-31'
            lijst = pd.date_range(start, end).difference(df.index.date)  # lijst dagen waarop een pod niks gemeten heeft
            
            df_kalender = pd.DataFrame(index=np.arange(52), columns=['ma','di','wo','do','vr','za','zo'])
            df_kalender.index.name ='week'
            df_kalender.index+=1
            df_kalender[::] = '1'
                
            for index, datum in enumerate(lijst):
                df_kalender.iat[datum.week-1,datum.weekday()] = '0'
                
            with cols[col]:
                st.write('boat sense pod: ',pod)
                st.dataframe(df_kalender.style.map(pod_kleur), height=1860)
                
            col+=1
            
def legenda(df_group):
    kolommen = df_group.columns.to_list() 
    if 'seizoen' in kolommen:
        df_group.seizoen = df_group.seizoen.replace([0, 1, 2, 3, 4], seizoen_lijst)
    if 'maand' in kolommen:
        df_group.maand = df_group.maand.replace([1, 2, 3, 4, 5, 6,7, 8, 9, 10, 11, 12], maand_lijst)
    if 'dagsoort' in kolommen:
        df_group.dagsoort = df_group.dagsoort.replace(['WD','WK'], dagsoort_lijst)
    if 'dagdeel' in kolommen:
        df_group.dagdeel = df_group.dagdeel.replace([0,1,2], dagdeel_lijst)
    if 'vaart' in kolommen:
        df_group.vaart = df_group.vaart.replace(['B','R'], vaart_lijst)
    if 'direction' in kolommen:
        df_group.direction = df_group.direction.replace(['D','U'], richting_lijst)
    #st.write(df_group,)
    return df_group

# functie kaart met verkeersborden maken en opslaan
def MaakKaart(gdf_vaarwegen, df_brug):
  
    # interactieve kaart maken en opslaan
    kaart = folium.Map(location=(52.060211, 4.499377), zoom_control=False)

    #bruggen op de kaart zetten
    brug_icon = 'https://images.trafficsupply.nl/imgfill/800/800/i-114415-2d2/verkeersbord-sb250-a9-beweegbare-brug'
   
    for index, row in df_brug.iterrows():
        tooltip = row['bridge_name']
        popup = 'hectometer '+str(row['hectometer'])
        icon = folium.features.CustomIcon(brug_icon, icon_size=(30,30))
        folium.Marker([row['latitude'], row['longitude']], popup = popup, icon = icon, tooltip = tooltip).add_to(kaart)

    # vaarwegen op de kaart zetten
    for index, row in gdf_vaarwegen.iterrows():
        locations = row['Polyline']
        tooltip = row['tooltip']
        color = row['color']
        folium.PolyLine(locations=locations, color=color, weight=5, tooltip=tooltip).add_to(kaart)
        
    st.map = st_folium(kaart, width = 700, height = 450)

# functie die x,y omdraait voor de polyline die gebruikt wordt in Folium map
def switch_LatLon (lijnstringLatLon):
    x,y = lijnstringLatLon.xy
    lijnstringLonLat = list(zip(list(y), list(x)))
    return lijnstringLonLat    


def main():
    st.set_page_config(APP_TITLE, layout='wide')
    st.title(APP_TITLE)
    st.caption(APP_SUBTITLE)
    st.text(APP_TEXT)
    
    # display filters in sidebar
    bridge_id, bridge_name = display_brug(df_brug)
    jaar, t_interval       = display_tijd_filters()
    groepeer               = display_groepeer()
    stack                  = display_stack()
            
    # maak de selectie van metingen
    df = df_counts[(df_counts['bridge_id']==bridge_id) & (df_counts.index.year==jaar)]
    aantal_pods = len(df.pod.unique())
    
    # maak een lijst van datums waarop alle pods goed geteld hebben.
    df_group = pd.DataFrame({'count' : df.groupby( [df.index.date,'pod']).size()}).reset_index() # datums waarop een of meer pods geteld hebben.
    df_group_dates = pd.DataFrame({'count' : df_group.groupby(['level_0']).size()}) # tel hoeveel pods op elke datum geteld hebben.
    df_group_dates = df_group_dates.loc[df_group_dates['count']==aantal_pods] # selecteer de dagen waarop alle pods geteld hebben.
    df_group_dates.index = pd.to_datetime(df_group_dates.index) # stel de datetime index in 
    df_group_dates['week'] = df_group_dates.index.isocalendar().week 
    df_weken = pd.DataFrame({'count' : df_group_dates.groupby(['week']).size()})
    df_weken = df_weken[df_weken>5].dropna() # selecteer de weken waarop 6 of meer dagen geteld is
    weken_lijst = df_weken.index.to_list()
    
    # selecteer de waarnemingen in de goedgekeurde weken
    df = df[df.index.isocalendar().week.isin(weken_lijst)]

    
    # display data in app
    col1, col2 = st.columns(2)
    with col1:
        display_metrics('brug', bridge_name)
        st.caption('beroepsvaart totaal')
        display_grafiek_totaal(df, t_interval, 'B', groepeer, stack)
        st.caption('beroepsvaart daggemiddelde')
        display_grafiek_gem(df, jaar, t_interval, 'B', groepeer, stack)
    with col2:
        display_metrics('jaar', jaar)
        st.caption('recreatievaart totaal')
        display_grafiek_totaal(df, jaar, t_interval, 'R', groepeer, stack)
        st.caption('recreatievaart daggemiddelde')
        display_grafiek_gem(df, t_interval, 'R', groepeer, stack)
            
    link = df_brug.loc[df_brug['id']==bridge_id].link.to_list()
    st.sidebar.image(link[0])
    st.sidebar.metric('vaartuigen', df.shape[0])
        
    MaakKaart(gdf_vaarwegen, df_brug)
    display_pod_data(df, bridge_id, jaar)
    
    
# start hoofdprogramma
seizoen_lijst   = ['1   jan-mrt','2   april-juni','3   juli-aug','4   sept-okt','5   nov-dec']
maand_lijst     = ['01  januari','02  februari','03  maart','04  april','05  mei','06  juni','07  juli',
                 '08  augustus','09  september','10  oktober','11  november','12  december']
dagsoort_lijst  = ['werkdag','weekenddag']
dagdeel_lijst   = ['1 Nacht 22-6 uur', '2 Ochtend 6-14 uur','3 Middag 14-22 uur',]
vaart_lijst     = ['beroepsvaart','recreatievaart']
richting_lijst  = ['stroomafwaarts','stroomopwaarts']



# load data
path = r'./data/bruggen.parquet'
df_brug = pd.read_parquet(path)
df_brug = df_brug.sort_values(by=['bridge_name'])

path = r'./data/vaarwegen/vaarwegenPZH.shp'
gdf_vaarwegen = read_dataframe(path, use_arrow=True)

path = r'./data/tellingen.parquet'
df_counts = pd.read_parquet(path)

jaar_lijst =df_counts.index.year.unique().sort_values()

# bewerk het vaarwegenbestand
gdf_vaarwegen.crs="EPSG:28992" # bestand heeft RDS coordinaten
gdf_vaarwegen = gdf_vaarwegen.to_crs(epsg = 4326) # omzetten naar WG84 coordinaten
gdf_vaarwegen['Polyline'] = gdf_vaarwegen.apply(lambda row: switch_LatLon(row.geometry), axis=1 ) #polylines maken van linestrings
gdf_vaarwegen['tooltip'] = gdf_vaarwegen.VRT_CODE+'  '+gdf_vaarwegen.VRT_NAAM
gdf_vaarwegen['color'] = '#0000FF' # kleurcode blauw


 # display het dashboard   
if __name__ == '__main__':
    main()