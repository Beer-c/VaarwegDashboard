# -*- coding: utf-8 -*-
"""
Created on Fri Oct  4 09:08:52 2024

Dashboard vaarwegtellingen

@author: Berend Feddes PZH
"""

import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import numpy as np

APP_TITLE = 'Vaarwegtellingen'
APP_SUBTITLE = 'Provincie Zuid-Holland'

def display_metrics(label, value):
    st.metric(label=label+": ", value=value)
    
def display_brug(df_brug):
    bridge_name = st.sidebar.selectbox('Brug',df_brug.name,10)
    bridge_id = df_brug.id.loc[df_brug['name']==bridge_name]
    return int(bridge_id), bridge_name
    
def display_tijd_filters():
    jaar_lijst =['', 2021, 2022, 2023, 2024, 2025]
    jaar = st.sidebar.selectbox('Jaar', jaar_lijst,len(jaar_lijst)-1)
    
    maand_lijst=['','januari', 'februari','maart','april','mei','juni',
                 'juli','augustus','september','oktober','november','december']
    maand = st.sidebar.multiselect('Maand', maand_lijst,
                                   help('selecteer een of meerder maanden'))
    return jaar, maand

def display_seizoen():
    seizoen_lijst = ['januari-maart','april-juni',
                 'juli-augustus','september-oktober','november-december']
    seizoen = st.sidebar.selectbox('Seizoen',seizoen_lijst,4)
    return seizoen

def display_dagdeel():
    dagdeel = st.sidebar.selectbox('Dagdeel',['','Ochtend 6-14 uur','Middag 14-22 uur','Nacht 22-6 uur'])
    return dagdeel

def display_dagsoort():
    dagsoort = st.sidebar.radio('Dagsoort',['werkdag','weekend','allebei'])
    return dagsoort

def display_vaarsoort():
    vaarsoort = st.sidebar.radio('Soort vaart',['beroepsvaart','recreatievaart','allebei'])
    return vaarsoort

def display_richting():
    richting = st.sidebar.radio('Richting',['stroom op','stroom af','allebei'])
    return richting

def display_dataframe(df, bridge_id, jaar):
    seizoen_lijst = ['1   jan-mrt','2   april-juni','3   juli-aug','4   sept-okt','5   nov-dec']
    maand_lijst = ['1  januari','2  februari','3  maart','4  april','5  mei','6  juni','7  juli',
                   '8  augustus','9  september','10  oktober','11  november','12  december']
    df_group = pd.DataFrame({'count' : df.groupby( [ "seizoen", "dagsoort"] ).size()}).reset_index()
    
    if 'seizoen' 
    df_group.seizoen = df_group.seizoen.replace([0, 1, 2, 3, 4], seizoen_lijst)
    
    
    st.dataframe(df_group)
    st.bar_chart(df_group, x="seizoen", y= 'count', y_label= 'aantal schepen', color="dagsoort", stack=False)

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
            lijst = pd.date_range(start, end).difference(df.index.date)
            
            df_kalender = pd.DataFrame(index=np.arange(52), columns=['ma','di','wo','do','vr','za','zo'])
            df_kalender.index.name ='week'
            df_kalender.index+=1
            df_kalender[::] = '1'
                
            for index, datum in enumerate(lijst):
                df_kalender.iat[datum.week-1,datum.weekday()] = '0'
                
            with cols[col]:
                st.write('boat sense pod: ',pod)
                st.dataframe(df_kalender.style.map(pod_kleur))
                
            col+=1
            


def main():
    st.set_page_config(APP_TITLE, layout='wide')
    st.title(APP_TITLE)
    st.caption(APP_SUBTITLE)
    
    # display filters in sidebar
    bridge_id, bridge_name = display_brug(df_brug)
    jaar, maand = display_tijd_filters()
    seizoen = display_seizoen()
    dagsoort = display_dagsoort()
    dagdeel = display_dagdeel()
    vaarsoort = display_vaarsoort()
    richting = display_richting()
    
    # maak de selectie van metingen
    df = df_counts[(df_counts['bridge_id']==bridge_id) & (df_counts.index.year==jaar)]
        
    # display data in app
    col1, col2, col3 = st.columns(3)
    with col1:
        display_metrics('brug', bridge_name)
    with col2:
        display_metrics('jaar', jaar)
    with col3:
        display_metrics('vaartuigen', df.shape[0])
       
        
    display_dataframe(df, bridge_id, jaar)
    display_pod_data(df, bridge_id, jaar)
    
    
# start hoofdprogramma

# load data
path = r'./data/bruggen.parquet'
df_brug = pd.read_parquet(path)
df_brug = df_brug.sort_values(by=['name'])

path = r'./data/tellingen.parquet'
df_counts = pd.read_parquet(path)

 # display het dashboard   
if __name__ == '__main__':
    main()