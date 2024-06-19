from datetime import datetime
from io import BytesIO

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
import altair as alt
import time, re, json, os
import moduleHandler

# page Configuration
def set_page_config() :
    st.set_page_config(
        page_title="Data Dashboard",
        page_icon="📊",
        layout='wide',
        initial_sidebar_state="expanded"
    )
    
alt.themes.enable("dark")

# Data load
@st.cache_data(ttl=24*60*60)
def load_data(file) :
    # data = pd.read_csv('./file/KIC_LOG_30.csv')
    file_bytes = BytesIO(file.getvalue())
    
    try :
        data = pd.read_csv(file_bytes, low_memory=False)
    except :
        st.warning('EmptyDataError (pandas.erros.EmptyDataError), check file.', 
                    icon="🚨")
        
        return pd.DataFrame()
        
        
    data = data.fillna('None')
    
    exception_fw_version = ['03.30.09', '03.30.15', '03.30.21', '03.30.22', '03.30.23', '03.30.24']
    
    col = ['message_key_1', 'message_value_1',
        'message_key_2', 'message_value_2', 
        'message_key_3', 'message_value_3',
        'message_key_4', 'message_value_4', 
        'message_key_5', 'message_value_5',
        'message_key_6', 'message_value_6', 
        'message_key_7', 'message_value_7',
        'message_key_8', 'message_value_8', 
        'message_key_9', 'message_value_9',
        'message_key_10', 'message_value_10']
    
        
    data['message_data'] = data[col].to_dict(orient='records')
    data['message_data'] = data['message_data'].apply(lambda x : getMessageData(x))
    
    data['log_time'] = pd.to_datetime(data['log_time'])
    data = data.rename(columns={'log_time':'log_date'})
    
    # data['log_date'] = data['log_time'].apply(lambda x : x.split(' ')[0])
    # data['log_time'] = pd.to_datetime(data['log_time'])
    # data['log_date'] = pd.to_datetime(data['log_date'])
    
    query_expr = "fw_version in @exception_fw_version"
    data = data.query(query_expr)

    return data

def getMessageData(x) :
    messageDatalist = []
    valuelst = list(x.values())
    keys, values = valuelst[::2], valuelst[1::2]
    for key,value in zip(keys, values) :
        if key != 'None' :
            messageDatalist.append((key, value))
    messageData = dict(messageDatalist)
    return messageData  

def displayKpiMetrics(TotalLogCount, TotalModule, TopUserData, TotalErrorCount, kpiNames) :
    st.header("KPI Metrics")
    kpivalueforMetrics = [TotalLogCount, TotalModule, TopUserData, TotalErrorCount]
        
    for i, (col, (kpi_name, kpi_value)) in enumerate(zip(st.columns(4), zip(kpiNames, kpivalueforMetrics))) :
        if kpi_name == 'Error Log' :
            if kpi_value == 0 :
                col.metric(label=kpi_name, value=kpi_value, delta=None)
            else :
                col.metric(label=kpi_name, value=kpi_value, delta=kpi_value, delta_color='inverse')
        else :
            col.metric(label=kpi_name, value=kpi_value, delta=kpi_value)


@st.cache_data(ttl=24*60*60)
def calculateKpis(data) :
    TotalLogCount = len(data)
    TotalModule = len(data['context_name'].unique())
    TotalUser = len(data['DEVICE_ID'].unique())
    
    # faultManager : errorLog
    try :
        faultModuleData = len(data[data['context_name'] == 'faultmanager'])
    except :
        faultModuleData = 0
        
    # TopModuleData = data['context_name'].value_counts().reset_index().sort_values(by='count', ascending=False).iloc[:1].values.tolist()
    # BottomModuleData = data['Context Name'].value_counts().reset_index().sort_values(by='count', ascending=True).iloc[:1].values.tolist()
    
    return (TotalLogCount, TotalModule, TotalUser, faultModuleData)
    
# sidebar
def displaySidebar(data) :
    st.sidebar.header("Filters")
    
    startDate = pd.Timestamp(st.sidebar.date_input("Start date", data['log_date'].min().date()))
    endDate = pd.Timestamp(st.sidebar.date_input("End date", data['log_date'].max().date()))
    
    ctxtlist = list(data['context_name'].unique())
    ctxtlist.insert(0, '')
    selectedContext = st.sidebar.selectbox('Select a Context Name', ctxtlist)
    
    msgIDlist = list(data[data['context_name']==selectedContext]['message_id'].unique())
    msgIDlist.insert(0, '') 
    selectedMsgId = st.sidebar.selectbox('Select a Message ID', msgIDlist)
    
    # startDate = startDate.strftime('%Y-%m-%d')
    # endDate = endDate.strftime('%Y-%m-%d')

    return (startDate, endDate, selectedContext, selectedMsgId)

def displayDonut(data) :
    fig = px.pie(data, names='context_name', values='count', hole=.3)
    fig.update_traces(textposition='inside', textinfo='percent + label + value')
    fig.update_layout(font=dict(size=14))
    fig.update(layout_showlegend=False)
    
    st.plotly_chart(fig, theme='streamlit', use_container_width=True)
    
    
    
# =============================================================================================== #
@st.cache_data(ttl=24*60*60)    
def displayTrendChart(data) :
    data['log_date_dt'] = data['log_date'].apply(lambda x : datetime.strftime(x, '%Y-%m-%d'))
    pxData = data['log_date_dt'].value_counts().reset_index()
    pxData = pxData.sort_values(by='log_date_dt', ascending=True)
    
    fig = px.area(pxData, x='log_date_dt', y='count', title='Log Trend')
    fig.update_layout(margin=dict(l=20, r=20, t=50, b=20), 
                        xaxis_title = 'Date',
                        yaxis_title = 'Count')
    fig.update_xaxes(rangemode='tozero', showgrid=False)
    fig.update_yaxes(rangemode='tozero', showgrid=True)
    st.plotly_chart(fig, theme='streamlit', use_container_width=True)

@st.cache_data(ttl=24*60*60)
def displayChoropleth(data):
    col1, col2 = st.columns((7.5,5))
    with col1 :
        import geopandas as gpd
        
        with open('country.json') as f:
            js = json.loads(f.read())
        
        cntryCode = pd.DataFrame(js, columns=['country2Code', 'country3Code'])
        
        world = gpd.read_file(gpd.datasets.get_path("naturalearth_lowres"))
        countryData = data['country'].value_counts().reset_index()

        world_cntryCode = world.merge(cntryCode, left_on='iso_a3', right_on='country3Code')
        world_cntryData = world_cntryCode.merge(countryData, left_on = 'country2Code', right_on='country')[['continent', 'name', 'country2Code', 'country3Code', 'count', 'geometry']]

        choropleth = px.choropleth(world_cntryData,
                                    locations='country3Code',
                                    color_continuous_scale=px.colors.sequential.Plasma,
                                    color='count',
                                    locationmode="ISO-3")
        
        
        choropleth.update_layout(
            title='Country Log count',
            template='plotly_dark',
            plot_bgcolor='rgba(0, 0, 0, 0)',
            paper_bgcolor='rgba(0, 0, 0, 0)',
            margin=dict(l=0, r=0, t=25, b=0),
            height=600,
            width=2000
        )
        
        st.plotly_chart(choropleth, use_container_width=True)
    
    with col2 :
        world_df = world_cntryData[['continent', 'name', 'country2Code', 'country3Code', 'count']].sort_values(by='count', ascending=False)
        st.dataframe(world_df,
                        column_order=('name', 'count'),
                        hide_index=True,
                        column_config={
                            "name" : 
                                st.column_config.TextColumn(
                                    "Country",
                                    width='medium'
                                    ),
                            "count" : st.column_config.ProgressColumn(
                                "Usability",
                                format="%f",
                                min_value=0,
                                max_value=max(world_df['count']),
                            )},
                        use_container_width=True)

# ================================================================================================== #
    

def displayTop10(data) :
    displayProgressBar()

    TopModuleUseData = data['context_name'].value_counts().reset_index().sort_values(by='count', ascending=False).iloc[:10,]
    
    col1, col2 = st.columns(2) 
    
    with col1 :
        container = st.container(border=True, height=450)
        with container :
            fig = px.pie(TopModuleUseData, names='context_name', values='count', title="Top 10 Log Module", hole=.3)
            # fig.update_traces(textposition='inside', textinfo='percent + label + value')
            fig.update_layout(font=dict(size=18))
            fig.update_layout(legend=dict(font=dict(size=18)))
            fig.update(layout_showlegend=True)
            st.plotly_chart(fig, theme='streamlit', use_container_width=True)
            
            
    with col2 :
        container = st.container(border=True, height=450)
        with container :         
            # show top 10 apps usablity
            ctxtName, messageId = 'SAM', 'NL_APP_LAUNCH_BEGIN'
            query_expr = "(context_name == @ctxtName and message_id == @messageId)"
            
            df = data.query(query_expr)[['log_date', 'context_name', 'message_id', 'message_data']].reset_index(drop=True)
            
            keylst = list(df['message_data'].iloc[0].keys())
            stdIdx = df.columns.get_loc('message_data')
            
            
            for loc in range(len(keylst)) :
                df.insert(stdIdx+loc+1,
                keylst[loc],
                df['message_data'].apply(lambda x : x.get(keylst[loc], 'None')))
    
            df = df.replace('', pd.NA).dropna()
            
            appUse_df = df['app_id'].value_counts().reset_index().sort_values(by='count', ascending=False).iloc[:10, :]
            
            appUse_fig = go.Figure(data=[go.Bar(
                x = appUse_df['count'].values.tolist(),
                y = appUse_df['app_id'].values.tolist(),
                marker_color = 'crimson',
                orientation='h'
            )])
            
            appUse_fig.update_layout(title='Top 10 : App Usability',
                            xaxis_title = "count",
                            yaxis_title = "App_id")
                            # height=700,
                            # uniformtext_minsize=8, uniformtext_mode='hide')
            
            st.plotly_chart(appUse_fig, theme='streamlit', use_container_width=True)
            
            # if (ctxtName != '') and (msgID != '') :
            #     query_expr = "(context_name == @ctxtName and message_id == @msgID)"
            #     showDataframe = data.query(query_expr)[['log_date', 'context_name', 'message_id', 'message_data']].reset_index(drop=True)
            
            # if (ctxtName != '') and (msgID == '') :
            #     showDataframe = data.query("(context_name == @ctxtName)")[['log_date', 'context_name', 'message_id', 'message_data']].reset_index(drop=True)
            
            # elif (ctxtName == '') and (msgID == '') :
            #     showDataframe = data[['log_date', 'context_name', 'message_id', 'message_data']].sort_values(by='log_date', ascending=True).reset_index(drop=True)
                
            # st.dataframe(figdf, use_container_width=True)
            
def displayHomeUsabilty(data) :
    pass
            
def displayRawData(data) :
    text_input = st.text_input(
                "Enter some string Text 👇",
                placeholder="Write string that you want to filter"
    )
    
    if text_input :       
        pass
    else :
        st.dataframe(data, use_container_width=True)
    
    
                                    
def displayProgressBar() :
    progress_text = "Operation in progress. Please wait."
    my_bar = st.progress(0, text=progress_text)
    for percent_complete in range(100):
        time.sleep(0.01)
        my_bar.progress(percent_complete + 1, text=progress_text)
            
    time.sleep(1)
    my_bar.empty() 

def displayMoudleDataAnalysis(data, msg) :
    try :
        module = data['context_name'].unique()[0]
    except :
        return

    msg = msg
    container = st.container(border=True)
    
    # regardless all msg..,
    with container : 
        data['log_date_dt'] = data['log_date'].apply(lambda x : datetime.strftime(x, '%Y-%m-%d'))
        pxData = data[['log_date_dt', 'message_id']].value_counts().reset_index().sort_values(by='log_date_dt', ascending=True)
        
        fig = px.line(pxData, x='log_date_dt', y='count', color='message_id', title=f'{module} Trend', markers=True)
        fig.update_layout(margin=dict(l=20, r=20, t=50, b=20),
                        xaxis_title = 'Date',
                        yaxis_title = 'Count')
        fig.update_xaxes(rangemode='tozero', showgrid=False)
        fig.update_yaxes(rangemode='tozero', showgrid=True)
        st.plotly_chart(fig, theme='streamlit', use_container_width=True)
    
    
    container = st.container(border=True)
    displayProgressBar()
    # regarding msg Handler
    if msg != '' :
        with container :
            analysisData(module, data, msg)
            
    else :
        with container :
            analysisData(module, data)

def analysisData(module, data, msg='') :
    contextName = module
    messageId = msg
    
    if contextName == 'ADMANAGER' :
        moduleHandler.admanagerHandler(data, messageId)
    if contextName == 'voice' :
        moduleHandler.voiceHandler(data, messageId)
    if contextName == 'SAM' :
        moduleHandler.samHandler(data, messageId)
    if contextName == 'com.webos.app.home' :
        moduleHandler.homeHandler(data, messageId)
    if contextName == 'com.webos.app.homeconnect' :
        moduleHandler.homeconnectHandler(data, messageId)
    if contextName == 'fancontroller' :
        moduleHandler.thermalHandler(data, messageId)
    if contextName == 'NUDGE' :
        moduleHandler.nudgeHandler(data, messageId)
    if contextName == 'AppInstallD' :
        moduleHandler.appInstallHandler(data, messageId)
        
def main() :
    set_page_config()
    st.title("📊 Log Dashboard")
    #UploadedFile = st.sidebar.file_uploader("Upload Log file (csv)")
        
    uploaded_files = st.sidebar.file_uploader("Choose a CSV file", accept_multiple_files=True, type=['csv'])
    
    if uploaded_files == [] :
        st.info('This Application is for analysis with Normal log. To use this app, please input normal log csv files!')
        
    elif uploaded_files is not None :
        data_frames = []

        with st.spinner('Wait for the data with analysis.....') :
            for file in uploaded_files :
                data = load_data(file)
        
                if data.empty :
                    return 

                data_frames.append(data)

        if data_frames:
            data = pd.concat(data_frames, ignore_index=True)
            
            startDate, endDate, selectedContext, selectedMsgId = displaySidebar(data)
                
            query_expr = "(context_name == @selectedContext)"
            filterData = data.query(query_expr)[['log_date', 'context_name', 'message_id', 'message_data']].reset_index(drop=True)
            
            filterData['log_date_dt'] = pd.to_datetime(filterData['log_date'].apply(lambda x : datetime.strftime(x, '%Y-%m-%d')))

            datetimeRange = pd.date_range(startDate, endDate)
        
            query_expr = "log_date_dt in @datetimeRange"
            filterData = filterData.query(query_expr)
            
                    
            # TotalLogCount, TotalModule, TotalUser, TopModuleData = calculateKpis(data)
            TotalLogCount, TotalModule, TotalUser, ErrorLogCount = calculateKpis(data)
            kpiNames = ["All Events", "All Moduels",'Total User', 'Error Log']
            # kpiNames = ["All Events", "All Moduels",'Total User', TopModuleData[0][0]]
            displayKpiMetrics(TotalLogCount, TotalModule, TotalUser, ErrorLogCount, kpiNames)
            displayTrendChart(data)
            st.divider()
            # Choropleth Map
            displayChoropleth(data)
            st.divider()

            displayTop10(data)
            displayHomeUsabilty(data)
            
            
            show_container = st.container(border=True)
            with show_container :
                isModified = st.checkbox("Show Raw-Data")
                if isModified : 
                    displayRawData(data)
                    

            if selectedContext != '' :
                displayMoudleDataAnalysis(filterData, selectedMsgId)

if __name__ == '__main__' :
    try :
        main()
    except Exception as err :
        st.warning(f"🚨 Error has happend while operating dashboard")
        st.warning(f"{err}")