import folium
import streamlit as st
import pandas as pd
from folium.features import GeoJsonPopup, GeoJsonTooltip
import folium
from streamlit_folium import st_folium
import plotly.express as px
import geopandas as gpd
import matplotlib.pyplot as plt
import altair as alt
import os
import scipy.stats as stats
import numpy as np
import math
from folium.features import DivIcon
import warnings


pd.options.mode.chained_assignment = None

st.set_page_config(layout="wide")


df_final = gpd.read_file('https://raw.githubusercontent.com/AndersAags/Visualization/main/df_geometry_random_data.geojson')


df_final.rename(columns={'Y19_Muni': 'Municipality', 
                         'v_all': 'Average number of contacts',
                         'edu': 'Proportion of patients with primary school',
                         'retired': 'Retired', 
                         'unempl': 'Patients unemployed', 
                         'CCI_index': 'Average Charlson Index',                      
                         'Y19_Muni': 'Municipality'
                         }, inplace=True)

feature_list =  [
     "Average number of contacts", 
     "Average Charlson Index",
     "Patients unemployed",
     "Retired",
     "Proportion of patients with primary school"     
     ]

#%%

# Set the theme using set_config
st.set_config(
    {
        "theme": "custom",
        "primaryColor": "#8B0000",
        "backgroundColor": "#BABDBB",
        "secondaryBackgroundColor": "#23392C",
        "textColor": "#FFFFFF",
        "font": "sans serif"
    }
)


#%% 
# st.title("Overskrift", color="#FF0000", align="center")

tab_main, tab_compare_map = st.tabs(["Main overview", "Compare maps"])

with tab_main:
    
    with st.sidebar:
        year = st.radio(
            "Choose one of the following years", df_final["year"].unique(), index=3
        )  # index first year
        year_filter_df = df_final[df_final.year == year]  # temp year df
        df_final['year'] = df_final['year'].fillna(year)
        map_filter = st.selectbox(
            "Filter the map by the following features:",
            df_final[feature_list
            ].columns,
        )
    
    col1, col2 = st.columns([2,1])
    with col1:
        icone1 = folium.Icon(icon="asterisk", icon_color="#9b59b6", color="lightblue")
        icon_hz = dict(prefix='fa', color='red', icon_color='darkred', icon='cny')    
        
        test_data = year_filter_df
        test_data = test_data.dropna()
        test_data = test_data.reset_index(level=None)
        
        location = test_data[['visueltcenter_y', 'visueltcenter_x']]
        location = location.values.tolist()
        
        def create_map(map_name, data, select_col):
            
                # Set up Choropleth map
                map_name = folium.Map(location=[56.2, 11.8], zoom_start=7)
                folium.TileLayer('CartoDB positron',name="Light Map",control=False).add_to(map_name)
                
                ## Set up Choropleth map
                folium.Choropleth(
                geo_data=data, 
                data=data,
                columns=['kode',select_col],
                key_on="feature.properties.kode",
                fill_color='Reds',
                # fill_opacity=1,
                # line_opacity=1,
                legend_name=select_col,
                # smooth_factor=1,
                Highlight= True,
                line_color = "#0000",
                name = select_col,
                show=False,
                overlay=True,
                nan_fill_color = "darkblack"
                ).add_to(map_name)
                

                geojson1 = folium.features.GeoJson(
                    data=year_filter_df,
                    name=select_col,
                    smooth_factor=0.1,
                    style_function=lambda x: {"color": "black", "fillColor": "Reds", "weight": 0.5}, 
                    tooltip=folium.features.GeoJsonTooltip(
                        fields=["Municipality", select_col],
                        aliases=["Municipality: ", select_col],
                        localize=True,
                        sticky=False,
                        labels=True,
                        max_width=800,
                    ),
                    highlight_function=lambda x: {"weight": 3, "fillColor": "red"},
                ).add_to(map_name)
            
                return map_name
        
        map1 = create_map("map1", df_final, map_filter)
        
        st_map = st_folium(map1, width=700, height=600, key = 'map1')

        # last click
        muni_name = 'Esbjerg Municipality' #default kommune
        if st_map['last_active_drawing']:
            muni_name = st_map['last_active_drawing']['properties']['Municipality'] 
        unique_muni = list(df_final['Municipality'].unique())
        
    # dropper geometry i ny df
    year_filter_df = df_final.loc[
        :, df_final.columns != "geometry"
    ]  # removing geodata from the dataframe
    year_filter_df = year_filter_df[
        year_filter_df["year"] == year
    ]  # taking a subset of the dataframe fro the chosen year
    with col2:
        df_analyse = df_final.loc[:, df_final.columns != "geometry"]
        selected_mun = st.selectbox(
            label="Municipality",
            options=unique_muni,
            index=unique_muni.index(  # "start" værdi når side opdateres (hvis last_draw - så det)
                muni_name
            ),
        )
    
        if selected_mun:
            filtered_bar = df_analyse[df_analyse["Municipality"] == selected_mun]
            base = (
                alt.Chart(filtered_bar)
                .mark_bar()
                .encode(
                    alt.X(f"{'year'}:O", title=selected_mun),
                    color=alt.condition(
                        alt.datum.year == 2016,
                        alt.value("darkred"),
                        alt.value("darkred"),
                    ),
                )
                .properties(height=250, width=300,)
                .interactive()
            )
            charts1 = alt.hconcat(
                base.encode(y=f"{map_filter}:Q").properties(title=f"{map_filter}")
            )
            if filtered_bar.isnull().values.any():
                st.error(
                    "You have chosen a municipality that has no information due to GDPR reasons"
                )
            else:
                st.altair_chart(charts1)
    
#%%

    # # Multiselect municipality
    st.subheader("Analyze the features")
    column1, column2 = st.columns([1, 2], gap="small")
    with column1:
        st.markdown("Investigate a variety stats for each municipality in a given year")
        plot_y = st.selectbox(
            "Which attribute do you want to analyze?", options=df_final[feature_list
            ].columns,
            index = feature_list.index(map_filter)
            )
            #df_analyse.keys()
            
        
        chosen_year = st.selectbox(
            "Which measure do you want to analyze?", options=df_analyse["year"].unique(),
            index = 3
        )
        plot_x = st.multiselect(
            "which municipality do you want to investigate further",
            options=df_analyse["Municipality"].unique(),
            default=muni_name,  # "start" værdi når side opdateres (hvis last_draw - så det)
        )
        chart_data = df_analyse[df_analyse["year"] == chosen_year]
        chart_data_muni = chart_data[chart_data["Municipality"].isin(plot_x)]
    
    with column2:
        chart1 = (
            alt.Chart(chart_data_muni)
            .mark_bar(color="darkred")
            .encode(x="Municipality:O", y=f"{plot_y}:Q",)
            .properties(height=400, width=600,)
            .interactive()
        )
    
        st.altair_chart(chart1)
    
#%%

    # feature_list_top10 = year_filter_df[feature_list]
    feature_list_top10 = feature_list
    feature_list_top10 = feature_list_top10.copy()
    feature_list_top10 += ["Municipality"]
    
    st.header("Top 10")

    options_top10 = year_filter_df[feature_list_top10]
    
    dataframe_top10 = year_filter_df[feature_list_top10]
    
    chosen_interaction = st.multiselect(
        label="Please select a type of interaction",
        options=options_top10.keys(),
        default=map_filter,
    )
    # sorting argument
    sort_arg = st.radio("How do you want the sorting", ["Descending", "Ascending"], index=0)
    
    
    # CSS to inject contained in a string
    hide_table_row_index = """
                <style>
                thead tr th:first-child {display:none}
                tbody th {display:none}
                </style>
                """
    
    # Inject CSS with Markdown
    st.markdown(hide_table_row_index, unsafe_allow_html=True)
    st.write("Keep in mind that the table is sorted by the second column")
    if chosen_interaction:
        chosen_interaction.insert(0, "Municipality")
        if sort_arg == "Descending":
            dataframe1 = dataframe_top10[chosen_interaction].sort_values(
                by=chosen_interaction[1], ascending=False
            )[:10]
            st.table(dataframe1.style.format(precision=2))
        else:
            dataframe2 = dataframe_top10[chosen_interaction].sort_values(
                by=chosen_interaction[1], ascending=True
            )[:10]
            st.table(dataframe2.style.format(precision=2,))
    else:
        st.error("You have to choose at least one interaction type")

#%%


with tab_compare_map:
    year_filter_df = df_final[df_final.year==year]

    map_1, map_2 = st.columns([1,1])
    with map_1:
        map_filter1 = st.selectbox(
            "Select feature for map 1:",
            options = df_final[feature_list
            ].columns,
            key = 'sb_2',
            index = 4 # retired
    )

        map2 = create_map("map2", df_final, map_filter1)
            
        st_map2 = st_folium(map2, width=700, height=600, key = 'map_2')
        
    with map_2:
        map_filter3 = st.selectbox(
            "Select feature for map 2:", 
            options = df_final[feature_list
            ].columns,
            key = 'sb_3',
            index = 2 # CCI
    )
        
        map3 = create_map("map3", df_final, map_filter3)
        
        st_map3 = st_folium(map3, width=700, height=600, key = 'map_3')


        
#%%


