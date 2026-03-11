import streamlit as st
import pandas as pd
import random
import json
import os
import io

# --- 1. 설정 및 데이터 로드 ---
st.set_page_config(page_title="협업 문제해결 수업 팀 구성", layout="wide")

DB_FILE = "students_db.csv"
RESPONSES_FILE = "responses.json"

# 하위 질문 정의
TENDENCIES = {
    "리더형": [
        "과제가 주어지면 전체적인 목차나 방향성을 먼저 기획한다.",
        "조원들의 의견이 충돌할 때 중재하고 결론을 도출하는 편이다.",
        "일정에 맞춰 진행 상황을 점검하고 팀원들을 독려한다.",
        "역할 분담이 모호할 때 나서서 일을 배분한다.",
        "팀의 최종 결과물에 대해 강한 책임감을 느낀다."
    ],
    "분위기 메이커형": [
        "첫 모임의 어색한 분위기를 깨고 대화를 주도하는 편이다.",
        "브레인스토밍 과정에서 기발하거나 엉뚱한 아이디어를 잘 낸다.",
        "팀원들의 의견에 긍정적인 리액션을 잘해준다.",
        "딱딱한 회의보다는 자유롭고 편안한 분위기를 선호한다.",
        "조원들 간의 갈등 상황에서 유머나 부드러운 화법으로 긴장을 푼다."
    ],
    "아나운서형": [
        "완성된 자료를 바탕으로 깔끔하게 대본을 작성하는 것에 자신 있다.",
        "여러 사람 앞에서 긴장하지 않고 말을 조리 있게 잘한다.",
        "복잡한 내용을 시각 자료와 함께 타인에게 쉽게 설명할 수 있다.",
        "발표 후 이어지는 질의응답에 순발력 있게 대처한다.",
        "비언어적 표현을 활용해 청중을 설득하는 것을 좋아한다."
    ],
    "성실한 팔로워형": [
        "나에게 주어진 분량의 자료 조사를 데드라인 전까지 완벽하게 해낸다.",
        "조장이 정해준 규칙이나 회의 일정을 엄격하게 준수한다.",
        "회의 내용을 꼼꼼하게 기록하여 서기 역할을 수행하는 편이다.",
        "전면에 나서기보다는 팀의 기초 자료를 수집하고 팩트 체크하는 데 능하다.",
        "PPT 제작이나 문서 편집 등 실무적인 보조 작업에 강점이 있다."
    ],
    "경청형": [
        "회의 중 즉각적으로 말하기보다 다른 사람들의 의견을 끝까지 경청한다.",
        "면대면 대화보다는 카톡 등 텍스트를 통한 의견 교환이 훨씬 편하다.",
        "생각이나 논리가 완전히 정리되기 전에는 섣불리 발언하지 않는다.",
        "다수의 의견이 정해지면 이견 없이 조용히 따르는 편이다.",
        "조별 과제라도 혼자 맡은 파트를 조용히 끝내는 것을 선호한다."
    ]
}

@st.cache_data
def load_students_db():
    try:
        df = pd.read_csv(DB_FILE, dtype={'학번': str})
    except UnicodeDecodeError:
        df = pd.read_csv(DB_FILE, encoding='cp949', dtype={'학번': str})
    df['E-MAIL'] = df['E-MAIL'].str.strip()
    df['학번'] = df['학번'].str.strip()
    return df

def load_responses():
    if os.path.exists(RESPONSES_FILE):
        with open(RESPONSES_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_responses(data):
    with open(RESPONSES_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

# --- 2. 세션 초기화 (무작위 문항 섞기 및 상태 관리) ---
if 'shuffled_qs' not in st.session_state:
    all_qs = [{"category": k, "question": q} for k, v in TENDENCIES.items() for q in v]
    random.shuffle(all_qs)
    st.session_state.shuffled_qs = all_qs

if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user_info = None
    st.session_state.is_admin = False

# 팀 구성 결과를 보관할 세션 변수 추가
if 'teams_result' not in st.session_state:
    st.session_state.teams_result = None

students_df = load_students_db()
responses = load_responses()

# --- 3. 로그인 화면 ---
if not st.session_state.logged_in:
    st.title("협업 문제해결 수업 설문 로그인")
    login_type = st.radio("로그인 유형", ["학생 로그인", "관리자 로그인"])
    
    with st.form("login_form"):
        if login_type == "학생 로그인":
            st.info("E-MAIL이 아이디, 학번이 비밀번호입니다.")
            input_id = st.text_input("E-MAIL")
            input_pw = st.text_input("학번 (비밀번호)", type="password")
        else:
            input_id = st.text_input("관리자 ID")
            input_pw = st.text_input("관리자 비밀번호", type="password")
            
        submit_btn = st.form_submit_button("로그인")
        
        if submit_btn:
            if login_type == "관리자 로그인":
                if input_id == "admin" and input_pw == "admin1234": 
                    st.session_state.logged_in = True
                    st.session_state.is_admin = True
                    st.rerun()
                else:
                    st.error("관리자 정보가 일치하지 않습니다.")
            else:
                user = students_df[(students_df['E-MAIL'] == input_id.strip()) & (students_df['학번'] == input_pw.strip())]
                if not user.empty:
                    st.session_state.logged_in = True
                    st.session_state.is_admin = False
                    st.session_state.user_info = user.iloc[0].to_dict()
                    st.rerun()
                else:
                    st.error("이메일 또는 학번을 확인해주세요.")

# --- 4. 학생 설문 화면 ---
elif not st.session_state.is_admin:
    st.title(f"환영합니다, {st.session_state.user_info['이름']} 학생!")
    
    user_id = st.session_state.user_info['학번']
    if user_id in responses:
        st.success("이미 설문을 완료하셨습니다. 참여해 주셔서 감사합니다.")
        if st.button("로그아웃"):
            st.session_state.logged_in = False
            st.rerun()
    else:
        st.write("아래 설문을 작성하여 제출해 주세요.")
        
        with st.form("survey_form"):
            gender = st.radio("가. 성별", ["남성", "여성"])
            mbti = st.selectbox("나. MBTI", [
                "ISTJ", "ISFJ", "INFJ", "INTJ", "ISTP", "ISFP", "INFP", "INTP",
                "ESTP", "ESFP", "ENFP", "ENTP", "ESTJ", "ESFJ", "ENFJ", "ENTJ"
            ])
            
            st.markdown("### 다. 조별 활동에 있어 나의 경향")
            st.write("본인에게 해당한다고 생각되는 항목을 모두 선택해 주세요.")
            
            selected_qs = []
            for item in st.session_state.shuffled_qs:
                if st.checkbox(item["question"]):
                    selected_qs.append(item["category"])
                    
            interest = st.text_input("라. 관심주제")
            comments = st.text_area("마. 하고 싶은 말(요청사항)")
            
            submit_survey = st.form_submit_button("설문 제출")
            
            if submit_survey:
                if not selected_qs:
                    st.error("조별 활동 경향 항목을 최소 1개 이상 선택해 주세요.")
                else:
                    tendency_counts = {k: selected_qs.count(k) for k in TENDENCIES.keys()}
                    max_tendency = max(tendency_counts, key=tendency_counts.get)
                    
                    responses[user_id] = {
                        "이름": st.session_state.user_info['이름'],
                        "학번": user_id,
                        "소속": st.session_state.user_info['소속'],
                        "성별": gender,
                        "MBTI": mbti,
                        "성향": max_tendency,
                        "관심주제": interest,
                        "하고싶은말": comments
                    }
                    save_responses(responses)
                    st.success("제출이 완료되었습니다!")
                    st.rerun()

# --- 5. 관리자 화면 (조 편성 및 초기화 기능 포함) ---
else:
    st.title("관리자 대시보드")
    
    if st.button("로그아웃"):
        st.session_state.logged_in = False
        st.rerun()
        
    st.subheader("현재 응답 현황")
    if not responses:
        st.info("아직 응답한 학생이 없습니다.")
    else:
        res_df = pd.DataFrame.from_dict(responses, orient='index')
        st.dataframe(res_df)
        
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            res_df.to_excel(writer, index=False, sheet_name='Responses')
        excel_data = output.getvalue()
        
        col1, col2 = st.columns(2)
        with col1:
            st.download_button(label="📥 엑셀로 응답내역 다운로드",
                               data=excel_data,
                               file_name="student_responses.xlsx",
                               mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        with col2:
            if st.button("🚨 전체 답변(응답데이터) 초기화", type="primary"):
                save_responses({})
                st.session_state.teams_result = None # 답변이 초기화되면 편성 결과도 초기화
                st.rerun()

    st.divider()
    st.subheader("자동 팀 편성 및 관리")
    st.write("응답 데이터를 기반으로 10개의 팀(5명 7팀, 4명 3팀)을 구성합니다.")
    st.write("우선순위: 성향 다양성 > 성별 비율 > E/I 비율 > 전공 다양성")
    
    # 팀 구성 및 초기화 버튼 배치
    col_team1, col_team2 = st.columns(2)
    with col_team1:
        if st.button("⚙️ 팀 구성 실행"):
            if len(responses) < 47:
                st.warning(f"현재 응답자가 {len(responses)}명입니다. 전체 인원(47명)이 응답한 후 편성을 권장합니다.")
                
            students = list(responses.values())
            random.shuffle(students)
            
            teams = [{"team_id": i+1, "members": [], "capacity": 5 if i < 7 else 4} for i in range(10)]
            
            for student in students:
                best_team = None
                min_penalty = float('inf')
                s_ei = student["MBTI"][0].upper()
                
                for team in teams:
                    if len(team["members"]) >= team["capacity"]:
                        continue
                    
                    penalty = 0
                    members = team["members"]
                    
                    same_tendency = sum(1 for m in members if m["성향"] == student["성향"])
                    penalty += same_tendency * 100
                    
                    same_gender = sum(1 for m in members if m["성별"] == student["성별"])
                    penalty += same_gender * 50
                    
                    same_ei = sum(1 for m in members if m["MBTI"][0].upper() == s_ei)
                    penalty += same_ei * 30
                    
                    same_major = sum(1 for m in members if m["소속"] == student["소속"])
                    penalty += same_major * 10
                    
                    if penalty < min_penalty:
                        min_penalty = penalty
                        best_team = team
                        
                if best_team is not None:
                    best_team["members"].append(student)
            
            # 편성 결과를 세션에 저장
            st.session_state.teams_result = teams
            st.rerun()

    with col_team2:
        if st.button("🔄 팀 구성 초기화"):
            st.session_state.teams_result = None
            st.rerun()

    # 세션에 팀 구성 결과가 존재할 경우 화면에 출력
    if st.session_state.teams_result is not None:
        st.success("팀 편성이 완료되었습니다! (아래 결과를 확인하세요)")
        for team in st.session_state.teams_result:
            with st.expander(f"Team {team['team_id']} (인원: {len(team['members'])}명)"):
                if team["members"]:
                    team_df = pd.DataFrame(team["members"])[["이름", "소속", "성별", "MBTI", "성향"]]
                    st.table(team_df)
                else:
                    st.write("배정된 인원이 없습니다.")