import pandas as pd
df = pd.read_csv('gazedataeye.csv')
df = df.drop(columns=['fixation_duration'])
df.to_csv('gazedataeye.csv', index=False)
