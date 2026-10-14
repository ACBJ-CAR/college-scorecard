from functools import partial

import polars as pl
import streamlit as st

st.set_page_config(
    page_title="College debt",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="collapsed",
)


@st.cache_data
def load_data(path: str) -> pl.DataFrame:
    return pl.read_parquet(path)


df = load_data("./data/dash_data.parquet")

if "worst_toggle" not in st.session_state:
    st.session_state.worst_toggle = False


with (
    st.container(horizontal=True, horizontal_alignment="center"),
    st.container(width=800),
):
    st.title(
        f"{'Worst' if st.session_state.worst_toggle else 'Best'} bang-for-your-buck college degrees",
        width="content",
    )
    worst = st.toggle(
        f"Switch to {'**worst**' if not st.session_state.worst_toggle else '**best**'} bang-for-your-buck view",
        key="worst_toggle",
        on_change=st.rerun,
    )
    st.markdown(
        f"This data is ranked by `debt-to-income ratio` in {'descending' if st.session_state.worst_toggle else 'ascending'} order to show which school's degree programs land graduates in the {'**worst**' if st.session_state.worst_toggle else '**best**'} financial position. `Debt-to-income ratio` is calculated as the ratio of median debt from federal student loans at graduation to median earnings four years after graduation.",
        width="content",
    )
    st.markdown(
        "This analysis is inspired by and uses the same dataset as [Wall Street Journal's 2021 article on Master's degree graduates ending up in deep student loan debt](https://www.wsj.com/us-news/education/financially-hobbled-for-life-the-elite-masters-degrees-that-dont-pay-off-11625752773?mod=article_inline)."
    )

with st.container(horizontal=True, horizontal_alignment="center"):
    with st.container(border=True):
        selected_states = st.multiselect(
            "Filter by state",
            options=sorted(df["state"].drop_nulls().unique().to_list()),
        )

        df = df.filter(pl.col("state").is_in(selected_states or pl.col("state")))

        selected_counties = st.multiselect(
            "Filter by county",
            options=sorted(df["county"].drop_nulls().unique().to_list()),
        )

    with st.container():
        with st.container(border=True):
            selected_institutions = st.multiselect(
                "Filter by institution",
                options=sorted(df["institution"].unique().to_list()),
            )
        st.caption(
            "Data points representing small samples are suppressed for privacy in the original dataset, and are marked as such."
        )

        df = df.filter(
            pl.col("institution").is_in(selected_institutions or pl.col("institution"))
        )

    with st.container(border=True):
        selected_degree_levels = st.multiselect(
            "Filter by degree level",
            options=[
                "Associate's",
                "Bachelor's",
                "Doctoral",
                "First professional degree",
                "Graduate/professional certificate",
                "Master's",
                "Post-baccalaureate certificate",
                "Ugrd. certificate/diploma",
            ],
            default=["Bachelor's", "Master's", "Doctoral"],
        )

        df = df.filter(
            pl.col("degree_level").is_in(
                selected_degree_levels or pl.col("degree_level")
            )
        )

        selected_fields = st.multiselect(
            "Filter by field of study",
            options=sorted(df["field"].drop_nulls().unique().to_list()),
        )


df = (
    df.filter(
        # pl.col("institution").is_in(selected_institutions or pl.col("institution")),
        pl.col("county").is_in(selected_counties or pl.col("county")),
        # pl.col("degree_level").is_in(selected_degree_levels or pl.col("degree_level")),
        pl.col("field").is_in(selected_fields or pl.col("field")),
    )
    .with_columns(
        rank=pl.col("debt_to_income_ratio").rank(
            descending=st.session_state.worst_toggle, method="min"
        )
    )
    .sort("rank", nulls_last=True)
)

dollar_config = partial(st.column_config.NumberColumn, format="dollar")
percent_config = partial(st.column_config.NumberColumn, format="%.2f%%")

column_config = {
    "rank": st.column_config.TextColumn(label="Rank", width=5, alignment="center"),
    "institution": st.column_config.TextColumn(label="College", width=100),
    "field": st.column_config.TextColumn(label="Field of study", width="medium"),
    "degree_level": st.column_config.TextColumn(label="Degree level", width=100),
    "debt_at_graduation": dollar_config(
        label="Median debt from federal student loans at graduation"
    ),
    "earnings_4_years_after_graduation": dollar_config(
        label="Median earnings 4 years after graduation"
    ),
    "debt_to_income_ratio": percent_config(label="Debt-to-income ratio"),
    "loan_burden_percentage": percent_config(label="Loan burden %"),
}

st.dataframe(
    df,
    column_config=column_config,
    column_order=column_config.keys(),
    row_height=70,
    placeholder="Suppressed",
)

st.caption(
    "Debt and earnings data represents a two-year cohort of graduates, completing their studies during academic years 2017-2018 and 2018-2019. Only graduates not enrolled at any institution 4 years after graduation are included in earnings data."
)

with st.container(horizontal=True):
    st.space("stretch")
    st.markdown(
        "**SOURCE:** [National Student Loan Data System, U.S. Department of Education/IRS Tax Records, U.S. Department of Treasury (via U.S Department of Education)](https://collegescorecard.ed.gov/data/)",
        text_alignment="right",
    )
