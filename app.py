from datetime import datetime, timezone
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

@st.cache_data
def load_data():
    df = pd.read_csv("https://www.dropbox.com/scl/fi/vsxwzit131pa4f71dgzkx/repository_data.csv?rlkey=egyy0zy0oepvak8fr1vijrplt&dl=1")
    df["primary_language"] = df["primary_language"].fillna("Plain Text")
    df["licence"] = df["licence"].fillna("None")
    df["year"] = pd.to_datetime(df["created_at"]).dt.year
    df = df.sort_values(by=["year"])
    return df

@st.cache_data(max_entries = 1)
def load_language_chart(languages):
    languageDF = None
    if len(languages) > 0:
        for i, language in enumerate(languages):
            df1 = df[df["primary_language"] == language].reset_index()
            df1[language] = df1.groupby("primary_language").cumcount()
            right = df1.loc[df1.groupby("year")[language].max()]
            right = right[["year", language]]
            if i == 0:
                languageDF = right
            else:
                languageDF = pd.merge(languageDF, right, how = "right", on="year")
        right = None
        df1 = None
    return languageDF

# @st.cache_data(max_entries = 1)
# def load_licence_chart(licences):
#     licenceDF = None
#     if len(licences) > 0:
#         for i, licence in enumerate(licences):
#             df1 = df[df["licence"] == licence].reset_index()
#             df1[licence] = df1.groupby("licence").cumcount()
#             right = df1.loc[df1.groupby("year")[licence].max()]
#             right = right[["year", licence]]
#             if i == 0:
#                 licenceDF = right
#             else:
#                 licenceDF = pd.merge(licenceDF, right, how = "right", on="year")
#         df1 = None
#         right = None

#     return licenceDF

@st.cache_data(max_entries = 1)
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
    ds = None
    indices = None
    values = None
    temp = None
    other_languages = None
    return languages, matrix

@st.cache_data(max_entries = 1)
def fork_to_pull_ratio(languages):
    dt = df[df["primary_language"].isin(languages)]
    fp = dt.groupby('primary_language')['forks_count'].sum().to_frame()
    fr = dt.groupby('primary_language')['watchers'].sum().to_frame()
    ds = fp.merge(fr, how = 'inner', on='primary_language')
    ds.reset_index(inplace=True)
    dt, fp, fr = None, None, None
    return ds

@st.cache_data(max_entries = 1)
def commits_to_watchers_ratio(limit):
    dt = df.sort_values(by="stars_count", ascending = False)

    if limit >= 21:
        dt = dt.head(limit + 1)
        dt = dt[dt["name"] != "linux"]
    else:
        dt = dt.head(limit)
    return dt


st.set_page_config(page_title = "Data Dashboard", layout = "wide")
df = load_data()

st.write("**Languages Used Over Time**")
languages = ["JavaScript", "Python", "Java", "C++", "PHP"]

languageDF = load_language_chart(languages)
if languageDF is not None:
    st.area_chart(languageDF, x="year", y=languages)
    languageDF = None


# col2.write("**Licences Being Used Over Time**")
# licences = ["MIT License", "None", "Apache License 2.0", "GNU General Public License v3.0"]

# licenceDF = load_licence_chart(licences)
# if licenceDF is not None:
#     col2.area_chart(licenceDF, x="year", y=licences)

st.write("**Most Frequent Pairings of Major Languages**")

number = 5
caption = f'Showing the {number} most common languages' 
st.write(caption)
languages, z = load_commonly_combined(number)
if languages is not None and z is not None:
    fig = px.imshow(z, labels = dict(x = "Language", y = "Language", color = "Occurrences"), x=languages, y = languages, text_auto=True)
    st.plotly_chart(fig, theme="streamlit", use_container_width=True)
    fig = None

st.write("**Ratio of Forks to Watchers by Language**")
languages = ["JavaScript", "Python", "Plain Text", "Java", "C++", "PHP", "TypeScript", "C", "C#", "Go", "HTML", "Shell", "Jupyter Notebook", "Ruby", "CSS", "Objective-C"]

ratioDF = fork_to_pull_ratio(languages)
if ratioDF is not None:
    st.scatter_chart(ratioDF, x = "forks_count", y = "watchers", color = "primary_language")
    ratioDF = None

st.write("**Relationship Between Commits and Pull Requests by Repository**")
number2 = 10
caption2 = f"Showing the {number2} most common repositories"
st.write(caption2)
cToW = commits_to_watchers_ratio(number2)
st.scatter_chart(cToW, x = "pull_requests", y = "commit_count", color = "name")
cToW = None