import pandas as pd
import fastf1
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import requests
import time

fastf1.Cache.enable_cache('FastF1_cache')


def convert_to_time_format(seconds):
    if pd.isna(seconds):
        return "N/A"
    minutes = int(seconds // 60)
    secs = seconds % 60
    return f"{minutes}:{secs:.4f}"

def retrive_driver_img(driver):
    race_results = st.session_state['race_data']['race_results']
    driver_img = race_results.loc[race_results['FullName'] == driver, 'HeadshotUrl'].iloc[0]
    driver_img = driver_img.replace('1col','3col')
    if driver_img is None:
        url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{driver}"
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            driver_img =  data.get('thumbnail', {}).get('source', None)
            return driver_img
    else:
        return driver_img

def set_page_config():
    st.set_page_config(page_title="F1 Dashboard", layout="wide")
    st.markdown(
        """
        <style>
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
        </style>
        """, unsafe_allow_html=True
    )

def retrive_choice_race():
    col1,col2,col3 = st.columns([10,15,10])
    with col2:
        st.header("F1 Analytics Dashboard 🏎️")
        st.divider()
        st.subheader("Select Race")
        excel_data = pd.read_excel('race.xlsx')
        year_select = st.selectbox("Year", options=sorted(excel_data['Year'].unique(), reverse=True))
        df_year = excel_data[excel_data['Year'] == year_select]
            
        race_select = st.selectbox("Race", options=df_year['Grand Prix'].unique().tolist())

        if st.button("Retrieve Results"):
            progress_bar = st.progress(0)

            for percent_complete in range(35):
                time.sleep(0.02)
                progress_bar.progress(percent_complete + 1)

            race = fastf1.get_session(int(year_select), race_select, 'R')
            race.load(laps=True, telemetry=False, weather=True, messages=False)
            progress_bar.progress(75)
            st.session_state['race_data'] = {
                'race': race,
                'session_info': race.session_info,
                'race_results': race.results,
                'weather_data': race.weather_data if race.weather_data is not None else None,
                'laps': race.laps,
                'circuit_info': race.get_circuit_info()
            }
            progress_bar.progress(100)
            time.sleep(1)
            st.rerun()


def set_race_name_flag(session_info):
    col1, col2 = st.columns([10, 1])
    with col1:
        st.markdown(f'<p style="font-size: 52px;font-weight: bold;"><u>{session_info["Meeting"].get("OfficialName", session_info["Meeting"].get("Name"))}<u></p>', unsafe_allow_html=True)

    with col2:
        country_name = session_info['Meeting']['Country']['Name']
        if 'race_flag' not in st.session_state:
            try:
                response = requests.get(f"https://restcountries.com/v3.1/name/{country_name}")
                if response.status_code == 200:
                    country_data = response.json()
                    flag_url = country_data[0]['flags']['png']
                    st.session_state['race_flag'] = flag_url
                else:
                    st.write("Country flag not found or an error occurred.")
            except:
                st.write("Country flag not found or an error occurred.")
        if 'race_flag' in st.session_state:
            st.markdown(
                f"""
                <div style="border: 2px solid black; display: inline-block;">
                    <img src="{st.session_state['race_flag']}" width="150">
                </div>
                """,
                unsafe_allow_html=True
            )

def set_race_info_results(session_info, race, race_results, race_weather, laps, circuit_info):
    race_info, race_result = st.columns(2)

    with race_info:
        st.header("Race Details")
        st.write(f"**Country**: {session_info['Meeting']['Country']['Name']}")
        st.write(f"**Circuit**: {session_info['Meeting']['Circuit']['ShortName']}")
        st.write(f"**Start Time**: {session_info['StartDate']}")
        st.write(f"**End Time**: {session_info['EndDate']}")
        st.write(f"**Total Laps**: {race.total_laps}")

        st.header("Weather Information")
        if race_weather is not None:
            col1, col2 = st.columns(2)
            with col1:
                st.write(f"**Average AirTemp** : {race_weather['AirTemp'].mean():.2f} °C")
                st.write(f"**Average Windspeed** : {race_weather['WindSpeed'].mean():.2f} m/s")
            with col2:
                st.write(f"**Average TrackTemp** : {race_weather['TrackTemp'].mean():.2f} °C")
                st.write(f"**Average Humidity** : {race_weather['Humidity'].mean():.2f} %")
            st.write(f"**Rainfall** : {race_weather['Rainfall'].sum():.2f} mm")
        else:
            st.write("Weather information not available")

        st.header("Circuit Information")
        col1, col2 = st.columns(2)

        with col1:
            st.write(f"**Total No of Corners**: {len(circuit_info.corners)} ")
            st.write(f"**Total No of Marshal Sectors**: {len(circuit_info.marshal_sectors)} ")

        with col2:
            if 'circuit_image' not in st.session_state:
                wiki_api_url = f"https://en.wikipedia.org/w/api.php?action=query&titles={session_info['Meeting']['Name']}&prop=pageimages&format=json&pithumbsize=250"
                response = requests.get(wiki_api_url).json()
                pages = response['query']['pages']
                image_url = None
                for page_id in pages:
                    if 'thumbnail' in pages[page_id]:
                        image_url = pages[page_id]['thumbnail']['source']
                if image_url:
                    st.session_state['circuit_image'] = image_url
                else:
                    st.write("No image available")

            if 'circuit_image' in st.session_state:
                st.image(st.session_state['circuit_image'])

    with race_result:
        st.header("Race Results")
        st.markdown(f"<p style='font-size: 20px'>Winner: {race_results['FullName'].iloc[0]}<p>", unsafe_allow_html=True)

        # st.write(f"**Fastest Lap**: {fastest_lap_driver} ({formatted_time})")

        race_results_display = race_results[['Position', 'DriverNumber', 'Abbreviation', 'FullName', 'TeamName', 'CountryCode', 'Points']].reset_index(drop=True)
        race_results_display.set_index('Position', inplace=True)
        st.table(race_results_display)
    
    st.divider()

def set_race_events(laps):
    st.header("Race Events")
    track_st_data = laps[laps['DriverNumber'] == laps['DriverNumber'].iloc[0]][['LapNumber', 'TrackStatus']]
    track_st_cond = {
            '1': 'Track clear',
            '2': 'Yellow flag',
            '4': 'Safety Car',
            '5': 'Red Flag',
            '6': 'Virtual Safety Car',
            '7': 'Virtual Safety Car ending'
    }
    track_st_data['Track Condition'] = track_st_data['TrackStatus'].map(track_st_cond)
    track_status = {}

    for index, data in track_st_data.iterrows(): 
        track_st = list(str(data['TrackStatus'])) 
        status_list = [track_st_cond.get(sta) for sta in track_st]
        track_status[int(data['LapNumber'])] = status_list
        
    track_status_df = pd.DataFrame(list(track_status.items()), columns=['LapNumber', 'Events'])
    track_status_df = pd.DataFrame(track_status_df.explode('Events'))

    events = []
    current_event = None
    event_laps = []

    for i, row in track_status_df.iterrows():
        lap = row['LapNumber']
        event = row['Events']
            
        if event != current_event:
            if current_event is not None:
                events.append((current_event, event_laps))
                
            current_event = event
            event_laps = [lap]
        else:
            event_laps.append(lap)

    if current_event is not None:
        events.append((current_event, event_laps))

    plot_data = []
    for event, lapsno in events:
        for lap in lapsno:
            plot_data.append({'Lap': lap, 'Event': event})

    plot_df = pd.DataFrame(plot_data)
    fig = px.scatter(plot_df, 
                    x='Lap', 
                    y='Event',
                    labels={'Lap': 'Lap Number', 'Event': 'Events'},
                    hover_name='Event',
                    color='Event'
                    )  

    fig.update_traces(marker=dict(size=15))
    fig.update_layout(
        yaxis=dict(tickmode='linear', title='Events'),
        xaxis_title='Lap Number',
        showlegend=False,
        height=400
    )

    st.plotly_chart(fig, use_container_width=True)
            
    st.divider()


def set_driver_selection(race_results):
    driver_info, driver_sel = st.columns([5, 3])

    with driver_sel:
        drivers = race_results['FullName'].unique()
        selected_driver = st.selectbox("Select Driver", drivers)
        st.session_state['selected_driver'] = selected_driver

    with driver_info:
        col1, col2,col3 = st.columns([1, 2,1])

        with col1:
            st.image(retrive_driver_img(selected_driver), use_column_width=True)
            
        with col2:
            st.header(selected_driver)
            position = int(race_results.loc[race_results['FullName'] == selected_driver, 'Position'].iloc[0])
            team_name = race_results.loc[race_results['FullName'] == selected_driver, 'TeamName'].iloc[0]

            race_finished = race_results.loc[race_results['FullName'] == selected_driver, 'Status'].iloc[0].strip()
            driver_info = {
                'Parameter' : ['Poition in race', 'Team'],
                'Value' : [position, team_name]
            }
            points = race_results.loc[race_results['FullName'] == selected_driver, 'Points'].iloc[0]
            if race_finished.lower() == 'finished':
                driver_info['Parameter'].append('Status')
                driver_info['Value'].append(race_finished)
                driver_info['Parameter'].append('Points')
                driver_info['Value'].append(points)

            elif race_finished.endswith('Laps') or race_finished.endswith('Lap'):
                driver_info['Parameter'].append('Status')
                driver_info['Value'].append(f"Finished ({race_finished})")
                driver_info['Parameter'].append('Points')
                driver_info['Value'].append(points)

            else:
                driver_info['Parameter'].append('Status')
                driver_info['Value'].append('Not Finished')
                driver_info['Parameter'].append('Reason')
                driver_info['Value'].append(race_finished)
            
            driver_info_df = pd.DataFrame(driver_info)
            driver_info_df.set_index('Parameter',inplace=True)

            st.dataframe(driver_info_df, use_container_width=True)

    st.divider()
    
def set_lap_wise_analysis(laps, race_results):
    driver_abb = race_results.loc[race_results['FullName'] == st.session_state['selected_driver'] , 'Abbreviation'].iloc[0]

    filtered_data = laps[laps['Driver'] == driver_abb]

    lap_time_pit_stop(filtered_data)
    tire_dist_sec_time(filtered_data)
    lap_position(filtered_data)

def lap_time_pit_stop(filtered_data):
    st.header("Lap wise Driver Analysis")

    col1, col2, col3 = st.columns([2, 5, 2])

    with col1:
        st.subheader("Lap Time per Lap")
        table_data = filtered_data[['LapNumber', 'LapTime']].copy()
        table_data['LapTime'] = table_data['LapTime'].apply(lambda x: convert_to_time_format(x.total_seconds()))
        table_data.set_index('LapNumber', inplace=True)

        st.dataframe(table_data, use_container_width=True)

    with col2:
        fig = px.line(filtered_data, x='LapNumber', y='LapTime')
        st.plotly_chart(fig)

    with col3:
        try:
            st.subheader("Lap Time Stats")

            fastest_lap_number = filtered_data.loc[filtered_data['LapTime'].dropna().idxmin(), 'LapNumber']
            lap_time_stats = {
                'Parameter': ['Fastest Time', 'Average Time'],
                'Time': [
                    convert_to_time_format(filtered_data['LapTime'].dropna().min().total_seconds()),
                    convert_to_time_format(filtered_data['LapTime'].dropna().mean().total_seconds())
                ],
                'Lap Number' : [int(fastest_lap_number), 'N/A']
            }
            lap_time_stats_df = pd.DataFrame(lap_time_stats)
            lap_time_stats_df.set_index("Parameter", inplace=True)

            st.dataframe(lap_time_stats_df, use_container_width=True)

            pit_data = filtered_data[filtered_data['PitInTime'].notna()].copy()
            pit_table_data = []
            st.subheader("Pit Stop Data")
            total_time = 0
            for index, row in pit_data.iterrows():
                lap_number = int(row['LapNumber'])
                pit_in_time = row['PitInTime']
                next_lap = filtered_data[filtered_data['LapNumber'] == (lap_number + 1)].iloc[0]
                pit_out_time = next_lap['PitOutTime'] if pd.notna(next_lap['PitOutTime']) else "Not Available"
                        
                pit_duration = (pit_out_time - pit_in_time).total_seconds()
                total_time += pit_duration
                duration_str = f"{convert_to_time_format(pit_duration)}"
                    
                pit_table_data.append([lap_number, duration_str])
                
            pit_data_df = pd.DataFrame(pit_table_data, columns=['Pit In Lap', 'Time Taken'])
            pit_data_df.set_index('Pit In Lap', inplace=True)
            st.dataframe(pit_data_df, use_container_width=True)
                
            st.write(f"**Total Pit Stop Time** - {convert_to_time_format(total_time)}")

        except Exception as e:
            st.write("Error while fetching Data")    
    st.divider()

def tire_dist_sec_time(filtered_data):
    col1, col2 = st.columns([3, 8])

    with col1:
        st.subheader("Tire Usage Distribution")
        compound_counts = filtered_data['Compound'].value_counts()

        fig = px.pie(compound_counts, values=compound_counts.values, names=compound_counts.index, hole=0.3)
        st.plotly_chart(fig)
        
        compound_data = []
        current_compound = None
        start_lap = None

        for _, row in filtered_data.iterrows():
            if row['Compound'] != current_compound:
                if current_compound is not None:
                    compound_data.append([current_compound, start_lap, row['LapNumber'] - 1])
                
                current_compound = row['Compound']
                start_lap = row['LapNumber']
        
        compound_data.append([current_compound, start_lap, filtered_data['LapNumber'].max()])

        compound_df = pd.DataFrame(compound_data, columns=['Compound Type', 'Start Lap', 'End Lap'])
        compound_df.set_index('Compound Type', inplace=True)

        st.dataframe(compound_df, use_container_width=True)
    
    with col2:
        st.subheader("Sector Time per Lap")
        col21, col22 = st.columns([5,3])
    
        with col22:
            table_data = filtered_data[['LapNumber', 'Sector1Time', 'Sector2Time', 'Sector3Time']].copy()
            time_col = ['Sector1Time', 'Sector2Time', 'Sector3Time']

            for col in time_col:
                table_data[col] = table_data[col].apply(lambda x: convert_to_time_format(x.total_seconds()))

            table_data.set_index('LapNumber', inplace=True)

            st.dataframe(table_data, use_container_width=True)
        with col21:
            fig = px.line(filtered_data, x='LapNumber', y=['Sector1Time', 'Sector2Time', 'Sector3Time'])
            st.plotly_chart(fig)

        sector_data = {
            'Sector': time_col,
            'Fastest Time': [convert_to_time_format(filtered_data[col].min().total_seconds()) for col in time_col],
            'Slowest Time': [convert_to_time_format(filtered_data[col].max().total_seconds()) for col in time_col],
            'Average Time': [convert_to_time_format(filtered_data[col].mean().total_seconds()) for col in time_col],
            'Total Time': [convert_to_time_format(filtered_data[col].sum().total_seconds()) for col in time_col]
        }

        sector_df = pd.DataFrame(sector_data)

        sector_df.set_index('Sector', inplace=True)

        st.dataframe(sector_df, use_container_width=True)
    st.divider()

def lap_position(filtered_data):
    st.subheader("Lap wise Position Analysis")
    pos_df_dis,pos_gr, pos_an = st.columns([2,6,2])
    pos_df = filtered_data[['LapNumber', 'Position','Deleted', 'DeletedReason']]
    with pos_df_dis:
        st.dataframe(pos_df[['LapNumber', 'Position']].set_index('LapNumber'), use_container_width=True)

    with pos_gr:
        fig = px.line(pos_df, x='LapNumber', y='Position')
        fig.update_yaxes(autorange='reversed')
        st.plotly_chart(fig)

    with pos_an:
        st.subheader("Position Analysis")
        
        start_position = int(pos_df['Position'].iloc[0])
        try:
            end_position = int(pos_df['Position'].iloc[-1])
        except ValueError:
            end_position = int(pos_df['Position'].iloc[-2])
        pos_gained = start_position - end_position

        analysis_data = {
            "Metric": ["Start Position", "End Position", "Position Change"],
            "Value": [start_position, end_position, pos_gained]
        }
        analysis_df = pd.DataFrame(analysis_data).set_index('Metric')

        st.dataframe(analysis_df,use_container_width=True) 

        st.subheader("Deleted Laps")

        deleted_laps = pos_df[pos_df['Deleted'] == True]

        if not deleted_laps.empty:
            deleted_laps.set_index('LapNumber', inplace=True)
            st.dataframe(deleted_laps[['DeletedReason']])
        else:
            st.write("No laps were deleted.")

    st.divider()  

def set_driver_speed(laps, race_results):
    driver_abb = race_results.loc[race_results['FullName'] == st.session_state['selected_driver'] , 'Abbreviation'].iloc[0]

    filtered_data = laps[laps['Driver'] == driver_abb]

    speed_metrics = {
        'Max Speed Sector 1': filtered_data['SpeedI1'].max(),
        'Avg Speed Sector 1': filtered_data['SpeedI1'].mean(),
        'Max Speed Sector 2': filtered_data['SpeedI2'].max(),
        'Avg Speed Sector 2': filtered_data['SpeedI2'].mean(),
        'Max Speed Finish Line': filtered_data['SpeedFL'].max(),
        'Avg Speed Finish Line': filtered_data['SpeedFL'].mean()
    }

    st.subheader("Speed Metrics")
    col1, col2 = st.columns([5,3])
    with col1:

        fig = px.bar(x=list(speed_metrics.keys()), y=list(speed_metrics.values()), title='Speed Metrics')
        st.plotly_chart(fig)

    with col2:
        table_data = filtered_data[['LapNumber', 'SpeedI1', 'SpeedI2', 'SpeedFL']].copy()
        table_data.rename(columns={
            'SpeedI1': 'SpeedI1 (km/h)',
            'SpeedI2': 'SpeedI2 (km/h)',
            'SpeedFL': 'SpeedFL (km/h)'
        }, inplace=True)
        table_data.set_index('LapNumber', inplace=True)
        st.dataframe(table_data, use_container_width=True)
    st.divider()


def set_driver_v_driver(laps, race_results):
    drivers_selection(race_results)
    race_result_comp(laps, race_results)
    lap_v_lap(laps)
    pos_v_lap_graphs(laps)
    speed_comp(laps)

def drivers_selection(race_results):
    st.header("Driver vs Driver Comparision")
    col1,col2 = st.columns(2)
    drivers = race_results['FullName'].unique()
    with col1:
        first_selected_driver = st.selectbox("Select 1st Driver", drivers)
        st.session_state['first_driver'] = first_selected_driver
    with col2:
        second_selected_driver = st.selectbox("Select 2nd Driver", drivers, index=1)
        st.session_state['second_driver'] = second_selected_driver
    
    st.divider()
    
def race_result_comp(laps, race_results):
    first_driver = st.session_state['first_driver']
    second_driver = st.session_state['second_driver']
    
    first_driver_abv = race_results.loc[race_results['FullName'] == first_driver, 'Abbreviation'].iloc[0]
    second_driver_abv = race_results.loc[race_results['FullName'] == second_driver, 'Abbreviation'].iloc[0]
    
    st.session_state['first_driver_abv'] = first_driver_abv
    st.session_state['second_driver_abv'] = second_driver_abv

    col1, col2, col3, col4 = st.columns([2,3,2,3])
    
    with col1:
        st.image(retrive_driver_img(first_driver), use_column_width=True)

    with col2:
        final_pos_dri_1 = int(race_results.loc[race_results['Abbreviation'] == first_driver_abv, 'Position'].iloc[0])
        fastest_dri_1 = convert_to_time_format(laps.loc[laps['Driver'] == first_driver_abv, 'LapTime'].min().total_seconds())
        avg_dri_1 = convert_to_time_format(laps.loc[laps['Driver'] == first_driver_abv, 'LapTime'].mean().total_seconds())

        st.subheader(f"{first_driver}")
        st.metric(label="Final Position", value=final_pos_dri_1)
        st.metric(label="Fastest Lap Time", value=fastest_dri_1)
        st.metric(label="Average Lap Time", value=avg_dri_1)
    
    with col3:
        st.image(retrive_driver_img(second_driver), use_column_width=True)

    with col4:
        final_pos_dri_2 = int(race_results.loc[race_results['Abbreviation'] == second_driver_abv, 'Position'].iloc[0])
        fastest_dri_2 = convert_to_time_format(laps.loc[laps['Driver'] == second_driver_abv, 'LapTime'].min().total_seconds())
        avg_dri_2 = convert_to_time_format(laps.loc[laps['Driver'] == second_driver_abv, 'LapTime'].mean().total_seconds())

        st.subheader(f"{second_driver}")
        st.metric(label="Final Position", value=final_pos_dri_2)
        st.metric(label="Fastest Lap Time", value=fastest_dri_2)
        st.metric(label="Average Lap Time", value=avg_dri_2)
    st.divider()

def lap_v_lap(laps):
    dri_1_abv = st.session_state['first_driver_abv']
    dri_2_abv = st.session_state['second_driver_abv']
    
    dri_1_laps = laps[laps['Driver'] == dri_1_abv].copy()
    dri_2_laps = laps[laps['Driver'] == dri_2_abv].copy()

    merged_laps = pd.merge(
        dri_1_laps[['LapNumber', 'LapTime']],
        dri_2_laps[['LapNumber', 'LapTime']],
        on='LapNumber',
        suffixes=(f'_{dri_1_abv}', f'_{dri_2_abv}'),
        how='outer' 
    )
    st.header("Lap v Lap Analysis")
    col1 , col2 = st.columns([2,5])
    with col1:
        lap_df = pd.DataFrame({
            'Lap Number': merged_laps['LapNumber'],
            st.session_state['first_driver']: merged_laps[f'LapTime_{dri_1_abv}'].apply(lambda x: convert_to_time_format(x.total_seconds()) if pd.notnull(x) else 'N/A'),
            st.session_state['second_driver']: merged_laps[f'LapTime_{dri_2_abv}'].apply(lambda x: convert_to_time_format(x.total_seconds()) if pd.notnull(x) else 'N/A'),
        })

        lap_df['Time Difference'] = (merged_laps[f'LapTime_{dri_1_abv}'] - merged_laps[f'LapTime_{dri_2_abv}']).dt.total_seconds()

        lap_df.set_index('Lap Number', inplace=True)
        st.dataframe(lap_df, use_container_width=True)
    with col2:
        fig = px.line(merged_laps, x='LapNumber', y=[f'LapTime_{dri_1_abv}',f'LapTime_{dri_2_abv}'])
        st.plotly_chart(fig)
    st.divider()

def pos_v_lap_graphs(laps):
    dri_1_abv = st.session_state['first_driver_abv']
    dri_2_abv = st.session_state['second_driver_abv']

    dri_1_laps = laps[laps['Driver'] == dri_1_abv].copy()
    dri_2_laps = laps[laps['Driver'] == dri_2_abv].copy()

    col1 , col2 = st.columns(2)
    with col1:
        st.header("Position v Lap Analysis")
        mergered_pos = pd.merge(
            dri_1_laps[['LapNumber', 'Position']],
            dri_2_laps[['LapNumber', 'Position']],
            on='LapNumber',
            suffixes=(f'_{dri_1_abv}', f'_{dri_2_abv}'),
            how='outer' 
        )
        fig = px.line(mergered_pos, x='LapNumber', y=[f'Position_{dri_1_abv}',f'Position_{dri_2_abv}'])
        fig.update_yaxes(autorange='reversed')
        st.plotly_chart(fig)

        st.write("")
        st.header("Position Analysis")

        start_position_dri_1 = int(dri_1_laps['Position'].iloc[0])
        start_position_dri_2 = int(dri_2_laps['Position'].iloc[0])

        try:
            end_position_dri_1 = int(dri_1_laps['Position'].iloc[-1])
            end_position_dri_2 = int(dri_2_laps['Position'].iloc[-1])
        except ValueError:
            end_position_dri_1 = int(dri_1_laps['Position'].iloc[-2])
            end_position_dri_2 = int(dri_2_laps['Position'].iloc[-2])

        pos_gained_dr_1 = start_position_dri_1 - end_position_dri_1
        pos_gained_dr_2 = start_position_dri_2 - end_position_dri_2

        avg_position_dri_1 = int(dri_1_laps['Position'].mean())
        avg_position_dri_2 = int(dri_2_laps['Position'].mean())

        analysis_data = {
            "Metric": ["Start Position", "End Position", "Position Change", "Average Position"],
            st.session_state['first_driver']: [start_position_dri_1, end_position_dri_1, pos_gained_dr_1, avg_position_dri_1],
            st.session_state['second_driver']: [start_position_dri_2, end_position_dri_2, pos_gained_dr_2, avg_position_dri_2]
        }

        analysis_df = pd.DataFrame(analysis_data).set_index('Metric').T
        st.dataframe(analysis_df, use_container_width=True)
    with col2:
        st.header("Sector Time per Lap")
        sector_choice = st.selectbox("Select Sector", options=[1, 2, 3], format_func=lambda x: f"Sector {x}")
        merged_sector_times = pd.merge(
            dri_1_laps[['LapNumber', f'Sector{sector_choice}Time']],
            dri_2_laps[['LapNumber', f'Sector{sector_choice}Time']],
            on='LapNumber',
            suffixes=(f'_{dri_1_abv}', f'_{dri_2_abv}'),
            how='outer'
        )

        fig = px.line(
            merged_sector_times,
            x='LapNumber',
            y=[f'Sector{sector_choice}Time_{dri_1_abv}', f'Sector{sector_choice}Time_{dri_2_abv}'],
            labels={'value': 'Sector Time', 'LapNumber': 'Lap Number'}
        )
        st.plotly_chart(fig)

        sector_data = {
            'Metric' : [f'Fastest Time {dri_1_abv}', f'Fastest Time {dri_2_abv}',f'Slowest Time {dri_1_abv}',f'Slowest Time {dri_2_abv}'],
            'Sector1Time' : [convert_to_time_format(dri_1_laps['Sector1Time'].min().total_seconds()), 
                             convert_to_time_format(dri_2_laps['Sector1Time'].min().total_seconds()),
                             convert_to_time_format(dri_1_laps['Sector1Time'].max().total_seconds()),
                             convert_to_time_format(dri_2_laps['Sector1Time'].max().total_seconds())],
            'Sector2Time' : [convert_to_time_format(dri_1_laps['Sector2Time'].min().total_seconds()),
                             convert_to_time_format(dri_2_laps['Sector2Time'].min().total_seconds()),
                             convert_to_time_format(dri_1_laps['Sector2Time'].max().total_seconds()),
                             convert_to_time_format(dri_2_laps['Sector2Time'].max().total_seconds())],
            'Sector3Time' : [convert_to_time_format(dri_1_laps['Sector3Time'].min().total_seconds()),
                             convert_to_time_format(dri_2_laps['Sector3Time'].min().total_seconds()),
                             convert_to_time_format(dri_1_laps['Sector3Time'].max().total_seconds()),
                             convert_to_time_format(dri_2_laps['Sector3Time'].max().total_seconds())]
        }

        sector_df = pd.DataFrame(sector_data).set_index('Metric').T

        st.dataframe(sector_df, use_container_width=True)
    st.divider()

def speed_comp(laps):
    st.header("Speed Analysis")
    driver1_data = laps[laps['Driver'] == st.session_state['first_driver_abv']]
    driver2_data = laps[laps['Driver'] == st.session_state['second_driver_abv']]
    
    speed_metrics = {
        'Max Speed Sector1': [driver1_data['SpeedI1'].max(), driver2_data['SpeedI1'].max()],
        'Avg Speed Sector 1': [int(driver1_data['SpeedI1'].mean()), int(driver2_data['SpeedI1'].mean())],
        'Max Speed Sector 2': [driver1_data['SpeedI2'].max(), driver2_data['SpeedI2'].max()],
        'Avg Speed Sector 2': [int(driver1_data['SpeedI2'].mean()), int(driver2_data['SpeedI2'].mean())],
        'Max Speed Finish Line': [driver1_data['SpeedFL'].max(), driver2_data['SpeedFL'].max()],
        'Avg Speed Finish Line': [int(driver1_data['SpeedFL'].mean()), int(driver2_data['SpeedFL'].mean())]
    }

    speed_df = pd.DataFrame(speed_metrics, index=[st.session_state['first_driver'], st.session_state['second_driver']]).T.reset_index()
    speed_df.columns = ['Metric', f'{st.session_state['first_driver_abv']} Speed (km/h)', f'{st.session_state['second_driver_abv']} Speed (km/h)']

    speed_df['Difference (km/h)'] = speed_df[f'{st.session_state["first_driver_abv"]} Speed (km/h)'] - speed_df[f'{st.session_state["second_driver_abv"]} Speed (km/h)']
    
    fig = px.bar(speed_df, x='Metric', y=[f'{st.session_state['first_driver_abv']} Speed (km/h)', f'{st.session_state['second_driver_abv']} Speed (km/h)'],
                 title="Speed Comparison",
                 labels={'value': 'Speed (km/h)', 'Metric': 'Metrics'},
                 barmode='group')

    col1, col2 = st.columns([5,3])
    
    with col1:
        st.plotly_chart(fig)
    
    with col2:
        st.subheader("Speed Metrics DataFrame")
        speed_df = speed_df.set_index('Metric')
        st.dataframe(speed_df, use_container_width=True)
    
    st.divider()

def race_summary(race_results, laps):
    st.header("Race Summary")
    st.divider()
    race_sum_res = race_results.copy()

    col1, col2 , col3, col4  = st.columns(4)

    with col3:
        st.subheader('Most Successful Team')

        team_points = race_sum_res.groupby('TeamName')['Points'].sum().reset_index()
        most_successful_team = team_points.loc[team_points['Points'].idxmax()]

        team_drivers = race_sum_res[race_sum_res['TeamName'] == most_successful_team['TeamName']]['FullName'].unique()
        
        st.image(retrive_driver_img(team_drivers[0]))
        st.subheader(f"**{most_successful_team['TeamName']}**")
        st.write(f"**Total Points: {most_successful_team['Points']}**")

    with col2:
        st.subheader('Most Places Gained')
    
        race_sum_res['pos_gained'] = race_sum_res['GridPosition'] - race_sum_res['Position']
        most_places_index =  race_sum_res['pos_gained'].idxmax()
        most_places_driver = race_sum_res.loc[most_places_index]
        
        st.image(retrive_driver_img(most_places_driver['FullName']))

        st.subheader(f"**{most_places_driver['FullName']}**")
        st.write(f"**Position Gained: {int(most_places_driver['pos_gained'])}**")

    with col1:
        st.subheader('Fastest Lap')

        fastest_lap_code = laps.loc[laps['LapTime'] == laps['LapTime'].min(), 'Driver'].iloc[0] 
        fastest_lap_driver = race_results.loc[race_results['Abbreviation'] == fastest_lap_code, 'FullName'].iloc[0]
        st.image(retrive_driver_img(fastest_lap_driver))
        fastest_lap_time = laps['LapTime'].min()
        fastest_lap_time_lap = laps.loc[laps['LapTime'] == fastest_lap_time, 'LapNumber'].iloc[0]
        fastest_formatted_time = convert_to_time_format(fastest_lap_time.total_seconds())

        st.subheader(f"**{fastest_lap_driver}**")
        st.write(f"**Lap Number: {int(fastest_lap_time_lap)}({fastest_formatted_time})**")

    with col4:
        st.subheader('Top Speed')

        speed_cols = laps[['SpeedI1','SpeedI2','SpeedFL','SpeedST']].copy()
        
        max_index = speed_cols.stack().idxmax()

        highest_speed_row = laps.loc[max_index[0]]
        highest_speed_driver = race_results.loc[race_results['Abbreviation'] == highest_speed_row['Driver'], 'FullName'].iloc[0]
        
        st.image(retrive_driver_img(highest_speed_driver))
        st.subheader(highest_speed_driver)
        highest_speed_value = highest_speed_row[max_index[1]]
        st.write(f"**Lap Number: {int(highest_speed_row['LapNumber'])} ({highest_speed_value} km/h)**")

    st.divider()

    cola , colb, colc = st.columns([10,4,10])
    with colb:
        st.subheader("Data Source: **FastF1**")
        st.write("Developed by: **Abhinav Tomar**")


def display_race_info():
    race = st.session_state['race_data']['race']
    session_info = st.session_state['race_data']['session_info']
    race_results = st.session_state['race_data']['race_results']
    race_weather = st.session_state['race_data']['weather_data']
    laps = st.session_state['race_data']['laps']

    time_columns = ['Time','LapTime', 'Sector1Time', 'Sector2Time', 
                    'Sector3Time', 'Sector1SessionTime', 
                    'Sector2SessionTime', 'Sector3SessionTime', 'PitOutTime', 'PitInTime']

    laps[time_columns] = laps[time_columns].apply(pd.to_timedelta, errors='coerce')
    
    circuit_info = st.session_state['race_data']['circuit_info']

    set_race_name_flag(session_info)
    set_race_info_results(session_info, race, race_results, race_weather, laps, circuit_info)
    set_race_events(laps)
    set_driver_selection(race_results)
    set_lap_wise_analysis(laps, race_results)
    set_driver_speed(laps, race_results)
    set_driver_v_driver(laps,race_results)
    race_summary(race_results, laps)
    

def main():

    set_page_config()

    if 'race_data' not in st.session_state:
        retrive_choice_race()

    if 'race_data' in st.session_state:
        display_race_info()



if __name__ == '__main__':
    main()

