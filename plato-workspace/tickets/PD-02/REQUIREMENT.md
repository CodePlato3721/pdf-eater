目前项目是后端用 python 前端用 streamlit
要改成前后端分离
后端用 fastapi暴露接口
前端用react做界面。
但是现在这个ticket只做后端部分：把后端服务封装成 fastapi 接口
这个改动是侵入性的，可以直接断开和 streamlit的连接