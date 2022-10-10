import json
import os
import streamlit as st
import altair as alt
import pandas as pd
from datetime import datetime

@st.cache(ttl=3600)
def load_data(data_source):
    data = pd.read_json(data_source)
    data['date'] = pd.to_datetime(data['date']).dt.date
    data['no'] = data['no'].apply(lambda x: [int(i) for i in x])
    data['sno'] = pd.to_numeric(data['sno'])
    return data

@st.cache(ttl=3600, show_spinner=False)
def load_color_definations(data_source):
    with open(data_source, encoding='utf-8') as file:
        data = json.load(file)
        data_frame = pd.io.json.json_normalize(data)
    return data_frame

def remove_none_from_list(data):
    return list(filter(None, data))

ball_colors = load_color_definations(os.path.join(os.path.dirname(__file__), '../data/ball-colors.json'));

st.title('Mark Six Statistics')

st.markdown(
    'Mark Six (Chinese: 六合彩) is a lottery game organised by the Hong Kong Jockey Club. ' + \
    'The game is a 6-out-of-49 lottery-style game, with seven prize levels. ' + \
    'The winning numbers are selected automatically from a lottery machine that contains balls with numbers 1 to 49.'
)

# Load online so that we don't need to a re-deployment on data change
DATA_SOURCE = 'https://raw.githubusercontent.com/icelam/schedule-scrape-experiment/master/data/all.json'
mark_six_data = load_data(DATA_SOURCE)

dataset_last_updated = mark_six_data['date'].max().strftime('%Y/%m/%d');
number_of_records = len(mark_six_data.index);
st.caption(f'Dataset last updated on: {dataset_last_updated}, number of records: {number_of_records}')

tab1, tab2 = st.tabs(['Chart', 'Raw Data'])

with tab1:
    st.subheader('Occurance of Balls')

    chart_option_column_1, chart_option_column_2, chart_option_column_3 = st.columns(3)

    min_data_date = mark_six_data['date'].min()
    max_data_date = mark_six_data['date'].max()
    date_range_to_display = chart_option_column_1.date_input(
        'Date Range',
        value=(min_data_date, max_data_date),
        min_value=min_data_date,
        max_value=max_data_date
    )

    group_by = chart_option_column_2.selectbox(
        'Group By',
        ('None', 'Odd / Even', 'Ball colors')
    )

    include_special_number = chart_option_column_3.selectbox(
        'Include special number',
        ('Yes', 'No')
    )

    # Insert spacing between option group and chart
    st.write('')

    filtered_mark_six_data = mark_six_data.copy()
    filtered_mark_six_data = filtered_mark_six_data[
        (filtered_mark_six_data['date'] >= date_range_to_display[0])
        & (filtered_mark_six_data['date'] <= date_range_to_display[-1])
    ]

    balls_sumary = pd.DataFrame(list(range(1, 50)), columns=['ball'])

    balls_count = filtered_mark_six_data['no'].explode().value_counts().sort_index().to_frame()
    balls_count.insert(0, 'ball', balls_count.index)

    special_ball_count = filtered_mark_six_data['sno'].value_counts().sort_index().to_frame()
    special_ball_count.insert(0, 'ball', special_ball_count.index)

    balls_sumary = balls_sumary.merge(balls_count, on='ball', how='left')
    balls_sumary = balls_sumary.merge(special_ball_count, on='ball', how='left')

    balls_sumary = balls_sumary.rename(columns={ 'no': 'count', 'sno': 'special_count' })
    balls_sumary['special_count'].fillna(0, inplace=True)
    balls_sumary['count'].fillna(0, inplace=True)

    balls_sumary.insert(3, 'total_count', balls_sumary['count'] + balls_sumary['special_count'])
    balls_sumary.insert(4, 'color', balls_sumary['ball'].apply(lambda x: ball_colors[str(x)]))

    # A customized version of st.bar_chart(histogram_values)
    # List of ptions: https://altair-viz.github.io/user_guide/customization.html
    chart_data = (
        alt.Chart(balls_sumary)
            .transform_fold(remove_none_from_list([
                'count',
                'special_count' if include_special_number == 'Yes' else None
            ]))
            .mark_bar()
            .encode(
                x=alt.X('ball:O', title='Balls'),
                y=alt.Y('value:Q', title='Occurance'),
                color=alt.Color(
                    'color',
                    scale=alt.Scale(
                        domain=['red', 'blue', 'green'],
                        range=['lightcoral', 'royalblue', 'mediumseagreen']
                    ),
                    legend=None
                ),
                opacity=alt.Opacity(
                    'value:Q',
                    legend=None
                ),
                tooltip=remove_none_from_list([
                    alt.Tooltip('ball', title='Ball'),
                    alt.Tooltip('count', title='Occurance'),
                    alt.Tooltip('special_count', title='Occurance (Special)') if include_special_number == 'Yes' else None,
                    alt.Tooltip('total_count', title='Total Occurance') if include_special_number == 'Yes' else None
                ])
            )
            .configure_axis(grid=False)
            .configure_view(strokeWidth=0)
            .properties(height=500)
    )

    st.altair_chart(chart_data, use_container_width=True)

    if st.checkbox('Show data'):
        st.write(balls_sumary)

with tab2:
    st.write(mark_six_data)
