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
    data = pd.read_csv(file)
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
    data['log_date'] = data['log_time'].apply(lambda x : x.split(' ')[0])
    data['log_time'] = pd.to_datetime(data['log_time'])
    data['log_date'] = pd.to_datetime(data['log_date'])
    
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

def displayKpiMetrics(TotalLogCount, TotalModule, TopModuleData, BottomModuleData, kpiNames) :
    st.header("KPI Metrics")
    kpivalueforMetrics = [TotalLogCount, TotalModule, TopModuleData, BottomModuleData]
        
    for i, (col, (kpi_name, kpi_value)) in enumerate(zip(st.columns(4), zip(kpiNames, kpivalueforMetrics))) :
        col.metric(label=kpi_name, value=kpi_value, delta=kpi_value)


@st.cache_data(ttl=24*60*60)
def calculateKpis(data) :
    TotalLogCount = len(data)
    TotalModule = len(data['context_name'].unique())
    TotalUser = len(data['DEVICE_ID'].unique())
    TopModuleData = data['context_name'].value_counts().reset_index().sort_values(by='count', ascending=False).iloc[:1].values.tolist()
    # BottomModuleData = data['Context Name'].value_counts().reset_index().sort_values(by='count', ascending=True).iloc[:1].values.tolist()
    
    return (TotalLogCount, TotalModule, TotalUser, TopModuleData)
    
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
    
    startDate = startDate.strftime('%Y-%m-%d')
    endDate = endDate.strftime('%Y-%m-%d')


    return (startDate, endDate, selectedContext, selectedMsgId)

def displayDonut(data) :
    fig = px.pie(data, names='context_name', values='count', hole=.3)
    fig.update_traces(textposition='inside', textinfo='percent + label + value')
    fig.update_layout(font=dict(size=14))
    fig.update(layout_showlegend=False)
    
    st.plotly_chart(fig, theme='streamlit', use_container_width=True)
    
@st.cache_data(ttl=24*60*60)    
def displayTrendChart(data) :
    pxData = data['log_date'].value_counts().reset_index()
    fig = px.area(pxData, x='log_date', y='count', title='Log Trend')
    fig.update_layout(margin=dict(l=20, r=20, t=50, b=20))
    fig.update_xaxes(rangemode='tozero', showgrid=False)
    fig.update_yaxes(rangemode='tozero', showgrid=True)
    st.plotly_chart(fig, theme='streamlit', use_container_width=True)
    
def displayTop10Module(data, ctxtName, msgID) :
    displayProgressBar()
    print(f'msgid : {msgID}')
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
            if (ctxtName != '') and (msgID != '') :
                query_expr = "(context_name == @ctxtName and message_id == @msgID)"
                showDataframe = data.query(query_expr)[['log_date', 'context_name', 'message_id', 'message_data']].reset_index(drop=True)
            
            if (ctxtName != '') and (msgID == '') :
                showDataframe = data.query("(context_name == @ctxtName)")[['log_date', 'context_name', 'message_id', 'message_data']].reset_index(drop=True)
            
            elif (ctxtName == '') and (msgID == '') :
                showDataframe = data[['log_date', 'context_name', 'message_id', 'message_data']].sort_values(by='log_date', ascending=True).reset_index(drop=True)
                
            st.dataframe(showDataframe, use_container_width=True)
                                    
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
        pxData = data[['log_date', 'message_id']].value_counts().reset_index().sort_values(by='log_date', ascending=True)
        fig = px.line(pxData, x='log_date', y='count', color='message_id', title=f'{module} Trend', markers=True)
        fig.update_layout(margin=dict(l=20, r=20, t=50, b=20))
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
    
    #UploadedFile = st.sidebar.file_uploader("Upload Log file (csv)")
    uploaded_files = st.sidebar.file_uploader("Choose a CSV file", accept_multiple_files=True, type=['csv'])
    if uploaded_files is not None :
        data_frames = []
        for file in uploaded_files :
            data = load_data(file)
            data_frames.append(data)
        
        if data_frames:
            data = pd.concat(data_frames, ignore_index=True)
            
            st.title("📊 Log Dashboard")
            startDate, endDate, selectedContext, selectedMsgId = displaySidebar(data)
                
            query_expr = "(context_name == @selectedContext)"
            filterData = data.query(query_expr)[['log_date', 'context_name', 'message_id', 'message_data']].reset_index(drop=True)
                
            datetimeRange = pd.date_range(startDate, endDate)
            query_expr = "log_date in @datetimeRange"
            filterData = filterData.query(query_expr)
                
            TotalLogCount, TotalModule, TotalUser, TopModuleData = calculateKpis(data)
            kpiNames = ["All Events", "All Moduels",'Total User', TopModuleData[0][0]]
            displayKpiMetrics(TotalLogCount, TotalModule, TotalUser, TopModuleData[0][1], kpiNames)
            displayTrendChart(data)
            st.divider()
            
            displayTop10Module(data, selectedContext, selectedMsgId)

            if selectedContext != '' :
                displayMoudleDataAnalysis(filterData, selectedMsgId)
            
if __name__ == '__main__' :
    main()