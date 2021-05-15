# ERDDAP Status.html page dashboard


This [Streamlit](https://streamlit.io) app, uses [erddap-python](https://github.com/hmedrano/erddap-python) library to collect metrics from public ERDDAP Servers, and uses various plotting libraries to create an interactive dashboard.

[ERDDAP](https://coastwatch.pfeg.noaa.gov/erddap/information.html) it's a data distribution server that gives you a simple, consistent way to download subsets of scientific datasets in common file formats and make graphs and maps.

ERDDAP generates a web page (status.html) with various statistics of the server status. In this demo, we use the erddap-python library that parses all this information and returns it as scalars and DataFrames. With this data, we created this simple dashboard to explore the statistics visually.

Access the web application [here](https://share.streamlit.io/hmedrano/erddap-status-dashboard/main/dashboard_streamlit_app.py)

![Streamlit screenshot](demo-dashboard.png "Major Load Datasets timeseries plots")]

## Development

Install requirements
```
pip install -r requirements.txt
```

Run the app locally

```
streamlit run dashboard_streamlit_app.py
```

----

