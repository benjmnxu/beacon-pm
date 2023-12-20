from datetime import datetime, timezone
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

@st.cache_data
def load_data():
    df = pd.read_csv("archive/repository_data.csv")
    df["primary_language"] = df["primary_language"].fillna("Plain Text")
    df["licence"] = df["licence"].fillna("None")
    df["year"] = pd.to_datetime(df["created_at"]).dt.year
    df = df.sort_values(by=["year"])
    return df

@st.cache_data
def load_language_chart(languages):
    languageDF = None
    for i, language in enumerate(languages):
        df1 = df[df["primary_language"] == language].reset_index()
        df1[language] = df1.groupby("primary_language").cumcount()
        right = df1.loc[df1.groupby("year")[language].max()]
        right = right[["year", language]]
        if i == 0:
            languageDF = right
        else:
            languageDF = pd.merge(languageDF, right, how = "right", on="year")

    return languageDF

@st.cache_data
def load_licence_chart(licences):
    licenceDF = None
    for i, licence in enumerate(licences):
        df1 = df[df["licence"] == licence].reset_index()
        df1[licence] = df1.groupby("licence").cumcount()
        right = df1.loc[df1.groupby("year")[licence].max()]
        right = right[["year", licence]]
        if i == 0:
            licenceDF = right
        else:
            licenceDF = pd.merge(licenceDF, right, how = "right", on="year")

    return licenceDF

@st.cache_data
def load_commonly_combined(limit):
    if limit == 0:
        return None, None
    matrix = []
    ds = df.groupby('languages_used').size()
    indices = ds.index
    values = ds.values
    languages = df["primary_language"].value_counts().nlargest(limit + 1).index.to_numpy()
    if (languages.size > 2):
        languages = np.delete(languages, 2)
    for language in languages:
        temp = [0] * len(languages)
        for index, value in zip(indices, values):
            if (len(index) > 1):
                if language in index:
                    other_languages = languages[np.arange(len(languages))!=language]
                    for lan in other_languages:
                        if lan in index:
                            temp[np.where(languages==lan)[0][0]] += value
        matrix.append(temp)
    return languages, matrix

@st.cache_data
def fork_to_pull_ratio(languages):
    dt = df[df["primary_language"].isin(languages)]
    fp = dt.groupby('primary_language')['forks_count'].sum().to_frame()
    fr = dt.groupby('primary_language')['watchers'].sum().to_frame()
    ds = fp.merge(fr, how = 'inner', on='primary_language')
    ds.reset_index(inplace=True)
    return ds

@st.cache_data
def commits_to_watchers_ratio(limit):
    dt = df.sort_values(by="stars_count", ascending = False)

    if limit >= 21:
        dt = dt.head(limit + 1)
        dt = dt[dt["name"] != "linux"]
    else:
        dt = dt.head(limit)
    return dt


st.set_page_config(page_title = "Data Dashboard", layout = "wide")
col1, col2 = st.columns(2)
df = load_data()

col1.write("**Languages Used Over Time**")
#languages = col1.multiselect("Primary language", options = df["primary_language"].unique(), default = ["JavaScript", "Python", "Java", "C++", "PHP"])

languageDF = load_language_chart(["JavaScript", "Python", "Java", "C++", "PHP"])
if languageDF is not None:
    col1.area_chart(languageDF, x="year", y=["JavaScript", "Python", "Java", "C++", "PHP"])


col2.write("**Licences Being Used Over Time**")
# licences = col2.multiselect("Type of Licence", options = df["licence"].unique(), default = ["MIT License", "None", "Apache License 2.0", "GNU General Public License v3.0"])

licenceDF = load_licence_chart(["MIT License", "None", "Apache License 2.0", "GNU General Public License v3.0"])
if licenceDF is not None:
    col2.area_chart(licenceDF, x="year", y=["MIT License", "None", "Apache License 2.0", "GNU General Public License v3.0"])

st.write("**Most Frequent Pairings of Major Languages**")

# number = int(st.number_input("Insert a number", format = "%d", min_value = 2, value=5, placeholder="Type a number..."))
st.write('Showing the ', 5, ' most common languages' )
languages, z = load_commonly_combined(5)
if languages is not None and z is not None:
    fig = px.imshow(z, labels = dict(x = "Language", y = "Language", color = "Occurrences"), x=languages, y = languages, text_auto=True)
    st.plotly_chart(fig, theme="streamlit", use_container_width=True)

st.write("**Ratio of Forks to Watchers by Language**")
# languages = st.multiselect("Metric", options = df["primary_language"].unique(), default = ["JavaScript", "Python", "Plain Text", "Java", "C++", "PHP", "TypeScript", "C", "C#", "Go", "HTML", "Shell", "Jupyter Notebook", "Ruby", "CSS", "Objective-C"])

ratioDF = fork_to_pull_ratio(["JavaScript", "Python", "Plain Text", "Java", "C++", "PHP", "TypeScript", "C", "C#", "Go", "HTML", "Shell", "Jupyter Notebook", "Ruby", "CSS", "Objective-C"])
if ratioDF is not None:
    st.scatter_chart(ratioDF, x = "forks_count", y = "watchers", color = "primary_language")

st.write("**Relationship Between Commits and Pull Requests by Repository**")
# number2 = int(st.number_input("Insert a number", format = "%d", min_value = 1, value=10, placeholder="Type a number..."))
st.write('Showing the ', 10, " most common repositories. (The repository 'linux' has been filtered out as a discovered outlier)" )
cToW = commits_to_watchers_ratio(10)
st.scatter_chart(cToW, x = "pull_requests", y = "commit_count", color = "name")