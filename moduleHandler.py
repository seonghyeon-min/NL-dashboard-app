from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from collections import Counter
from wordcloud import WordCloud
from konlpy.tag import Okt
from nltk.tag import pos_tag

import os, sys, json, re
import pandas as pd
import plotly.express as px
import streamlit as st
import altair as alt
import nltk
import plotly.graph_objects as go
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm

def admanagerHandler(data, msg) :
    if vaildCheck(msg) :
        return
    
    adData = set_keyData(data, msg)
    adData['result'] = adData['result'].apply(lambda x : str(x).lower())
    
    if msg == 'NL_ADMAN_REQ' :
        # show AD Requqest info.
        ret = adData[[ 'X-Device-Platform', 'result']].value_counts().reset_index()
        fig = px.bar(ret, x='result', y='count', color='X-Device-Platform',
                        barmode='group', title=f'{msg} count', text_auto=True)
        st.plotly_chart(fig, theme='streamlit', use_container_width=True)
    
    elif msg == 'NL_ADMAN_IMP' :
        dataforbar = adData[['ad_type','adslot_id']].value_counts().reset_index()
        dataforline = adData[['ad_type', 'log_date']].value_counts().reset_index().sort_values(by=['log_date','ad_type'], ascending=[True, True])
        print(dataforline)
        # bar = alt.Chart(dataforbar).mark_bar().encode(
        #     x=alt.X('ad_type', axis=alt.Axis(labelAngle=0)),
        #     y='count',
        #     color = 'adslot_id'
        # ).interactive()
        
        fig = px.bar(dataforbar, x="ad_type", y='count', barmode='group', color='adslot_id',text_auto=True)
    
        
        line = px.line(dataforline, x='log_date', y='count', color='ad_type')
        # line = alt.Chart(dataforline).mark_line().encode(
        #     x=alt.X('log_date:T'),
        #     y='count',
        #     color='ad_type'
        # ).interactive()
        
        tab1, tab2 = st.tabs(['Adtype', 'trend'])
        with tab1 :
            st.plotly_chart(fig, theme='streamlit', use_container_width=True)
        with tab2 :
            st.plotly_chart(line, theme='streamlit', use_container_width=True)
        
        
def voiceHandler(data, msg) :
    if vaildCheck(msg) :
        return
    
    voiceData = set_keyData(data, msg)
            
    # 발화: user_utterance, 발화 후 동작 앱: foreground_app, 최종 action: main_action
    if msg == 'NL_RESULT_DATA' :
                
        # show User voice main_action pattern info
        ret = voiceData[[ 'foreground_app', 'main_action']].value_counts().reset_index()
        fig = px.bar(ret, x='foreground_app', y='count', color='main_action',
                        barmode='group', title=f'Primary key in foreground_app count', text_auto=True)
        #fig.update_traces(marker_line_color='white', marker_line_width=1)
        #fig.update_layout(xaxis = dict(ticklen = 10, tickwidth =2, tickcolor = 'white'))
        st.plotly_chart(fig, theme='streamlit', use_container_width=True)
        
        # show User's utterance keyword pattern
        ret_c = voiceData['user_utterance']
        ret_count = ret_c.value_counts().reset_index()
                
        nltk.download('punkt')
        nltk.download('stopwords')
        okt = Okt()
                
        korean_stopwords = ['이', '있', '하', '것', '들', '그', '되', '수', '이', '보', '않', '없', '나', 
                                    '사람', '주', '아니', '등', '같', '우리', '때', '년', '가', '한', '지', '대하', 
                                    '오', '말', '일', '그렇', '위하', '때문', '그것', '두', '말하', '알', '그러나', 
                                    '받', '못하', '일', '그런', '또', '문제', '더', '사회', '많', '그리고', '좋', 
                                    '크', '따르', '중', '나오', '가지', '씨', '시키', '만들', '지금', '생각하', '그러', 
                                    '속', '하나', '집', '살', '모르', '적', '월', '데', '자신', '안', '어떤', '내', '내', 
                                    '경우', '명', '생각', '시간', '그녀', '다시', '이런', '앞', '보이', '번', '나', '다른', 
                                    '어떻', '여자', '개', '전', '들', '사실', '이렇', '점', '싶', '말', '정도', '좀', '원', '잘', '통하', '소리', '놓', '중인']
        stop_words = stopwords.words('english')
        if 'none' not in stop_words:
            stop_words.append('none')
                
        def preprocess_text(text):
            english_text = re.sub('[^a-zA-Z]', ' ', text)
            korean_text = re.sub('[^가-힣]', ' ', text)
                    
            english_tokens = word_tokenize(english_text.lower())
            filtered_english = [word for word in english_tokens if word not in stop_words]
                    
            korean_tokens = okt.nouns(korean_text)
            count_korean_tokens = [n for n in korean_tokens if len(n) > 1]
            filtered_korean = [word for word in count_korean_tokens if word not in korean_stopwords]

            return filtered_english + filtered_korean
                
                
        word_lists = ret_c.apply(preprocess_text)
        all_words = [word for words in word_lists for word in words]
        word_counts = Counter(all_words)
        filtered_word_counts = dict(word_counts.most_common(20))
        #filtered_word_counts = Counter({word: count for word, count in word_counts.items() if count > 1})
        
        new_ret_a = pd.DataFrame.from_records(list(filtered_word_counts.items()), columns=['user_utterance', 'count'])
        fig = px.bar(new_ret_a, x='user_utterance', y='count', color='user_utterance', title=f'User_utterance keyword', text_auto=True)
        st.plotly_chart(fig, theme='streamlit', use_container_width=True)
        
        col1, col2 = st.columns(2)
        
        with col1:
            container = st.container(border=True, height=600)
            with container:
                wordcloud_list = ' '.join(filtered_word_counts)
                wordcloud = WordCloud(font_path= 'C:/Windows/Fonts/HMFMPYUN.ttf', max_words=50, max_font_size=300, width=800, height=450).generate(wordcloud_list)
                #plt.title("User Utteranc Wordcloud")
                plt.imshow(wordcloud, interpolation='bilinear')
                plt.axis('off')
                st.pyplot(plt, use_container_width=True)          
        
        with col2:
            container = st.container(border=True, height=600)
            with container:
                count_words = pd.Series(all_words).value_counts().head(10)
                st.dataframe(count_words, use_container_width=True)             

    # launch_type: voice or search
    # show select content (Voice search results / Search)
    elif msg == 'NL_SELECT_ITEM' :
        ret = voiceData[[ 'launch_type', 'query']].value_counts().reset_index()
        fig = px.bar(ret, x='launch_type', y='count', color='query',
                        barmode='group', title=f'{msg} count', text_auto=True)
        st.plotly_chart(fig, theme='streamlit', use_container_width=True)
            
    # show usability of provided keywords on search
    elif msg == 'NL_SELECT_KEYWORD' :
        ret = voiceData[[ 'keyword']].value_counts().reset_index()
        fig = px.bar(ret, x='keyword', y='count', color='keyword',
                        barmode='group', title=f'{msg} count', text_auto=True)
        st.plotly_chart(fig, theme='streamlit', use_container_width=True)
                        
    else :
        pass       

def samHandler(data, msg) :
    if vaildCheck(msg) :
        return
    
    if msg == 'NL_APP_LAUNCH_BEGIN' :
        query_expr = "message_id == @msg"
        exception_caller_id = ['com.webos.bootManager','com.webos.service.preloadmanager']
                
        filterData = data.query(query_expr)[['message_data']].reset_index(drop=True)

        #dict to dataframe lauchedapplist
        launchedApplist = filterData.apply(lambda x:json.loads(json.dumps(x['message_data'])), axis=1)
        launchedApplist = pd.DataFrame(launchedApplist, columns=['message_data'])

        cols = launchedApplist['message_data'][0].keys()

        rows = launchedApplist['message_data'].apply(lambda x:list(x.values()))

        launchedApplist = pd.DataFrame(rows.values.tolist(),columns=cols)

        query_expr = "caller_id not in @exception_caller_id"
        launchedApplist = launchedApplist.query(query_expr)
        print(launchedApplist)

        TopAppUseData = launchedApplist['app_id'].value_counts().reset_index().sort_values(by='count', ascending=False).iloc[:10,]
        EtcAppUseData = launchedApplist['app_id'].value_counts().reset_index().sort_values(by='count', ascending=False).iloc[10:,]


        #append etc app
        TopAppUseData = pd.concat([TopAppUseData, pd.DataFrame({'app_id':'etc', 'count': EtcAppUseData['count'].sum()}, index=[0])], ignore_index=True)
        col1, col2 = st.columns(2)

        with col1 :
            container = st.container(border=True, height=450)
            with container :
                fig = px.pie(TopAppUseData, names='app_id', values='count', title="Top 10 launched App through SAM", hole=.3)
                fig.update_layout(font=dict(size=16))
                fig.update_layout(legend=dict(font=dict(size=16)))
                fig.update(layout_showlegend=True)
                st.plotly_chart(fig, theme='streamlit', use_container_width=True)
        with col2 :
            container = st.container(border=True, height=450)
            with container :
                #query_expr = "(message_id == @msgID)"
                #filter_data = filter_data.query(query_expr)[['log_date', 'context_name', 'message_id', 'message_data']].reset_index(drop=True)
                st.dataframe(launchedApplist, use_container_width=True)
                
def homeHandler(data, msg) :
    if vaildCheck(msg) :
        return
    
    homeData = set_keyData(data, msg)
    # 1. 사용성 분석 (NL_APP_LAUNCH)
    if msg == 'NL_APP_LAUNCH' :
        normalRet = homeData[['log_date','app_id']].value_counts().reset_index().sort_values(by='log_date', ascending=True).reset_index(drop=True)
        accumulativeRet = homeData['log_date'].value_counts().reset_index().sort_values(by='log_date').reset_index(drop=True)
        appCountRet = homeData['app_id'].value_counts().reset_index().sort_values(by='count', ascending=False).reset_index(drop=True)

        maxXaxis = accumulativeRet.nlargest(1, 'count')['log_date'].unique()[0]
        
        # trend_fig = px.scatter(accumulativeRet, x='log_date', y='count', trendline="ols")
        trend_fig = px.line(accumulativeRet, x='log_date', y='count', markers=True) 
        trend_fig.add_vline(x=maxXaxis, line_width=1.5, line_dash='dash', line_color='red')
        trend_fig.update_layout(title="App Trend",
                                xaxis_title = "date",
                                yaxis_title = "count",
                                height=500)
        

        AppsUnique = appCountRet['app_id'].unique()
        
        usabilty_fig = go.Figure()
        usabilty_fig.add_trace(go.Scatter(
            x = appCountRet['count'].unique(),
            y = AppsUnique,
            marker = dict(color="gold", size=12),
            mode = "markers"
        ))
        
        usabilty_fig.update_layout(title="App Usability", 
                            xaxis_title = "Usability",
                            yaxis_title = "app_id",
                            height=700)

        tab1, tab2 = st.tabs(['Trend', 'Usability'])
        with tab1 :
            st.plotly_chart(trend_fig, theme='streamlit', use_container_width=True)
        with tab2 :
            st.plotly_chart(usabilty_fig, theme='streamlit', use_container_width=True)
            
    
    #2. qCard 사용성 파악 (신규기능)
    elif msg == 'NL_QCARD_CLICKED' : # app_id 
        qcardUsabilityRet = homeData['app_id'].value_counts().reset_index().sort_values(by='count', ascending=False).reset_index(drop=True)
        AppsUnique = qcardUsabilityRet['app_id'].unique()
                
        qcard_fig = go.Figure()
        
        qcard_fig.add_trace(go.Scatter(
            x = qcardUsabilityRet['count'].unique(),
            y = AppsUnique,
            marker = dict(color='darkturquoise', size=12),
            mode = 'markers'
        ))
        
        qcard_fig.update_layout(title="qCard Usability", 
                    xaxis_title = "Usability",
                    yaxis_title = "qCard_id",
                    height=500)
        
        st.plotly_chart(qcard_fig, theme='streamlit', use_container_width=True)
        
    #3. HERO Banner (NL_HERO_SHOWN <-> NL_HERO_CLICEKD Connection)
    elif msg == 'NL_HERO_SHOWN' :
        heroClickedRet = set_keyData(data, 'NL_HERO_CLICKED')[['log_date', 'hero_type']].value_counts().reset_index().sort_values(by='log_date', ascending=True).reset_index(drop=True)
        adfromheroClickRet = heroClickedRet[heroClickedRet['hero_type'] == 'advertisement']
        heroUsabilityRet = homeData[['log_date','hero_type']].value_counts().reset_index().sort_values(by='log_date', ascending=True).reset_index(drop=True)
        
        adXaxis = heroUsabilityRet[heroUsabilityRet['hero_type'] == 'advertisement']['log_date']
        adYaxis = heroUsabilityRet[heroUsabilityRet['hero_type'] == 'advertisement']['count']
        defaultXaxis = heroUsabilityRet[heroUsabilityRet['hero_type'] == 'default banner']['log_date']
        defaultYaxis = heroUsabilityRet[heroUsabilityRet['hero_type'] == 'default banner']['count']
        adclickedDate = adfromheroClickRet['log_date'].unique()
        
        hero_fig = go.Figure()
        hero_fig.add_trace(go.Scatter(x=adXaxis, y=adYaxis,
                                        mode='lines+markers',
                                        name='advertisement'))
        
        hero_fig.add_trace(go.Scatter(x=defaultXaxis, y=defaultYaxis,
                                        mode='lines+markers',
                                        name='default banner'))
        
        hero_fig.add_trace(go.Scatter(x=adfromheroClickRet['log_date'], y=adfromheroClickRet['count'],
                                        mode='markers',
                                        name='clickedAd'))

        for adDate in adclickedDate :
            hero_fig.add_vline(x=adDate, line_width=1.5, line_dash='dash', line_color='red')
            
        hero_fig.update_layout(title="advertisement & default banner in Hero Banner", 
                    xaxis_title = "date",
                    yaxis_title = "count",
                    height=500)
        
        st.plotly_chart(hero_fig, theme='streamlit', use_container_width=True)

def homeconnectHandler(data, msg) :
    if msg == '' :
        deviceUsabilityList = ['NL_HC_EVENT_BAP', 'NL_HC_EVENT_SCREEN', 'NL_HC_EVENT_PHOTO',  'NL_HC_EVENT_MUSIC', 'NL_HC_EVENT_AIRPLAY', 'NL_HC_EVENT_USB']
        renamingNormalLog = ['Bluetooth', 'ScreenShare', 'Photo', 'music', 'Airplay', 'USB']

        hcData = set_all_keyValue(data, deviceUsabilityList)
        
        hcData = hcData.replace(to_replace=dict(zip(deviceUsabilityList, renamingNormalLog)))
        homeconnectUsability = hcData['message_id'].value_counts().reset_index()
        
        hc_fig = px.bar(data_frame=homeconnectUsability, x='count', y='message_id', orientation='h', text_auto=True)
        
        hc_fig.update_traces(textfont_size=15, textfont_color='red')
        hc_fig.update_layout(title="HomeConnect Usability", 
                    xaxis_title = "count",
                    yaxis_title = "service",
                    height=500)
        
        st.plotly_chart(hc_fig, theme='streamlit', use_container_width=True)
    
    if msg == 'NL_HC_SWITCH_SOURCE' :
        # 주사용 외부입력 정보 및 속성을 수집함. {이전기기명, 전환된 기기명}
        switchSourceData = set_keyData(data, msg)
        inputswitchSourceRet = switchSourceData['input_source'].value_counts().reset_index().sort_values(by='count')
        
        InputSourceXaxis = []
        
        for source in inputswitchSourceRet['input_source'].values.tolist() :
            before, after = source.split(',')
            InputSourceXaxis.append(before + '->' + after)
            
        
        inputsource_fig = go.Figure(data=[go.Bar(
            x = InputSourceXaxis,
            y = inputswitchSourceRet['count'].values.tolist(),
            text = inputswitchSourceRet['count'].values.tolist(),
            textposition='outside',
            marker_color = 'crimson',
            name = 'InputSource'
        )])
        
        inputsource_fig.update_layout(title='Input Source Usability',
                                    xaxis_title = "inputSource",
                                    yaxis_title = "count",
                                    height=700,
                                    uniformtext_minsize=8, uniformtext_mode='hide')
        

        st.plotly_chart(inputsource_fig, theme='streamlit', use_container_width=True)
            
    
def thermalHandler(data, msg) : ## test ##
    if vaildCheck(msg) :
        return
    
    if msg == 'NL_CHIP_THERMAL' :
        keyLst = ['soc_temperature', 'core_iddq', 'cpu_iddq']
        for key in keyLst :
            thermalData = data
            thermalData[key] = data['message_data'].apply(lambda x : x.get(key, "None"))

    # split
        thermalTempeatureData = thermalData[['log_date', 'context_name', 'message_id', 'message_data', 'soc_temperature']].sort_values(by='log_date', ascending=True)
        thermalTempeatureData = thermalTempeatureData.drop(thermalTempeatureData[thermalTempeatureData['soc_temperature'] == 'None'].index)

        coreIddqData = thermalData[['log_date', 'context_name', 'message_id', 'message_data', 'core_iddq']].sort_values(by='log_date', ascending=True)
        coreIddqData = coreIddqData.drop(coreIddqData[coreIddqData['core_iddq'] == 'None'].index)
        
        cpuIddqData = thermalData[['log_date', 'context_name', 'message_id', 'message_data', 'cpu_iddq']].sort_values(by='log_date', ascending=True)
        cpuIddqData = cpuIddqData.drop(cpuIddqData[cpuIddqData['cpu_iddq'] == 'None'].index)

        fancorr_fig = px.density_heatmap(x=thermalTempeatureData['soc_temperature'], y=coreIddqData['core_iddq'], marginal_x='histogram', marginal_y='histogram')
        fancorr_fig.update_layout(title="temperature with core", 
                xaxis_title = "Tempeature",
                yaxis_title = "core",
                height=500)
        
        fancorr2_fig = px.density_heatmap(x=thermalTempeatureData['soc_temperature'], y=cpuIddqData['cpu_iddq'], marginal_x='histogram', marginal_y='histogram')
        fancorr2_fig.update_layout(title="temperature with cpu", 
                xaxis_title = "Tempeature",
                yaxis_title = "cpu",
                height=500)
        
        fancorr3_fig = px.density_heatmap(x=coreIddqData['core_iddq'], y=cpuIddqData['cpu_iddq'], marginal_x='histogram', marginal_y='histogram')
        fancorr3_fig.update_layout(title="core with cpu", 
                xaxis_title = "core",
                yaxis_title = "cpu",
                height=500)
        
        tab1, tab2, tab3 = st.tabs(['var1', 'var2', 'var3'])
        with tab1 :
            st.plotly_chart(fancorr_fig, theme='streamlit', use_container_width=True)
        with tab2 :
            st.plotly_chart(fancorr2_fig, theme='streamlit', use_container_width=True)
        with tab3 :
            st.plotly_chart(fancorr3_fig, theme='streamlit', use_container_width=True)
        
def nudgeHandler(data, msg) :
    if vaildCheck(msg) :
        return
    
    if msg == 'NL_NUDGE_RESULT_INFO' :
        nudgeResultInfoData = set_keyData(data, msg)
        nudgeIdUsability = nudgeResultInfoData['nudge_id'].value_counts().reset_index().sort_values(by='count')
        
        nudge_fig = px.bar(nudgeIdUsability, y='nudge_id', x='count', text_auto=True, orientation='h')
        nudge_fig.update_layout(title="nudgeId Usability", 
                xaxis_title = "count",
                yaxis_title = "nudge_id",
                height=500)
        
        st.plotly_chart(nudge_fig, theme='streamlit', use_container_width=True)

def appInstallHandler(data, msg) :
    if vaildCheck(msg) :
        return
    
    if msg == 'NL_APP_INSTALLED' : # app 별 인기도 분석
        appInstalledData = set_keyData(data, msg)
        appInstallPopularity = appInstalledData['app_id'].value_counts().reset_index().sort_values(by='count')
        appInstalledLst = appInstalledData['app_id'].unique()
        
        appDeletedData = set_keyData(data, 'NL_APP_REMOVED')
        try :
            appDeletedUsability = appDeletedData['app_id'].value_counts().reset_index().sort_values(by='count')
            appDeletedLst = appDeletedData['app_id'].unique()
        except :
            appDeletedLst = []
        
        if len(appDeletedLst) > 0 :
            commonAppLst = [app for app in appDeletedLst if app in appInstalledLst]
            commonAppdiscount = appDeletedUsability.query("app_id in @commonAppLst")['count'].values.tolist()
            commonAppdiscount = [(-value) for value in commonAppdiscount]
        
        #installed
        appPop_fig = go.Figure(data=[go.Bar(
            x=appInstallPopularity['app_id'].values.tolist(),
            y=appInstallPopularity['count'].values.tolist(),
            text =appInstallPopularity['count'].values.tolist(),
            textposition='outside',
            marker_color = 'crimson',
            name='installed'
        )])
        
        #Removed
        if len(appDeletedLst) > 0 :
            appPop_fig.add_trace(go.Bar(
                x=commonAppLst, 
                y=commonAppdiscount, 
                text=commonAppdiscount, 
                textposition='outside',
                marker_color='cadetblue',
                name='removed'))

        appPop_fig.update_layout(title='App Popularity',
                                    xaxis_title = "app_id",
                                    yaxis_title = "count",
                                    height=700,
                                    uniformtext_minsize=8, uniformtext_mode='hide',
                                    xaxis_tickangle=90)
        
        
        appPop_fig.update_traces(textposition='outside')

        st.plotly_chart(appPop_fig, theme='streamlit', use_container_width=True)
    
def vaildCheck(msg) :
    if msg == '' :
        return True 

def set_all_keyValue(data, services) :
    totalUsablityData = pd.DataFrame()
    for msg in services :
        moduledata = set_keyData(data, msg)
        if moduledata is not None :
            totalUsablityData = pd.concat([totalUsablityData, moduledata])

    return totalUsablityData

def set_keyData(data, msg) :
    moduleData = data[data['message_id'] == msg]
    # moduleData['message_data'] = moduleData['message_data'].apply(lambda x : preprocessing_data(x))
    try :
        keylst = list(moduleData['message_data'].iloc[0].keys())
    except :
        return
    
    stdIdx = moduleData.columns.get_loc('message_data')
    
    for loc in range(len(keylst)) :
        moduleData.insert(stdIdx+loc+1,
                        keylst[loc],
                        moduleData['message_data'].apply(lambda x : x.get(keylst[loc], 'None')))
    
    moduleData = moduleData.replace('', pd.NA).dropna()
    
    return moduleData

def preprocessing_data(data) :
    # first, remove blank
    try :
        data = data.strip('')
    except :
        pass
    
    matchData = re.findall(r'\{(.*?)\}', data)
    
    str_to_json = '{' + matchData[-1] + '}'
    
    try :
        ret = json.loads(str_to_json)
    except : # unvaild dict type
        m_json = str_to_json + '}'
        ret = json.loads(m_json)
    
    return ret