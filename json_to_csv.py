# create a dataframe from the combined json and output to a csv
# %%
import pandas as pd

df = pd.read_json('output/combined.json')
