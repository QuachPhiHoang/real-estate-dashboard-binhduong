# DASHBOARD BDS BINH DUONG

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dash import Dash, dcc, html, Input, Output

try:
    # Load dữ liệu CSV
    file_path = 'bat_dong_san_com_vn_fillter_update.csv'
    df = pd.read_csv(file_path)

    # Tiền xử lý ngày tháng
    if 'Thoi_gian_dang' in df.columns:
        df['Thoi_gian_dang'] = pd.to_datetime(df['Thoi_gian_dang'], errors='coerce')
        df = df.dropna(subset=['Thoi_gian_dang'])
        df['date'] = df['Thoi_gian_dang'].dt.date
except Exception as e:
    print("❌ Lỗi load dữ liệu:", str(e))
    df = pd.DataFrame()  # Tạo DataFrame trống để tiếp tục chạy app

# App
app = Dash(__name__)
server = app.server  # 👈 CẦN THÊM DÒNG NÀY
app.title = 'Dashboard BĐS Bình Dương'

# Layout
app.layout = html.Div([
    html.H1('📊 Dashboard BĐS Bình Dương', style={'textAlign': 'center'}),

    html.Div([
        html.Label('Chọn Quận/Huyện:'),
        dcc.Dropdown(
            options=[{'label': qh, 'value': qh} for qh in sorted(df['Quan_huyen'].dropna().unique())],
            value=None,
            id='district-filter',
            multi=True,
            placeholder='-- Lọc theo Quận/Huyện --'
        )
    ], style={'width': '48%', 'display': 'inline-block'}),

    html.Div([
        html.Label('Chọn loại hình:'),
        dcc.Dropdown(
            options=[{'label': ptype, 'value': ptype} for ptype in sorted(df['Property_Type'].dropna().unique())],
            value=None,
            id='property-filter',
            multi=True,
            placeholder='-- Lọc theo Loại hình BĐS --'
        )
    ], style={'width': '48%', 'display': 'inline-block', 'float': 'right'}),

    dcc.Graph(id='bar-chart'),
    dcc.Graph(id='double-bar-chart'),
    dcc.Graph(id='ward-chart'),
    dcc.Graph(id='pie-chart'),
    dcc.Graph(id='line-chart')
])

# Callbacks
@app.callback(
    [Output('bar-chart', 'figure'),
     Output('pie-chart', 'figure'),
     Output('line-chart', 'figure'),
     Output('double-bar-chart', 'figure'),
     Output('ward-chart', 'figure')],
    
    [Input('district-filter', 'value'),
     Input('property-filter', 'value')]
)

def update_charts(selected_districts, selected_types):
    filtered_df = df.copy()

    if selected_districts:
        filtered_df = filtered_df[filtered_df['Quan_huyen'].isin(selected_districts)]

    if selected_types:
        filtered_df = filtered_df[filtered_df['Property_Type'].isin(selected_types)]

    # 1. Biểu đồ cột (bar chart)
    if not filtered_df.empty:
        bar_df = filtered_df.groupby('Quan_huyen').size().reset_index(name='total_post')
    else:
        bar_df = pd.DataFrame(columns=['Quan_huyen', 'total_post'])

    bar_fig = go.Figure()
    if not bar_df.empty:
        bar_fig.add_trace(go.Bar(
            x=bar_df['Quan_huyen'],
            y=bar_df['total_post'],
            text=bar_df['total_post'],
            textposition='auto',
            marker_color=bar_df['total_post'],
            name='Số tin'
        ))
    bar_fig.update_layout(title='Số lượng tin theo Quận/Huyện',
                          xaxis_title='Quận/Huyện',
                          yaxis_title='Số tin')

    # 2. Pie chart
    if not bar_df.empty:
        pie_fig = px.pie(bar_df, names='Quan_huyen', values='total_post',
                         title='Tỉ lệ tin đăng theo Quận/Huyện', hole=0.3)
    else:
        pie_fig = go.Figure()
        pie_fig.update_layout(title='Không có dữ liệu để hiển thị Pie Chart')

    # 3. Line chart
    if not filtered_df.empty:
        line_df = filtered_df.groupby(['date', 'Quan_huyen']).size().reset_index(name='total_post')
        line_fig = px.line(line_df, x='date', y='total_post', color='Quan_huyen',
                           title='Số lượng tin theo ngày & Quận', markers=True)
    else:
        line_fig = go.Figure()
        line_fig.update_layout(title='Không có dữ liệu để hiển thị Line Chart')

    # 4. Biểu đồ cột đôi
    if not filtered_df.empty:
        du_an_df = filtered_df[filtered_df['Property_Type'].str.contains('Dự án|Nhà đất', case=False, na=False)]
        chung_cu_df = filtered_df[filtered_df['Property_Type'].str.contains('Chung cư|Căn hộ', case=False, na=False)]

        du_an_group = du_an_df.groupby('Quan_huyen').size()
        chung_cu_group = chung_cu_df.groupby('Quan_huyen').size()

        quanhuyens = sorted(set(du_an_group.index).union(chung_cu_group.index))
        du_an_counts = [du_an_group.get(qh, 0) for qh in quanhuyens]
        chung_cu_counts = [chung_cu_group.get(qh, 0) for qh in quanhuyens]

        double_bar_fig = go.Figure()
        double_bar_fig.add_trace(go.Bar(
            x=quanhuyens, 
            y=du_an_counts, 
            text=du_an_counts,  # Hiển thị số lượng
            textposition='outside',  # Hiển thị phía trên cột
            name='Nhà đất, Dự án',
            ))
        double_bar_fig.add_trace(go.Bar(
            x=quanhuyens, 
            y=chung_cu_counts,
            text=chung_cu_counts,  # Hiển thị số lượng
            textposition='outside',  # Hiển thị phía trên cột 
            name='Chung cư, Căn hộ'))
        double_bar_fig.update_layout(
            barmode='group',
            title='Phân bố tin đăng theo khu vực và loại bất động sản',
            xaxis_title='Quận/Huyện',
            yaxis_title='Số lượng tin đăng',
            height=1000,
            uniformtext_minsize=8,
            uniformtext_mode='hide'
        )
    else:
        double_bar_fig = go.Figure()
        double_bar_fig.update_layout(title='Không có dữ liệu để hiển thị Biểu đồ Cột Đôi')


    #5. Biểu đồ theo phường (Ward)
    if not filtered_df.empty and 'Ward' in filtered_df.columns:
        ward_df = filtered_df.groupby('Ward').size().reset_index(name='total_post')
        ward_df = ward_df.sort_values('total_post', ascending=False)

        ward_fig = go.Figure()
        ward_fig.add_trace(go.Bar(
            x=ward_df['Ward'],
            y=ward_df['total_post'],
            text=ward_df['total_post'],
            textposition='outside',
            marker_color='darkgreen',
            name='Tin đăng theo phường',
        ))
        ward_fig.update_layout(title='Phường/Xã có nhiều tin đăng nhất',
                               xaxis_title='Phường/Xã',
                               yaxis_title='Số lượng tin',
                               xaxis_tickangle=-45,
                               height=1000,  # 👈 Chiều cao phù hợp hơn
                               margin=dict(t=60, b=120),  # 👈 Giảm khoảng trống dư thừa
                               )
    else:
        ward_fig = go.Figure()
        ward_fig.update_layout(title='Không có dữ liệu để hiển thị biểu đồ Phường/Xã')




    return bar_fig, pie_fig, line_fig, double_bar_fig, ward_fig



# Chạy app
if __name__ == '__main__':
    app.run_server(debug=True)
