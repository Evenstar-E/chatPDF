import time

from PIL import Image
import pymysql
from dotenv import load_dotenv
import streamlit as st
from PyPDF2 import PdfReader
from langchain.text_splitter import CharacterTextSplitter
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.vectorstores import FAISS
from langchain.chains.question_answering import load_qa_chain
from langchain.callbacks import get_openai_callback
from streamlit_chat import message
from langchain.chat_models import ChatOpenAI
import base64
from pathlib import Path
import tempfile


st.set_page_config(page_title="ChatPDF",page_icon="🧊",layout="wide")

con = pymysql.connect(
    host = "127.0.0.1",
    port = 3306
    user = "root",
    password = "2592t03081",
    database = "TESTDB",
    charset="utf8"
)

c = con.cursor()

def create_table():
    c.execute('CREATE TABLE IF NOT EXISTS users(username TEXT, password TEXT, status int)')
    con.commit()

def add_userdata(username,password):

    if c.execute('SELECT username FROM users WHERE username = %s',(username)):
        st.warning("用户名已存在，请更换一个新的用户名")
    else:
        c.execute('INSERT INTO users(username,password,status) VALUES(%s,%s,0)',(username,password))
        con.commit()



def login_user(username,password):

    if c.execute('SELECT username FROM users WHERE username = %s AND status = 0', (username)):
        c.execute('SELECT * FROM users WHERE username = %s AND password = %s ', (username, password))
        data = c.fetchall()
        c.execute('UPDATE users set status = 1 where username = %s AND password = %s',(username, password))
        con.commit()
        return data
    else:
        st.warning("用户名不存在，请先选择注册按钮完成注册。或您已经在别的地方登录")

def view_all_users():
    c.execute('SELECT * FROM userstable')
    data = c.fetchall()
    return data

@st.cache_data
def preface():
    col1, col2 = st.columns([1, 2])
    with col1:
        image = Image.open('nkd_logo.png')
        st.image(image)
        st.markdown('# 　　　   :100:ChatPDF:100:')
        st.markdown(
            '##### ChatPDF是一个基于Python的PDF处理工具，它可以用于创建、合并、拆分、加密和解密PDF文件，以及提取文本和图像等。ChatPDF提供了简单易用的API，使得用户可以方便地完成各种PDF处理任务。ChatPDF还是一种工具，它使用户能够像人一样与他们的PDF文档进行交互。它的工作原理是分析PDF文件以创建语义索引，然后将相关段落呈现给文本生成AI。')

        st.markdown(
            '### 您可以在右侧:point_right:看到相关使用教程和演示视频，您也可以在左侧:point_left:选择注册、登录、注销等选项.')

    with col2:
        st.markdown('## 　　　这里是使用教程:point_down:')
        st.markdown(
            '#### 　　　　　　　　:one:首先您可以点击页面左侧的:arrow_forward:并点击注册按钮（若您已有账号则可以跳过使用教程）')
        st.markdown(
            '#### 　　　　　　　　:two:接着您需要填写您想要注册的账户名:satisfied:和您的密码:lock:')
        st.markdown(
            '#### 　　　　　　　　:three:然后您可以点击登录来进入ChatPDF的使用')
        st.markdown(
            '#### 　　　　　　　　:four:上传您的PDF并开始您的使用吧!:tada::tada::tada:')
        st.markdown('## 　　　这里是演示视频:point_down:')
        col3, col4 = st.columns([1, 5])
        with col4:
            video_file = open('show.mp4', 'rb')
            video_bytes = video_file.read()

            st.video(video_bytes)
def main():
    create_table()
    menu = ["首页","登录","注册"]

    if 'count' not in st.session_state:
        st.session_state.count = 0

    choice = st.sidebar.selectbox("选项", menu)
    st.sidebar.markdown(
        """
         <style>
         [data-testid="stSidebar"][aria-expanded="true"] > div:first-child {
             width: 300px;
         }
         [data-testid="stSidebar"][aria-expanded="false"] > div:first-child {
             width: 300px;
             margin-left: -200px;
         }
         </style>
         """,
        unsafe_allow_html = True)

    if choice =="首页":
        preface()

    elif choice =="登录":
        st.sidebar.subheader("登录区域")

        username = st.sidebar.text_input("用户名")
        password = st.sidebar.text_input("密码",type = "password")

        menu_1 = ["请选择登录或者注销","登录", "注销"]

        choice_1 = st.sidebar.selectbox("开始登录",menu_1)
        if choice_1 == "登录":
            logged_user = login_user(username,password)

            if logged_user:
                st.session_state.count += 1

                if 'prompts' not in st.session_state:
                    st.session_state.prompts = []
                if 'responses' not in st.session_state:
                    st.session_state.responses = []

                if st.session_state.count >= 1:
                    st.sidebar.success("您已登录成功，您的用户名是 {}".format(username))
                    st.sidebar.info("退出前请点击注销")



                    col2, col1 = st.columns([1, 2])

                    load_dotenv()
                    # Left column: Upload PDF text
                    col1.header("Upload PDF Text")
                    col2.header("Ask your PDF  ")

                    # upload file
                    pdf = col1.file_uploader("Upload your PDF", type="pdf")

                    # time.sleep(10)

                    if pdf is not None:
                        pdf_reader = PdfReader(pdf)

                        text = ""

                        for page in pdf_reader.pages:
                            text = text + page.extract_text()

                        with col1:
                            if pdf is not None:
                                with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
                                    fp = Path(tmp_file.name)
                                    fp.write_bytes(pdf.getvalue())
                                    with open(tmp_file.name, "rb") as f:
                                        base64_pdf = base64.b64encode(f.read()).decode('utf-8')
                                    pdf_display = f'<embed src="data:application/pdf;base64,{base64_pdf}" ' \
                                                  f'width="1100" height="1500" type="application/pdf">'
                                    st.markdown(pdf_display, unsafe_allow_html=True)
                        text_splitter = CharacterTextSplitter(
                            chunk_size=1000,
                            chunk_overlap=200,
                        )
                        chunks = text_splitter.split_text(text)

                    # create embeddings
                        embeddings = OpenAIEmbeddings()
                        knowledge_base = FAISS.from_texts(chunks, embeddings)


                    def send_click():
                        if st.session_state.user != '':
                            prompt = st.session_state.user
                            model_name = "gpt-3.5-turbo-16k"
                            if prompt:
                                docs = knowledge_base.similarity_search(prompt)
                            llm = ChatOpenAI(model_name=model_name)
                            chain = load_qa_chain(llm, chain_type="stuff")
                            with get_openai_callback() as cb:
                                response = chain.run(input_documents=docs, question=prompt)
                            st.session_state.prompts.append(prompt)
                            st.session_state.responses.append(response)

                    # show user input
                    with col2:

                        st.text_input("Ask a question about your PDF:", key="user")
                        st.button("Send", on_click=send_click)
                        if st.session_state.prompts:
                            for i in range(len(st.session_state.responses) - 1, -1, -1):
                                message(st.session_state.prompts[i], is_user=True, key=str(i) + '_user',
                                        allow_html=True)
                                message(st.session_state.responses[i], key=str(i), seed='Milo', allow_html=True)
            else:
                st.sidebar.warning("用户名或者密码不正确，请检查后重试。")
        elif choice_1 == "注销":
            sql = "UPDATE users SET status = 0 WHERE username = '%s'" % (username)
            c.execute(sql)
            con.commit()
            st.sidebar.info("您已注销，请选择登录重新登录")
        else:
            preface()
    elif choice =="注册":
        preface()
        if 'count' not in st.session_state:
            st.session_state.count = -1
        new_user = st.sidebar.text_input("用户名")
        new_password = st.sidebar.text_input("密码",type = "password")

        if st.sidebar.button("注册"):
            create_table()
            add_userdata(new_user,new_password)
            st.balloons()
            st.sidebar.success("恭喜，您已成功注册！")
            st.sidebar.info("请选择‘登录’选项进行登录")
            time.sleep(0.5)
            preface()

if __name__=="__main__":
    main()
