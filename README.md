## GreenbyteAnalysisSDK is a wrapper geared for data analysis around the Greenbyte API

GreenbyteSDK simplifies working with Greenbyte API. Features include caching api results to minimize network overhead and native support for Pandas dataframes

```
# Initialize SDK with a client specific url and api authorization token
gb = GreenbyteSDK(client_url, auth_token)

# Return a list of Pandas DataFrames showing the energy exported from a site in the past week 
energy_export = gb.sites('Backen').devices().signals('Energy Export')

# Because the new data for Backend was already cached the SDK only calls for the new Berget data
energy_export = gb.sites('Backen', 'Berget).devices().signals('Energy Export')

```
