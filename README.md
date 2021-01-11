## GreenbyteAnalysisSDK is a wrapper geared for data analysis around the Greenbyte API

GreenbyteSDK simplifies working with Greenbyte API

Features include caching api results to minimize network overhead and native support for Pandas dataframes

```
# Initialize SDK with a client specific url and api authorization token
gb = GreenbyteSDK(client_url, auth_token)

# Get a list of sites available
gb.sites()

# Return a list of Pandas DataFrames showing the energy exported from a site in the past week 
gb.sites('Backen').devices().signals('Energy Export')

# Because the new data for Backend was already cached the SDK only calls for the new Berget data
gb.sites(['Backen', 'Berget']).devices().signals('Energy Export')

# Drill into specific deviecs and signals
gb.sites('Berget').devices([1, 3]).signals(['Energy Export', 'Lost Production'])

```
