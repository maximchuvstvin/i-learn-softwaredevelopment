import pandas as pd
import plotly.express as px
import streamlit as st
from PIL import Image

df = pd.read_csv('vehicles_us.csv')

# 1. fillna() for boolean if car is 4wd
df['is_4wd'] = df['is_4wd'].fillna(0).astype(bool)

# 2. fillna('unknown') for paint_color
df['paint_color'] = df['paint_color'].fillna('unknown')

# 3. implicit duplicates (2) . Let'a replace duplicated models
# dictianary of correct models (keys) and wrong|duplicate models (lists)
wrong_models = {
    'ford f-150' : ['ford f150'],
    'ford f-250' : ['ford f250'],
    'ford f-250 sd': ['ford f-250 super duty', 'ford f250 super duty' ],
    'ford f-350 sd' : ['ford f350 super duty'],
    'ford f-350' : ['ford f350'],
    'ford f-150 supercrew cab xlt' : ['ford f150 supercrew cab xlt'],
}

def replace_wrong_models(correct_model, wrong_models, series_to_check):
    series_to_check.replace(to_replace = wrong_models, value = correct_model, inplace = True)

for key, value in wrong_models.items():
    replace_wrong_models(key, value, df['model'])

# let's create column 'maker' and 'model_sep' separated from model
df['maker'] = df['model'].apply(lambda x: x.split()[0])
df['model_sep'] = df['model'].apply(lambda x: ' '.join(x.split()[1:]))

# 4. check obvious duplicates except days_listed to find if identical cars were published simultaneously
unwanted = ['days_listed']
col_to_check = [x for x in df.columns if x not in unwanted]
df = df.drop_duplicates(subset=col_to_check)

# function to choose DataFrame for analysis (either drop NaN or replace with -1 to track them further, remove top outliers in price and odometer)
def dropping(df_input, drop_na : bool = False, drop_outliers : bool = False, quantile_to_drop = 0.01):
    if drop_outliers and not 0 <= quantile_to_drop <= 1: 
        print('set correct quantile from 0 to 1')
        return
    elif drop_na:
        df = df_input.dropna()
        if drop_outliers:
            q_hi_p  = df['price'].quantile(1-quantile_to_drop)
            q_low_p = df['price'].quantile(quantile_to_drop)
            q_hi_o  = df['odometer'].quantile(1-quantile_to_drop)
            q_low_o = df['odometer'].quantile(quantile_to_drop)
            return df[(df["price"] < q_hi_p) & (df["price"] > q_low_p) &
                      (df["odometer"] < q_hi_o) & (df["odometer"] > q_low_o)]
        else:
             return df         
    else:
        df = df_input.fillna(-1)
        if drop_outliers:
            q_hi_p  = df['price'].quantile(1-quantile_to_drop)
            q_low_p = df['price'].quantile(quantile_to_drop)
            q_hi_o  = df[df['odometer']>0]['odometer'].quantile(1-quantile_to_drop)
            q_low_o = df[df['odometer']>0]['odometer'].quantile(quantile_to_drop)
            return df[(df["price"] < q_hi_p) & (df["price"] > q_low_p) &
                      (df["odometer"] < q_hi_o) & (df["odometer"] > q_low_o)]
        else:
             return df
        
# Building app

# initial configs
st.set_page_config(page_title="i-learn-streamlit", layout="wide")
col0 =st.sidebar
col1, col2, col3 = st.columns([2,5,2])

# building sidebar to get final filtered dataset
col0.header('Controls')

# drop NA and outliers
drop_na = col0.checkbox('delete ads with missing information?')
outliers = col0.checkbox('delete outliers?')

quantile_to_drop = 0
if outliers:
    quantile_to_drop = col0.slider('How much to delete?', 0, 10, value=1, step=1, format='%f%%' ) / 100

df_final = dropping(df, drop_na=drop_na, drop_outliers = outliers, quantile_to_drop = quantile_to_drop)

# filters
# 1. makers
makers = sorted(df_final['maker'].unique())
selected_makers = col0.multiselect('Manufacturer', makers, makers)
selected_makers_b = df_final['maker'].isin(selected_makers)

# 2. price range
current_max_price = int(df_final['price'].max())
min_price, max_price = col0.slider('Set price range', 0, current_max_price, (0, current_max_price), step=1000)
price_range_b = (df_final['price'] >= min_price) & (df_final['price'] <= max_price)

# 3. color
paint_colors = sorted(df_final['paint_color'].unique())
selected_paint_colors = col0.multiselect('Choose color', paint_colors, paint_colors)
selected_paint_colors_b = df_final['paint_color'].isin(selected_paint_colors)

#filtered dataset

df_filtered = df_final[selected_makers_b
                       & price_range_b
                       & selected_paint_colors_b]


rows_initial = len(df)
rows_after_drop = len(df_final)
rows_dropped = rows_initial - rows_after_drop
rows_after_filter = len(df_filtered)
rows_filtered = rows_after_drop - rows_after_filter

# header
img = Image.open('logo.png')
col2.image(img)
col2.title('Let\'s analyse some data about used cars')
col2.write(f'Initial number of rows: {str(rows_initial)}')
col2.write(f'Number of rows after drop: {str(rows_after_drop)}\t\tRows dropped:  {str(rows_dropped)}')
col2.write(f'Number of rows after filter: {str(rows_after_filter)}\t\tRows filtered:  {str(rows_filtered)}')

condition_order = ['new', 'like new', 'excellent', 'good', 'fair', 'salvage']

# dataset
column_order = ['maker', 
                'model_sep',
                'model_year',
                'paint_color',
                'type',
                'condition',
                'odometer',
                'cylinders',
                'fuel',                
                'transmission',
                'is_4wd',
                'price',
                'date_posted',
                'days_listed']
col2.subheader('Our dataset')
col2.dataframe(df_filtered,
               # hide_index=True,
               column_order=column_order)

# figure 1
col2.subheader('Number of ads over Price')
fig = px.histogram(df_filtered,
                   x='price',
                   nbins=30,
                   color='condition',
                   category_orders={'condition':condition_order},                   
                   # histnorm='probability',
                   # barmode='stack',
                   # title = 'Number of ads over Price',
                   width = 1000, height=500)

col2.plotly_chart(fig)

# figure 2
col2.subheader('Car price over odometer')
fig1 = px.scatter(df_filtered,
                     x='odometer',
                     y='price',
                     color='condition',
                     category_orders={'condition':condition_order},
                     opacity=0.8,
                     # title = 'Car price over odometer',
                     width = 1000, height=500)
col2.plotly_chart(fig1)

# figure 3
col2.subheader('Heatmap of average Price over odometer and age')
fig2 = px.density_heatmap(df_filtered,
                          x="odometer", y="model_year", z="price",
                          histfunc="avg",
                          facet_col='condition',
                          facet_col_wrap=3,
                          facet_row_spacing = 0.01, facet_col_spacing = 0.01,
                          color_continuous_scale=['White', 'Orange', 'Red', 'Purple'],
                          range_x = [0, 290000], range_y = [1950, 2019],
                          category_orders={'condition':condition_order},                          
                          nbinsx=100, nbinsy=150,
                          # title='Heatmap of average Price over odometer and age',
                          width = 1000, height=500)
fig2.update_layout(xaxis=dict(showgrid=False), yaxis=dict(showgrid=False))
col2.plotly_chart(fig2)

# figure 4
col2.subheader('Just for fun: look most popular model and their prices')
fig3 = px.sunburst(df_filtered, path=['maker', 'model_sep'],
                   #values='pop',
                  color='price',
                  #hover_data=['iso_alpha'],
                  color_continuous_scale=['Green', 'Yellow', 'Orange', 'Red', 'Purple', 'Blue'],
                  width = 1000, height=1000,                  
                  )
fig3.update_traces(insidetextorientation='radial') 
col2.plotly_chart(fig3)