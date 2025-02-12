import pandas as pd
import matplotlib.pyplot as plt
import geopandas as gpd
import plotly.graph_objects as go
import plotly.io as pio

df = pd.read_excel(r"C:\Users\razin\OneDrive\Desktop\enwl_fault_data.xlsx",sheet_name = 2, header = None)

df.drop(0,axis=0,inplace = True)

                
# filter first column to 2000-2022 and sort by district code and category cause
df[0] = pd.to_numeric(df[0])
df[1] = pd.to_numeric(df[1])
cause = "Weather and Environment"
wanted_causes = ['Wind and Gale (excluding Windborne Material)',
                 'Snow, Sleet and Blizzard',
                 'Lightning',
                 'Windborne Materials',
                 'Airborne Deposits (excluding Windborne Material)',
                 'Ice',
                 'Solar Heat',
                 'Flooding',
                 'Rain',
                 'Fire not due to Faults',
                 'Condensation',
                 'Freezing Fog and Frost',
                 'Corrosion due to atmosphere/ environment']

districts = list(zip(df[1],df[2]))
districts = list(dict.fromkeys(districts))

df = df[df[7].isin(wanted_causes)]

for district_code, city in districts:
      
    df2 = df.loc[(df[0]>= 2000) & ((df[1] == district_code) & df[8].str.contains(cause))]
# plot graph
    years = df2[0]
    category = df2[7]

# Creates a group with years and categories - and counts no. of occurances in group, into a reshaped dataframe
    if df2.empty:
        continue
       
    counts = df2.groupby([years, category]).size().unstack(fill_value=0)
    bubble_size = counts.sum(axis=1)

# Plot each category as a stacked bar
# Set up the figure and axes
    fig, ax = plt.subplots()

# Accumulate the bottom for stacking
    bottom = None

    colours = {'Wind and Gale (excluding Windborne Material)' : 'blue',
'Growing or Falling Trees (not felled)':'orange',
'Snow, Sleet and Blizzard' : 'green',
'Lightning':'red',
'Windborne Materials' : 'purple',
'Corrosion' : 'yellowgreen',
'Airborne Deposits (excluding Windborne Material)' : 'pink',
'Ice' : 'gray',
'Mechanical Shock or Vibration' : 'olive',
'Solar Heat' :'yellow',
'Flooding' : 'aquamarine',
'Rain' : 'slateblue',
'Ground Subsidence' : 'lightcoral',
'Fire not due to Faults' : 'mediumpurple',
'Condensation' : 'lightblue',
'Freezing Fog and Frost' : 'lawngreen',
'Corrosion due to atmosphere/ environment' : 'lavender',
'Growing Trees' : 'cornflowerblue',
'Falling live trees (not felled)' : 'darkgreen',
'Falling dead tree' : 'darkkhaki',
    }

    
# Iterate through each category in the DataFrame
    for category in counts.columns:
        ax.bar(counts.index, counts[category], label=category, bottom=bottom, color = colours.get(category,'gray'))
    # Update bottom to be cumulative for next category
        if bottom is None:
            bottom = counts[category]
        else:
            bottom += counts[category]
            
#category_values = df2[8].unique()

# Print the unique values
#for value in category_values:
    #print(value)

# Add labels and title
    plt.xlabel("Year")
    plt.ylabel("Number of Outages")
    plt.title(f" Number of Outages in {city} over the years")
    plt.legend(title="Type of Outages", bbox_to_anchor=(1.05,1),loc='upper left')
    plt.ylim(0, counts.values.max() + 20)  # Adjust y-axis limit as needed
    plt.show()

# Convert the DataFrame to a GeoDataFrame
# Ensure the WKT column is of type string and handle NaN values
df[18] = df[18].apply(lambda x: str(x) if isinstance(x, str) else None)  # Convert invalid types to None
df = df.dropna(subset=[18])
gdf = gpd.GeoDataFrame(df, geometry=gpd.GeoSeries.from_wkt(df[18]))

# Set CRS to EPSG:27700 (British National Grid) since coordinates are in that system
gdf.set_crs('EPSG:27700', allow_override=True, inplace=True)
gdf = gdf.dropna(subset=['geometry'])

# Filter the GeoDataFrame for "Weather and Environment" category
gdf_filtered = gdf[gdf[8].str.contains(cause, na=False)]

for year in range(2000,2023):
    gdf_year = gdf_filtered[gdf_filtered[0] == year]
    
    # Correct grouping syntax by specifying the column names or column indices
    bubble_size = gdf_year.groupby([gdf_year.columns[1], gdf_year.columns[7]]).size().reset_index(name="bubble_size")
    
    # Merge the bubble size back into the GeoDataFrame (gdf_year)
    gdf_year = gdf_year.merge(bubble_size, how="left", on=[gdf_year.columns[1], gdf_year.columns[7]])
    
    north_west_bounds = {
    'xmin': 300000,  
    'xmax': 430000,  
    'ymin': 350000,  
    'ymax': 590000,}
    
    gdf_year = gdf_year.to_crs(epsg=4326) 

      # Create a scattermapbox plot
    fig = go.Figure(go.Scattermapbox(
            lat=gdf_year.geometry.y,
            lon=gdf_year.geometry.x,
            mode='markers',
            marker=go.scattermapbox.Marker(
                size=gdf_year['bubble_size'] / 2,  # Scale the bubble sizes
                color=gdf_year['bubble_size'],
                colorscale='Plasma',  # Choose the color scale
                showscale=True
            ),
            text=gdf_year[7],  # Tooltip text to show category
            hoverinfo='text+lat+lon',
        ))
    pio.renderers.default = "browser"

        # Update layout with Mapbox settings
    fig.update_layout(
            title=f"Bubble Map of Outages in {year} - North West England",
            mapbox=dict(
                accesstoken="pk.eyJ1IjoicmF6aW4wNSIsImEiOiJjbTN0NHFrcTYwNWIxMmtyMG9vcWEyYWp2In0.hN5kPtCS1JC0BOm30Qx8gg",  # Add your Mapbox access token
                style='mapbox://styles/mapbox/streets-v12',  # Map style
                center=dict(lat=gdf_year.geometry.y.mean(), lon=gdf_year.geometry.x.mean()),  # Center map on the UK
                zoom=5,  # Adjust the zoom level
            ),
            showlegend=False,
        )

        # Show the interactive map
    fig.show()