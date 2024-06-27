from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from collections import Counter
from wordcloud import WordCloud
from konlpy.tag import Okt
from nltk.tag import pos_tag

import os, sys, json, re
import pandas as pd
import plotly.express as px
import plotly.figure_factory as ff
import streamlit as st
import altair as alt
import nltk
import plotly.graph_objects as go
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import geopandas as gpd
import numpy as np

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
        dataforline = adData[['ad_type', 'log_date_dt']].value_counts().reset_index().sort_values(by=['log_date_dt','ad_type'], ascending=[True, True])
        print(dataforline)
        # bar = alt.Chart(dataforbar).mark_bar().encode(
        #     x=alt.X('ad_type', axis=alt.Axis(labelAngle=0)),
        #     y='count',
        #     color = 'adslot_id'
        # ).interactive()
        
        fig = px.bar(dataforbar, x="ad_type", y='count', barmode='group', color='adslot_id',text_auto=True)
    
        
        line = px.bar(dataforline, x='log_date_dt', y='count', color='ad_type')
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

# 퀵 설정 메뉴 선택 사용 관련 (사용자가 어떤 퀵 설정 메뉴를 사용하는지 파악하는데 용이)
# Quicksettings_menu_button은 제외
# count 1은 제외, game = gameoptimizer
# 국가 별로 quicksettings_item을 설정해서 기존 quicksettings_item count는 삭제 진행
def quicksettingsHandler(data, msg) :
    if vaildCheck(msg) :
        return

    cntryCode = readCountryJson()
    quickData = set_keyData(data, msg)
    world = gpd.read_file(gpd.datasets.get_path("naturalearth_lowres"))
    world_cntryCode = world.merge(cntryCode, left_on='iso_a3', right_on='country3Code')    
    quickData = quickData.merge(world_cntryCode, left_on='country', right_on='country2Code')
    
    
    if msg == 'NL_QUICKSETTINGS_VALUE' :
        accumulativeRet = quickData[['log_date_dt', 'name']].value_counts().reset_index().sort_values(by='log_date_dt').reset_index(drop=True)
        appCountRet = quickData[['quicksettings_item','name']].value_counts().reset_index().sort_values(by='count', ascending=False).reset_index(drop=True)

        maxXaxis = accumulativeRet.nlargest(1, 'count')['log_date_dt'].unique()[0]
        
        trend_fig = px.bar(accumulativeRet, x='log_date_dt', y='count', color='name') 
        trend_fig.update_layout(title="Quicksettings_item Usage Trend (Country)",
                                xaxis_title = "date",
                                yaxis_title = "count",
                                height=500)
        
        st.plotly_chart(trend_fig, theme='streamlit', use_container_width=True)
        
        UseCountryUnique = list(appCountRet['name'].unique())

        tabSeries = st.tabs(UseCountryUnique)
        for idx in range(len(tabSeries)) :
            appUsage = appCountRet[appCountRet['name'] == UseCountryUnique[idx]]
            appUnique = appUsage['quicksettings_item'].unique()
            
            usabilty_fig = go.Figure()
            usabilty_fig.add_trace(go.Scatter(
                x = appUsage['count'].unique(),
                y = appUnique,
                marker = dict(color='gold', size=12),
                mode = 'markers'
            ))
            
            usabilty_fig.update_layout(title=f"Quicksettings_item Usage Country : {UseCountryUnique[idx]}", 
                            xaxis_title = "Usability",
                            yaxis_title = "quicksettings_item",
                            height=700)
            
            with tabSeries[idx] :
                st.plotly_chart(usabilty_fig, theme='streamlit', use_container_width=True)
        
        
def voiceHandler(data, msg) :
    if vaildCheck(msg) :
        return
    
    #keyword 정리 함수
    def preprocess_text(text):
        english_text = re.sub('[^a-zA-Z]', ' ', text)
        korean_text = re.sub('[^가-힣]', ' ', text)
                    
        english_tokens = word_tokenize(english_text.lower())
        filtered_english = [word for word in english_tokens if word not in stop_words]
        #print(english_tokens)
        #print(filtered_english)
        
        korean_tokens = okt.nouns(korean_text)
        count_korean_tokens = [n for n in korean_tokens if len(n) > 1]
        filtered_korean = [word for word in count_korean_tokens if word not in korean_stopwords]
            
        if filtered_korean:
            filtered_korean = [filtered_korean[0]]
            
        return filtered_english + filtered_korean
    
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
    
    voiceData = set_keyData(data, msg)
    world_cntryCode = readCountryJson()
    voiceData = voiceData.merge(world_cntryCode, left_on='country', right_on='country2Code')
    
    
    # ============================================================================================ #
    # 발화: user_utterance, 발화 후 동작 앱: foreground_app, 발화 후 동작 앱에서 액션: main_action
    # voice 검색 결과의 action_type, service_type 분석
    # User_utterance keyword Top 10: 사용자가 발화한 키워드 Top 10 (한글자는 예외처리함)
    # Action App after User_utterance: 발화 후 동작 앱 및 행동(main action)
    if msg == 'NL_RESULT_DATA' :
        accumulativeRet = voiceData[['log_date_dt', 'name']].value_counts().reset_index().sort_values(by='log_date_dt').reset_index(drop=True)
        appCountRet = voiceData[['foreground_app','name']].value_counts().reset_index().sort_values(by='count', ascending=False).reset_index(drop=True)
        
        trend_fig = px.bar(accumulativeRet, x='log_date_dt', y='count', color='name') 

        trend_fig.update_layout(title="After User_utterance foreground_app (Country)",
                                xaxis_title = "date",
                                yaxis_title = "count",
                                height=500)

        st.plotly_chart(trend_fig, theme='streamlit', use_container_width=True)
        
        # show User's utterance keyword pattern
        ret_c = voiceData['user_utterance']
        ret_count = ret_c.value_counts().reset_index(name= 'count')
        
        # Setting Keyword   
        word_lists = ret_c.apply(preprocess_text)
        all_words = [word for words in word_lists for word in words]
        word_counts = Counter(all_words)
        filtered_keyword_counts = dict(word_counts.most_common(10))
        #filtered_word_counts = dict(word_counts.most_common(20))
        
        new_ret_a = pd.DataFrame.from_records(list(filtered_keyword_counts.items()), columns=['user_utterance', 'count'])
        UseCountryUnique = list(appCountRet['name'].unique())
        
        tabSeries = st.tabs(UseCountryUnique)
        for idx in range(len(tabSeries)):
            country = UseCountryUnique[idx]
            
            country_data = appCountRet[appCountRet['name'] == country]
            appUsage = country_data[country_data['name'] == country]
            appUnique = appUsage['foreground_app'].unique()
            
            country_keyword_counts = voiceData[voiceData['name'] == country]['user_utterance'].value_counts().reset_index(name='count').head(10)
            country_keyword_counts.rename(columns={'index': 'user_utterance'}, inplace=True)
            fig = px.bar(country_keyword_counts, x='user_utterance', y='count', color='user_utterance', title=f'Voice/Search Keyword Top 10: {country}',
                        text_auto=True, labels={'user_utterance': 'Content Keyword'})
            
            usabilty_fig = go.Figure()
            usabilty_fig.add_trace(go.Scatter(
                x=appUsage['count'].unique(),
                y=appUnique,
                marker=dict(color='gold', size=12),
                mode='markers'
            ))
            
            usabilty_fig.update_layout(title=f"Voice/Search Usage Country: {country}",
                                    xaxis_title="Usability",
                                    yaxis_title="Keyword_Tile",
                                    height=700)
            
            with tabSeries[idx]:
                st.plotly_chart(usabilty_fig, theme='streamlit', use_container_width=True)  
                st.plotly_chart(fig, theme='streamlit', use_container_width=True)

    # launch_type: voice or search
    # show select content (Voice search results / Search)
    # 추천 리스트/음성인식/통합검색 결과 컨텐츠 진입율 파악
    elif msg == 'NL_SELECT_ITEM':
        accumulativeRet = voiceData[['log_date_dt', 'name']].value_counts().reset_index(name='count').sort_values(by='log_date_dt').reset_index(drop=True)
        appCountRet = voiceData[['app_id', 'name']].value_counts().reset_index(name='count').sort_values(by='count', ascending=False).reset_index(drop=True)
        
        trend_fig = px.bar(accumulativeRet, x='log_date_dt', y='count', color='name')
        trend_fig.update_layout(title="Voice/Search Result Logs Trend (Country)",
                                xaxis_title="date",
                                yaxis_title="count",
                                height=500)
        st.plotly_chart(trend_fig, theme='streamlit', use_container_width=True)

        movie_data = voiceData[voiceData['query'] == 'movie']
        voiceData.loc[voiceData['query'] == 'movie', 'query'] = movie_data['content_title']
        
        ret_c = voiceData['query']
        ret_count = ret_c.value_counts().reset_index(name='count')
        word_lists = ret_c.apply(preprocess_text)
        all_words = [word for words in word_lists for word in words]
        word_counts = Counter(all_words)
        filtered_keyword_counts = dict(word_counts.most_common(10))
        
        new_ret_a = pd.DataFrame.from_records(list(filtered_keyword_counts.items()), columns=['query', 'count'])
        
        UseCountryUnique = list(appCountRet['name'].unique())
        
        tabSeries = st.tabs(UseCountryUnique)
        for idx in range(len(tabSeries)):
            country = UseCountryUnique[idx]
            
            country_data = appCountRet[appCountRet['name'] == country]
            appUsage = country_data[country_data['name'] == country]
            appUnique = appUsage['app_id'].unique()
            
            country_keyword_counts = voiceData[voiceData['name'] == country]['query'].value_counts().reset_index(name='count').head(10)
            country_keyword_counts.rename(columns={'index': 'query'}, inplace=True)
            fig = px.bar(country_keyword_counts, x='query', y='count', color='query', title=f'Voice/Search Keyword Top 10: {country}',
                        text_auto=True, labels={'query': 'Content Keyword'})
            
            usabilty_fig = go.Figure()
            usabilty_fig.add_trace(go.Scatter(
                x=appUsage['count'].unique(),
                y=appUnique,
                marker=dict(color='gold', size=12),
                mode='markers'
            ))
            
            usabilty_fig.update_layout(title=f"Voice/Search Usage Country: {country}",
                                    xaxis_title="Usability",
                                    yaxis_title="Keyword_Tile",
                                    height=700)
            
            with tabSeries[idx]:
                st.plotly_chart(usabilty_fig, theme='streamlit', use_container_width=True)
                st.plotly_chart(fig, theme='streamlit', use_container_width=True)

            
    # show usability of provided keywords on search
    # 키워드 타일(통합검색) 사용성 파악
    elif msg == 'NL_SELECT_KEYWORD':
        accumulativeRet = voiceData[['log_date_dt', 'name']].value_counts().reset_index().sort_values(by='log_date_dt').reset_index(drop=True)
        appCountRet = voiceData[['keyword', 'name']].value_counts().reset_index().sort_values(by='count', ascending=False).reset_index(drop=True)
        
        # Keyword_Tile(Search) Trend (country)
        trend_fig = px.bar(accumulativeRet, x='log_date_dt', y='count', color='name')
        trend_fig.update_layout(title="Keyword_Tile(Search) Trend (Country)",
                                xaxis_title="date",
                                yaxis_title="count",
                                height=500)
        st.plotly_chart(trend_fig, theme='streamlit', use_container_width=True)

        # Keyword_Tile(Search) Usage Time (Country)
        # data['log_time_only'] = pd.to_datetime(data['log_date_dt']).dt.time
        # bins = [0, 4, 8, 12, 16, 20, 24]
        # labels = ['Late Night(0~4)', 'Early Morning(4~8)', 'Morning(8~12)', 'Afternoon(12~16)', 'Evening(16~20)', 'Night(20~24)']
        # data['time_category'] = pd.cut(data['log_time_only'].apply(lambda x: x.hour), bins=bins, labels=labels, right=False)
        # time_counts = data.groupby(['time_category', 'country']).size().reset_index(name='count')
        # fig = px.bar(time_counts, x='time_category', y='count', color='country', barmode='group', title='Keyword_Tile(Search) Usage Time(Country)', text_auto=True)
        # st.plotly_chart(fig, theme='streamlit', use_container_width=True)
        # print(time_counts)
        
        # Keyword_Tile Usage Country
        UseCountryUnique = list(appCountRet['name'].unique())

        tabSeries = st.tabs(UseCountryUnique)
        for idx in range(len(tabSeries)) :
            appUsage = appCountRet[appCountRet['name'] == UseCountryUnique[idx]]
            appUnique = appUsage['keyword'].unique()
            
            usabilty_fig = go.Figure()
            usabilty_fig.add_trace(go.Scatter(
                x = appUsage['count'].unique(),
                y = appUnique,
                marker = dict(color='gold', size=12),
                mode = 'markers'
            ))
            
            usabilty_fig.update_layout(title=f"Keyword_Tile Usage Country : {UseCountryUnique[idx]}", 
                            xaxis_title = "Usability",
                            yaxis_title = "Keyword_Tile",
                            height=700)
            
            with tabSeries[idx] :
                st.plotly_chart(usabilty_fig, theme='streamlit', use_container_width=True)
    
    # mrcu_key:매직리모컨, voice_far:원거리 음성, mobile: ThinQ앱, voiceGuide:음성 도움말
    # 음성인식 사용상황 파악
    elif msg == 'NL_ACTIVATE_VOICE' :
        accumulativeRet = voiceData[['log_date_dt', 'name']].value_counts().reset_index().sort_values(by='log_date_dt').reset_index(drop=True)
        appCountRet = voiceData[['foreground_app','name']].value_counts().reset_index().sort_values(by='count', ascending=False).reset_index(drop=True)

        maxXaxis = accumulativeRet.nlargest(1, 'count')['log_date_dt'].unique()[0]
        
        trend_fig = px.bar(accumulativeRet, x='log_date_dt', y='count', color='name') 

        trend_fig.update_layout(title="Voice Usage Trend (Country)",
                                xaxis_title = "date",
                                yaxis_title = "count",
                                height=500)

        st.plotly_chart(trend_fig, theme='streamlit', use_container_width=True)
 
        UseCountryUnique = list(appCountRet['name'].unique())

        tabSeries = st.tabs(UseCountryUnique)
        for idx in range(len(tabSeries)) :
            appUsage = appCountRet[appCountRet['name'] == UseCountryUnique[idx]]
            appUnique = appUsage['foreground_app'].unique()
            
            usabilty_fig = go.Figure()
            usabilty_fig.add_trace(go.Scatter(
                x = appUsage['count'].unique(),
                y = appUnique,
                marker = dict(color='gold', size=12),
                mode = 'markers'
            ))
            
            usabilty_fig.update_layout(title=f"Voice foreground_app Usage Country : {UseCountryUnique[idx]}", 
                            xaxis_title = "Usability",
                            yaxis_title = "Search foreground_app",
                            height=700)
            
            with tabSeries[idx] :
                st.plotly_chart(usabilty_fig, theme='streamlit', use_container_width=True)
        
        ret = voiceData[[ 'foreground_app', 'input_type']].value_counts().reset_index()
        fig = px.treemap(ret, path=[px.Constant("all"),'foreground_app','input_type'], values='count', color='foreground_app', title='input_type count')
        st.plotly_chart(fig, use_container_width=True)

    # mrcu_key:매직리모컨, voice_far:원거리 음성, mobile: ThinQ앱, voiceGuide:음성 도움말
    # 통합검색 실행 방법 확인
    elif msg == 'NL_ACTIVATE_SEARCH':
        accumulativeRet = voiceData[['log_date_dt', 'name']].value_counts().reset_index().sort_values(by='log_date_dt').reset_index(drop=True)
        appCountRet = voiceData[['foreground_app','name']].value_counts().reset_index().sort_values(by='count', ascending=False).reset_index(drop=True)

        maxXaxis = accumulativeRet.nlargest(1, 'count')['log_date_dt'].unique()[0]
        
        trend_fig = px.bar(accumulativeRet, x='log_date_dt', y='count', color='name') 

        trend_fig.update_layout(title="Search Usage Method Trend Trend (Country)",
                                xaxis_title = "date",
                                yaxis_title = "count",
                                height=500)

        st.plotly_chart(trend_fig, theme='streamlit', use_container_width=True)
        
        UseCountryUnique = list(appCountRet['name'].unique())

        tabSeries = st.tabs(UseCountryUnique)
        for idx in range(len(tabSeries)) :
            appUsage = appCountRet[appCountRet['name'] == UseCountryUnique[idx]]
            appUnique = appUsage['foreground_app'].unique()
            
            usabilty_fig = go.Figure()
            usabilty_fig.add_trace(go.Scatter(
                x = appUsage['count'].unique(),
                y = appUnique,
                marker = dict(color='gold', size=12),
                mode = 'markers'
            ))
            
            usabilty_fig.update_layout(title=f"Search foreground_app Usage Country : {UseCountryUnique[idx]}", 
                            xaxis_title = "Usability",
                            yaxis_title = "voice_input foreground_app",
                            height=700)
            
            with tabSeries[idx] :
                st.plotly_chart(usabilty_fig, theme='streamlit', use_container_width=True)
        
        ret = voiceData[[ 'foreground_app', 'input_type']].value_counts().reset_index()
        fig = px.treemap(ret, path=[px.Constant("all"),'foreground_app','input_type'], values='count', color='input_type', title='voice input_type count')
        st.plotly_chart(fig, use_container_width=True)
    
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
    
    world_cntryCode = readCountryJson()
    homeData = set_keyData(data, msg)
    homeData = homeData.merge(world_cntryCode, left_on='country', right_on='country2Code')
    
    # 1. 사용성 분석 (NL_APP_LAUNCH) 국가별 분석 필요
    if msg == 'NL_APP_LAUNCH' :
        normalRet = homeData[['log_date_dt','app_id']].value_counts().reset_index().sort_values(by='log_date_dt', ascending=True).reset_index(drop=True)
        accumulativeRet = homeData[['log_date_dt', 'name']].value_counts().reset_index().sort_values(by='log_date_dt').reset_index(drop=True)
        appCountRet = homeData[['app_id','name']].value_counts().reset_index().sort_values(by='count', ascending=False).reset_index(drop=True)

        maxXaxis = accumulativeRet.nlargest(1, 'count')['log_date_dt'].unique()[0]
        
        # trend_fig = px.scatter(accumulativeRet, x='log_date', y='count', trendline="ols")
        trend_fig = px.bar(accumulativeRet, x='log_date_dt', y='count', color='name') 
        # trend_fig.add_vline(x=maxXaxis, line_width=1.5, line_dash='dash', line_color='red')

        trend_fig.update_layout(title="App Usage Logs Trend (Country)",
                                xaxis_title = "date",
                                yaxis_title = "count",
                                height=500)

        st.plotly_chart(trend_fig, theme='streamlit', use_container_width=True)
        
        ###### App Usage (Country) #####
        UseCountryUnique = list(appCountRet['name'].unique())

        tabSeries = st.tabs(UseCountryUnique)
        for idx in range(len(tabSeries)) :
            appUsage = appCountRet[appCountRet['name'] == UseCountryUnique[idx]]
            appUnique = appUsage['app_id'].unique()
            
            usabilty_fig = go.Figure()
            usabilty_fig.add_trace(go.Scatter(
                x = appUsage['count'].unique(),
                y = appUnique,
                marker = dict(color='gold', size=12),
                mode = 'markers'
            ))
            
            usabilty_fig.update_layout(title=f"App Usage Country : {UseCountryUnique[idx]}", 
                            xaxis_title = "Usability",
                            yaxis_title = "app_id",
                            height=700)
            
            
            with tabSeries[idx] :
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
        '''
        soc_temperature : SoC 온도 데이터 제공
        core_iddq, cpu_iddq : 무부하상태의 전류값 출력(누설전류)
        '''
        keyLst = ['soc_temperature', 'core_iddq', 'cpu_iddq']
        for key in keyLst :
            thermalData = data
            thermalData[key] = data['message_data'].apply(lambda x : x.get(key, "None"))

    # split
    #### distplot #### not create tab series, just check to see distribution
        group_labels = keyLst
        colors = ['#393E46', '#2BCDC1', '#F66095']
    
        thermalTempeatureData = thermalData[['log_date', 'context_name', 'message_id', 'message_data', 'soc_temperature']].sort_values(by='log_date', ascending=True)
        thermalTempeatureData = thermalTempeatureData.drop(thermalTempeatureData[thermalTempeatureData['soc_temperature'] == 'None'].index)

        coreIddqData = thermalData[['log_date', 'context_name', 'message_id', 'message_data', 'core_iddq']].sort_values(by='log_date', ascending=True)
        coreIddqData = coreIddqData.drop(coreIddqData[coreIddqData['core_iddq'] == 'None'].index)
        
        cpuIddqData = thermalData[['log_date', 'context_name', 'message_id', 'message_data', 'cpu_iddq']].sort_values(by='log_date', ascending=True)
        
        cpuIddqData = cpuIddqData.drop(cpuIddqData[cpuIddqData['cpu_iddq'] == 'None'].index)

        hist_data = [np.array(thermalTempeatureData['soc_temperature'].values.tolist()).astype('int'), np.array(coreIddqData['core_iddq'].values.tolist()).astype('int'), np.array(cpuIddqData['cpu_iddq'].values.tolist()).astype('int')]

        fig = ff.create_distplot(hist_data, group_labels, colors=colors, show_curve=True)
    
        fig.update_layout(title='Thermal Data Distribution',
                            height = 500)
        
        st.plotly_chart(fig, theme='streamlit', use_container_width=True)

        
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

        appPop_fig.update_layout(title='App Download Popularity',
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
        # keylst = list(moduleData['message_data'].iloc[0].keys())
        
        # data 형식이 다를 수도 있는 case가 있음
        # set -> list
        ## test ##
        
        uniqueKeylist = []
        keydata = moduleData['message_data'].values.tolist()
        
        for data in keydata :
            for key in data.keys() :
                uniqueKeylist.append(key)
        
        uniqueKeySet = set(uniqueKeylist) # 중복 제거
        keylst = list(uniqueKeySet)
        
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

def readCountryJson() :
    with open('country.json') as f: 
        js = json.loads(f.read())
    
    cntryCode = pd.DataFrame(js, columns=['country2Code', 'country3Code'])
    world = gpd.read_file(gpd.datasets.get_path("naturalearth_lowres"))
    world_cntryCode = world.merge(cntryCode, left_on='iso_a3', right_on='country3Code')   

    
    return world_cntryCode