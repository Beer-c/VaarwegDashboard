# -*- coding: utf-8 -*-
"""
Created on Fri Oct  4 09:08:52 2024

Dashboard vaarwegtellingen

@author: Berend Feddes PZH
"""

import streamlit as st
import pandas as pd
#import folium
#from streamlit_folium import st_folium
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
    jaar_lijst =[2020, 2021, 2022, 2023, 2024, 2025]
    jaar = st.sidebar.selectbox('Jaar', jaar_lijst,len(jaar_lijst)-1)
    t_interval = st.sidebar.radio('Periode',['maand','seizoen','dagsoort','dagdeel'])
    return jaar, t_interval

def display_dataframe(df, Xas, Zas, titel):
       
    df_group = pd.DataFrame({'count' : df.groupby( [Xas, Zas] ).size()}).reset_index()
    
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
     
    #st.dataframe(df_group)
    st.bar_chart(df_group, x= Xas, y= 'count', y_label= 'totaal aantal schepen', color = Zas, stack=False)
    
    aantal_pods = len(df.pod.unique())
    
    # maak een lijst van datums waarop alle pods goed geteld hebben.
    df_group = pd.DataFrame({'count' : df.groupby( [df.index.date,'pod']).size()}).reset_index() # datums waarop een of meer pods geteld hebben.
    df_group_dates = pd.DataFrame({'count' : df_group.groupby(['level_0']).size()}) # tel hoeveel pods op elke datum geteld hebben.
    df_group_dates = df_group_dates.loc[df_group_dates['count']==aantal_pods] # selecteer de dagen waarop alle pods geteld hebben.
    df_group_dates.index = pd.to_datetime(df_group_dates.index)
    
    # bepaal het aantal dagen per maand dat goed gemeten is (om straks het gemiddelde te kunnen berekenen)
    df_months = pd.DataFrame({'count': df_group_dates.index.to_series().resample("M").size()}).reset_index()
    df_months.index = pd.to_datetime(df_months.level_0)
    df_months['maand'] = df_months.index.month
    
    # bepaal het aantal dagen per seizoen dat goed gemeten is
    seizoenen = [[1,2,3],[4,5,6],[7,8],[9,10],[11,12]]
    df_seizoenen =pd.DataFrame(index=np.arange(5), columns=['count'])
    t=0
    for seizoen in seizoenen:
        df_seizoenen.iat[t,0] = df_months['count'].loc[df_months.maand.isin(seizoen)].sum()
        t+=1

    
     # selecteer de metingen op de dagen waarop alle pods werkten
    df_sel = df[df.index.normalize().isin(df_group_dates.index)]
    
   # groepeer per tijdsinterval het aantal schepen, het aantal gemeten dagen en bereken het gemiddelde hiervan
    df_group_sel = pd.DataFrame({'count' : df_sel.groupby( [Xas, Zas] ).size()}).reset_index()
    
    if Xas == 'maand':
        df_group_sel['meetdagen']=df_group_sel.maand
        df_group_sel['meetdagen'] = df_group_sel.meetdagen.replace(df_months['maand'].to_list(), df_months['count'].to_list())
    if Xas =='seizoen':
        df_group_sel['meetdagen']=df_group_sel.seizoen
        df_group_sel['meetdagen'] = df_group_sel.meetdagen.replace(df_seizoenen.index.to_list(), df_seizoenen['count'].to_list())

    df_group_sel['daggem'] = (df_group_sel['count'] / df_group_sel['meetdagen']).astype(int)

    st.bar_chart(df_group_sel, x= Xas, y= 'daggem', y_label= ' gem aantal schepen per dag', color = Zas, stack=False)

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
    jaar, t_interval       = display_tijd_filters()
        
    # maak de selectie van metingen
    df = df_counts[(df_counts['bridge_id']==bridge_id) & (df_counts.index.year==jaar)]
    
    # display data in app
    col1, col2 = st.columns(2)
    with col1:
        display_metrics('brug', bridge_name)
        st.caption('verdeling beroepsvaart / recreatievaart totaal')
        display_dataframe(df, t_interval, 'vaart','')
    with col2:
        display_metrics('jaar', jaar)
        st.caption('verdeling stroomafwaarts / stroomopwaarts totaal')
        display_dataframe(df, t_interval, 'direction','')
    
    st.sidebar.metric('vaartuigen', df.shape[0])
       
    display_pod_data(df, bridge_id, jaar)
    
    
# start hoofdprogramma
seizoen_lijst   = ['1   jan-mrt','2   april-juni','3   juli-aug','4   sept-okt','5   nov-dec']
maand_lijst     = ['01  januari','02  februari','03  maart','04  april','05  mei','06  juni','07  juli',
                 '08  augustus','09  september','10  oktober','11  november','12  december']
dagsoort_lijst  = ['weekdag','weekenddag']
dagdeel_lijst   = ['1 Nacht 22-6 uur', '2 Ochtend 6-14 uur','3 Middag 14-22 uur',]
vaart_lijst     = ['beroepsvaart','recreatievaart']
richting_lijst  = ['stroomafwaarts','stroomopwaarts']



# load data
path = r'./data/bruggen.parquet'
df_brug = pd.read_parquet(path)
df_brug = df_brug.sort_values(by=['name'])

path = r'./data/tellingen.parquet'
df_counts = pd.read_parquet(path)

 # display het dashboard   
if __name__ == '__main__':
    main()