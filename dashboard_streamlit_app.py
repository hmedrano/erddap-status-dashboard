import streamlit as st
from erddapClient import ERDDAP_Server
import altair as alt

st.set_page_config(page_title="ERDDAP Status Dashboard")
# DEFAULT ERDDAP Server
DEFAULT_ERDDAPURL = 'https://coastwatch.pfeg.noaa.gov/erddap'
# Check if url query param is provided
if 'experimental_get_query_params' in dir(st):
    query_params = st.experimental_get_query_params()
    DEFAULT_ERDDAPURL = str(query_params["url"][0]) if "url" in query_params else 'https://coastwatch.pfeg.noaa.gov/erddap'

# Reference to the Server connection object
gremote = None
lasterddapurl = None

def getStatusData(remote, erddapurl, force=False):
    if remote is None:
        remote = ERDDAP_Server(erddapurl)
        lasterddapurl = erddapurl
    else:
        if erddapurl != lasterddapurl:
            remote = ERDDAP_Server(erddapurl)
            lasterddapurl = erddapurl

    remote.parseStatusPage(force=force)
    statusValues = remote.statusValues
    statusValues['version'] = remote.version_numeric
    return statusValues


def plotMLDTimeseries(sdf):

    st.subheader("Major Load Datasets Time Series")
    st.write('Major Load Dataset event it\'s when ERDDAP reprocesses the configuration file datasets.xml, including checking each dataset to see if it needs to be reloaded according to the reload settings, for most servers the default its every 15 minutes')
    # st.write('Various metrics since last 95 (ish) MLD events')

    sdfnoindex = sdf['major_loaddatasets_timeseries'].reset_index()

    # Data MDL Time
    mldtime = sdfnoindex[['timestamp', 'mld_time']]
    # Data MLD try vs fails data
    ntryfail = sdfnoindex[['timestamp','DL_ntry','DL_nfail']]
    ntryfail = ntryfail.rename(columns={'DL_ntry' : 'Load tries' , 'DL_nfail' : 'Failed' })
    ntryfail = ntryfail.melt('timestamp', var_name='type', value_name='value')
    ntryfail = ntryfail.rename(columns={'type' : 'variable'})
    # Data responses failed vs successful
    nresponses = sdfnoindex[['timestamp','R_nsuccess','R_nfailed']]
    nresponses = nresponses.rename(columns={'R_nsuccess' : 'Successful' , 'R_nfailed' : 'Failed' })
    nresponses = nresponses.melt('timestamp', var_name='type', value_name='value')
    nresponses = nresponses.rename(columns={'type' : 'variable'})
    # Data memory usage
    memoryusage = sdfnoindex[['timestamp','M_inuse','M_highwater']]
    memoryusage = memoryusage.rename(columns={'M_inuse' : 'In use' , 'M_highwater' : 'Highwater' })
    memoryusage = memoryusage.melt('timestamp', var_name='type', value_name='value')
    memoryusage = memoryusage.rename(columns={'type' : 'variable'})    

    mldTimePlot = ( 
        alt.Chart(mldtime)
        .mark_line()
        .transform_fold(fold=['MLD time'],as_=['variable', 'value'])
        .encode(
            x=alt.X('timestamp', title=''),
            y=alt.Y('mld_time', title='seconds'),
            color='variable:N',
            tooltip=['mld_time']
        )
        .configure_axis(grid=False)
        .configure_view(strokeOpacity=0)
        .properties(width=600, title='Seconds to complete MLD Event') 
    )

    st.altair_chart(mldTimePlot, use_container_width=True)

    mldTryFailsPlot = (
        alt.Chart(ntryfail)
        .mark_bar(opacity=.7, width=6)
        .encode(
            x='timestamp',
            y=alt.Y('value', title='datasets', stack=None),
            color=alt.Color('variable', scale=alt.Scale(
                domain=['Load tries', 'Failed'], range=['green', 'red']
            )),
            tooltip='value'
        )
        .configure_axis(grid=False)
        .configure_view(strokeOpacity=0)
        .properties(width=600, title='Datasets loaded vs failed') 
    )

    st.altair_chart(mldTryFailsPlot, use_container_width=True)

    reqSuccessfulFailsPlot = (
        alt.Chart(nresponses)
        .mark_line()
        .encode(
            x='timestamp',
            y=alt.Y('value', title='requests', stack=None),
            color=alt.Color('variable', scale=alt.Scale(
                domain=['Successful', 'Failed'], range=['green', 'red']
            )),
            tooltip='value'
        )
        .configure_axis(grid=False)
        .configure_view(strokeOpacity=0)
        .properties(width=600, title='Requests successful vs failed') 
    )

    st.altair_chart(reqSuccessfulFailsPlot, use_container_width=True)

    memUsagePlot = (
        alt.Chart(memoryusage)
        .mark_line()
        .encode(
            x=alt.X('timestamp'),
            y=alt.Y('value', title='MB', stack=None),
            color=alt.Color('variable', scale=alt.Scale(
                domain=['In use', 'Highwater'], range=['green', 'red']
            )),
            strokeDash=alt.condition(alt.datum.variable == 'Highwater', alt.value([5, 1]), alt.value([0])),
            tooltip='value'
        )
        .configure_axis(grid=False)
        .configure_view(strokeOpacity=0) 
        .properties(width=650, height=300, title='Memory usage') 
    )

    st.altair_chart(memUsagePlot, use_container_width=True)

    
    


def plotMajorMinorTD(sdf):

    st.subheader("Load Datasets Events Time Distributions")
    
    sinceSelect = st.selectbox('Recover data since: ', ('Last Daily Report', 'Startup'))
    sinceID = {'Last Daily Report' : 'lastdr' , 'Startup' : 'startup'}
    since = sinceID[sinceSelect]

    # Data
    mld_df = sdf['major_loaddatasets_timedistribution_since_{}'.format(since)]
    n_mld = sdf['n_major_loaddatasets_timedistribution_since_{}'.format(since)]
    n_mld = 0 if n_mld is None else n_mld
    median_mld = sdf['nmedian_major_loaddatasets_timedistribution_since_{}'.format(since)]
    median_mld = 0 if median_mld is None else median_mld

    mild_df = sdf['minor_loaddatasets_timedistribution_since_{}'.format(since)]
    n_mild  = sdf['n_minor_loaddatasets_timedistribution_since_{}'.format(since)]
    n_mild = 0 if n_mild is None else n_mild
    median_mild = sdf['nmedian_minor_loaddatasets_timedistribution_since_{}'.format(since)]
    median_mild = 0 if median_mild is None else median_mild

    tomelt = None
    if (mld_df.empty):
        if (mild_df.empty):
            tomelt = None
        else:
            tomelt = mild_df.rename(columns={'n' : 'Minor'})
    else:
        if (mild_df.empty):
            tomelt = mld_df.rename(columns={'n' : 'Major'})
        else:
            tomelt = mld_df
            tomelt['Minor'] = mild_df['n']
            tomelt = tomelt.rename(columns={'n' : 'Major'})

    #mld_df['Minor'] = mild_df['n']
    #mld_df.rename(columns={'n' : 'Major'}, inplace=True)
    if tomelt is None:
        melt = None
    else:
        melt = tomelt.melt('time_distribution', var_name='type', value_name='value')
        melt = melt.rename(columns={'type' : 'variables'})
        rowOrder = mld_df['time_distribution'].values

    fig = (
        alt.Chart(melt)
        .mark_bar(size=6)
        .encode(
            x=alt.X('value:Q', title='events'),
            row=alt.Row('time_distribution',
                    sort=rowOrder, 
                    spacing=3, center=True,
                    title='Time Distribution', 
                    header=alt.Header(labelAngle=0, labelAlign='left')),
            color='variables',
            y=alt.Y('variables', title=None, axis=alt.Axis(labels=False, ticks=False)),
            tooltip=['variables','value']
        )
        .configure_scale(bandPaddingInner=1)
        .configure_axis(grid=False)
        .configure_view(strokeOpacity=0)
        .properties(width=510, height=12)
    )
    
    st.altair_chart(fig, use_container_width=False)
    st.write('**Major LD**: `total={:,}  median={:,}ms`'.format(n_mld, median_mld) + '<br>' + '**Minor LD**: `total={:,}  median={:,}seconds`'.format(n_mild, median_mild), unsafe_allow_html=True)


def plotResponsesSvsF(sdf):

    st.subheader("Requests Successful vs Failed Time Distributions")

    sinceSelect2 = st.selectbox('Recover data since: ', ('Last Daily Report', 'Last Major Load Datasets',  'Startup'))
    sinceID = {'Last Daily Report' : 'lastdr' , 'Last Major Load Datasets': 'lastmld', 'Startup' : 'startup'}
    since = sinceID[sinceSelect2]

    rf_df = sdf['response_failed_timedistribution_since_{}'.format(since)]
    nrf = sdf['n_response_failed_timedistribution_since_{}'.format(since)]
    nrf = 0 if nrf is None else nrf
    medianrf = sdf['nmedian_response_failed_timedistribution_since_{}'.format(since)]
    medianrf = 0 if medianrf is None else medianrf

    rs_df = sdf['response_succeeded_timedistribution_since_{}'.format(since)]
    nrs = sdf['n_response_succeeded_timedistribution_since_{}'.format(since)]
    nrs = 0 if nrs is None else nrs
    medianrs = sdf['nmedian_response_succeeded_timedistribution_since_{}'.format(since)]
    medianrs = 0 if medianrs is None else medianrs

    tomelt = None
    if (rf_df.empty):
        if (rs_df.empty):
            tomelt = None
        else:
            tomelt = rs_df.rename(columns={'n' : 'Successful'})
    else:
        if (rs_df.empty):
            tomelt = rf_df.rename(columns={'n' : 'Failed'})
        else:
            tomelt = rf_df
            tomelt['Successful'] = rs_df['n']
            tomelt = tomelt.rename(columns={'n' : 'Failed'})

    if tomelt is None:
        melt = None
    else:
        melt = tomelt.melt('time_distribution', var_name='type', value_name='value')
        melt = melt.rename(columns={'type' : 'variables'})
        rowOrder = tomelt['time_distribution'].values

    if (not melt is None or not melt.empty):
        fig = ( 
            alt.Chart(melt)
            .mark_bar(size=6)
            .encode(
                x=alt.X('value:Q', title='requests'),
                row=alt.Row('time_distribution',
                        sort=rowOrder, 
                        spacing=3, center=True,
                        title='Time Distribution', 
                        header=alt.Header(labelAngle=0, labelAlign='left')),
                color='variables',
                y=alt.Y('variables', title=None, axis=alt.Axis(labels=False, ticks=False)),
                tooltip=['variables','value']
            )
            .configure_scale(bandPaddingInner=1)
            .configure_axis(grid=False)
            .configure_view(strokeOpacity=0)
            .properties(width=510, height=12)    
        )

        st.altair_chart(fig, use_container_width=False)
        st.write('**Successful responses**: `total={:,}  median={:,}ms`'.format(nrs, medianrf) + '<br>' + '**Failed responses**: `total={:,}  median={:,}seconds`'.format(nrs, medianrs), unsafe_allow_html=True)

##

def customCSS():
    hide_full_screen = '''
<style>
.element-container button:first-child[title='View fullscreen'] {visibility: hidden;}

</style>
'''
    st.markdown(hide_full_screen, unsafe_allow_html=True)   
    

def titleDashboard():
    st.title("ERDDAP Server Status Dashboard")
    st.write("This is a ERDDAP server status dashboard demostration. We use [Streamlit](https://streamlit.io) for the wep app framework, [Altair](https://altair-viz.github.io) for visualizations and [erddap-python](https://github.com/hmedrano/erddap-python) for data collection.")
    st.write("[ERDDAP](https://coastwatch.pfeg.noaa.gov/erddap/information.html) it's a data distribution server that gives you a simple, consistent way to download subsets of scientific datasets in common file formats and make graphs and maps.")
    st.write("ERDDAP generates a web page (`status.html`) with various statistics of the server status. In this demo we use the [erddap-python](https://github.com/hmedrano/erddap-python) library that parses all this information and return it has scalars and dataframes. With this data we created this simple dashboard to explore the statistics visualy.")
    st.write("If you are a user or admin of a ERDDAP server just change the following URL to your ERDDAP server to get the stats.")


def serverURLWidget():
    _erddapurl = st.text_input("URL of the ERDDAP Server", DEFAULT_ERDDAPURL, help="Change this to get metrics from a different ERDDAP Server")
    _reloadActivated = st.button('Reload', help='Reload the last status data from ERDDAP Server')
    st.write('')
    return _erddapurl, _reloadActivated


def failed2LoadDatasets(sdf):
    nfd = sdf['ndatasetsfailed2load_sincelast_mld']
    fd = sdf['datasetsfailed2load_sincelast_mld']
    st.subheader('The bad.. Some datasets that failed to load.')
    st.write('Number of failed datasets to load since last major load datasets event: `{}`'.format(nfd))
    if nfd > 0:
        st.write('Datasets id\'s: {}'.format(', '.join(['`{}`'.format(d) for d in fd])))
    

def showGenerals(sdf):
    st.subheader("Server numbers")
    st.write("- Server version: `{}` ".format(sdf['version']))
    st.write("- Metrics recovered on: `{}` ".format(sdf['current-time']))
    st.write("- Server started : `{}` ".format(sdf['startup-time']))
    if sdf['version'] >= 2.12:
        st.write("- Unique users since startup : `{}` ".format(sdf['nunique_users_since_startup']))
    st.write("- Total datasets : `{:,}` ".format(sdf['ntotaldatasets']))
    st.write("- Tabledap datasets : `{:,}` ".format(sdf['ntabledatasets']))
    st.write("- Griddap datasets : `{:,}` ".format(sdf['ngriddatasets']))
    st.write("- Memory in use : `{:,} MB`".format(sdf['memoryinuse']))
    st.write("- Memory high water mark : `{:,} MB`".format(sdf['highwatermark']))
    st.write("- Memory XMX : `{:,} MB`".format(sdf['xmx']))
    

def showCredits():
    st.write('----')
    st.write('Review the source code [here](https://github.com/hmedrano/erddap-status-dashboard)')
    st.write('*By Favio Medrano*')




#
# MAIN
try:

    customCSS()
    titleDashboard()

    erddapurl, reloadActivated = serverURLWidget()
    with st.spinner('Loading metrics..'):
        sdf = getStatusData(gremote, erddapurl, force=reloadActivated)

    showGenerals(sdf)
    plotMLDTimeseries(sdf)
    plotResponsesSvsF(sdf)
    plotMajorMinorTD(sdf)
    failed2LoadDatasets(sdf)
    showCredits()
    

except Exception as e:
    st.error(
        """
        An error occurred :( :  %s
        """ 
        % str(e)
    )
