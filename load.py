import marimo

__generated_with = "0.25.1"
app = marimo.App(width="medium")


@app.cell
def _():
    import polars as pl
    from pathlib import Path
    import us

    return Path, pl, us


@app.cell
def _(Path):
    data_folder = Path("./data/")
    field_of_study_csv = data_folder / "Most-Recent-Cohorts-Field-of-Study.csv"
    field_of_study_1718_1819_path = data_folder / "FieldOfStudyData1718_1819_PP.csv"
    field_of_study_2122_2223_path = data_folder / "FieldOfStudyData2122_2223_PP.csv"
    college_locations_path = data_folder / "college_location.csv"
    return (
        college_locations_path,
        data_folder,
        field_of_study_1718_1819_path,
        field_of_study_2122_2223_path,
    )


@app.cell
def _(
    college_locations_path,
    field_of_study_1718_1819_path,
    field_of_study_2122_2223_path,
    pl,
):
    field_of_study_1718_1819 = pl.read_csv(field_of_study_1718_1819_path, null_values=["NA", "PS"])
    field_of_study_2122_2223 = pl.read_csv(field_of_study_2122_2223_path, null_values=["NA", "PS"])
    college_locations = pl.read_csv(college_locations_path)
    return (
        college_locations,
        field_of_study_1718_1819,
        field_of_study_2122_2223,
    )


@app.cell
def _(
    college_locations,
    field_of_study_1718_1819,
    field_of_study_2122_2223,
    pl,
    us,
):
    degree_map = {
        "Undergraduate Certificate or Diploma": "Ugrd. certificate/diploma",
        "Bachelor's Degree": "Bachelor's",
        "Associate's Degree": "Associate's",
        "Master's Degree": "Master's",
        "Doctoral Degree": "Doctoral",
        "Post-baccalaureate Certificate": "Post-baccalaureate certificate",
        "First Professional Degree": "First professional degree",
        "Graduate/Professional Certificate": "Graduate/professional certificate",
        "Non-Credential Program (Preparatory Coursework/Teacher Certification)": "Non-credential program",
    }

    state_name_map = {state.abbr: state.name for state in us.STATES} | {
        "DC": "District of Columbia",
        "AS": "American Samoa",
        "GU": "Guam",
        "PR": "Puerto Rico",
        "PW": "Palau",
        "FM": "Micronesia",
        "MH": "Marshall Islands",
        "VI": "Virgin Islands, U.S.",
        "MP": "Northern Mariana Islands",
    }

    (
        field_of_study_1718_1819.select(
            unitid=pl.col("UNITID"),
            cipcode=pl.col("CIPCODE"),
            cred_level_code=pl.col("CREDLEV"),
            institution=pl.col("INSTNM"),
            field=pl.col("CIPDESC").str.strip_chars("."),
            degree_level=pl.col("CREDDESC").replace_strict(degree_map),
            degree_level_raw=pl.col("CREDDESC"),
            debt_at_graduation=pl.col("DEBT_ALL_STGP_EVAL_MDN"),
            graduates_with_loans=pl.col("DEBT_ALL_STGP_EVAL_N"),
        )
        .join(
            field_of_study_2122_2223.select(
                unitid=pl.col("UNITID"),
                cipcode=pl.col("CIPCODE"),
                cred_level_code=pl.col("CREDLEV"),
                earnings_4_years_after_graduation=pl.col("EARN_MDN_4YR"),
                graduates_not_in_school_4_years_after_graduation=pl.col(
                    "EARN_COUNT_WNE_4YR"
                ),
            ),
            on=["unitid", "cipcode", "cred_level_code"],
            validate="1:1",
        )
        .join(
            college_locations.select(
                unitid=pl.col("UNITID"),
                state=pl.col("STABBR").replace_strict(state_name_map),
                # state_code=pl.col("STABBR"),
                county=pl.col("COUNTYNM"),
                # county_fips=pl.col("COUNTYCD"),
            ).with_columns(
                county=pl.format("{}, {}", pl.col("county"), pl.col("state"))
            ),
            on="unitid",
            validate="m:1",
        )
        .unique()
        .with_columns(
            debt_to_income_ratio=100
            * pl.col("debt_at_graduation")
            / pl.col("earnings_4_years_after_graduation"),
        )
        .sort("debt_to_income_ratio", descending=True, nulls_last=True)
        # .write_parquet(data_folder / "dash_data.parquet")
    )
    return


@app.cell
def _(data_folder, pl):
    field_of_study_2223 = pl.read_csv(data_folder / "FieldOfStudyData2122_2223_PP.csv",  null_values=["NA", "PS"], infer_schema_length=10_000)
    return (field_of_study_2223,)


@app.cell
def _(field_of_study_2223, pl):
    field_of_study_2223.select(
        college=pl.col("INSTNM"),
        field=pl.col("CIPDESC"),
        degree_level=pl.col("CREDDESC"),
        debt_at_graduation=pl.col("DEBT_ALL_STGP_EVAL_MDN"),
        median_monthly_payment=pl.col("DEBT_ALL_STGP_ANY_MDN10YRPAY"),
        earnings_2_years_after_graduation_highest_degree=pl.col("EARN_MDN_HI_2YR"),
        earnings_1_years_after_graduation=pl.col("EARN_MDN_1YR"),
        earnings_5_years_after_graduation=pl.col("EARN_MDN_5YR"),

    ).unique()


    # .with_columns(
    #     debt_to_income_ratio=pl.col("debt_at_graduation")
    #     / pl.col("earnings_2_years_after_graduation_highest_degree"),
    #     loan_burden_percentage=pl.col("median_monthly_payment")
    #     * 12
    #     / pl.col("earnings_2_years_after_graduation_highest_degree"),
    # ).with_columns(
    #     rank=pl.col("debt_to_income_ratio").rank(descending=False, method="min"),
    # ).sort("rank").filter(pl.col("degree_level") == "Master's Degree")
    return


@app.cell
def _(field_of_study_2223):
    field_of_study_2223[[s.name for s in field_of_study_2223 if not (s.null_count() == field_of_study_2223.height)]]
    return


@app.cell
def _(field_of_study, field_of_study_2223):
    field_of_study[[s.name for s in field_of_study_2223 if not (s.null_count() == field_of_study_2223.height)]]
    return


@app.cell
def _():
    return


if __name__ == "__main__":
    app.run()
