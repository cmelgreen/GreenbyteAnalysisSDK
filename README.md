## GreenbyteAnalysisSDK: seamless data analysis with the Greenbyte API
Note: This sdk is not affiliated with Greenbyte. It was written purely for personal convenience when using the official API and is provided as-is
Learn more about the Greenbyte API at https://developer.greenbyte.com/

### Simplify working with Greenbyte API by providing a wrapper gearded towards data anaylsis

Features include caching api results to minimize network overhead and native support for Pandas dataframes.

```python
# Initialize SDK with a client specific url and api authorization token
gb = GreenbyteSDK(client_url, auth_token)

# Get a list of sites available
gb.sites()

# Return a list of Pandas DataFrames showing the energy exported from a site in the past week 
gb.sites('Backen').devices().signals('Energy Export')

# Because the data for the Backen site was already cached the SDK only calls for the new Berget data but returns results for both
gb.sites(['Backen', 'Berget']).devices().signals('Energy Export')

# Drill into specific deviecs and signals
gb.sites('Berget').devices([1, 3]).signals(['Energy Export', 'Lost Production'])

```
