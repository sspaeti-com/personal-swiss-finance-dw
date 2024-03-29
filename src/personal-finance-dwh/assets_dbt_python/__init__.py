import os

from dagster import (
    Definitions,
    FilesystemIOManager,
    ScheduleDefinition,
    define_asset_job,
    load_assets_from_package_module,
)
from dagster._utils import file_relative_path
from dagster_dbt import DbtCliClientResource, load_assets_from_dbt_project
from dagster_duckdb_pandas import DuckDBPandasIOManager

from assets_dbt_python.assets import bekb_transactions

DBT_PROJECT_DIR = file_relative_path(__file__, "../dbt_project")
DBT_PROFILES_DIR = file_relative_path(__file__, "../dbt_project/config")

# all assets live in the default dbt_schema
dbt_assets = load_assets_from_dbt_project(
    DBT_PROJECT_DIR,
    DBT_PROFILES_DIR,
    # prefix the output assets based on the database they live in plus the name of the schema
    key_prefix=["duckdb", "dbt_schema"],
    # prefix the source assets based on just the database
    # (dagster populates the source schema information automatically)
    source_key_prefix=["duckdb"],
)


## BEKB
raw_data_assets = load_assets_from_package_module(
    bekb_transactions,
    group_name="raw_data",
    key_prefix=["duckdb", "raw_data"],
)


# define jobs as selections over the larger graph
everything_job = define_asset_job("everything_everywhere_job", selection="*")

resources = {
    # this io_manager allows us to load dbt models as pandas dataframes
    "io_manager": DuckDBPandasIOManager(
        database=os.path.join(
            DBT_PROJECT_DIR,
            "/Users/sspaeti/Simon/Sync/1 Areas/Finance/Bank/Kontoauszüge/_analytics/personal-finance.duckdb",)),
    # this io_manager is responsible for storing/loading our pickled machine learning model
    "model_io_manager": FilesystemIOManager(),
    # this resource is used to execute dbt cli commands
    "dbt": DbtCliClientResource(
        project_dir=DBT_PROJECT_DIR, profiles_dir=DBT_PROFILES_DIR
    ),
}

defs = Definitions(
    assets=[*dbt_assets, *raw_data_assets],
    resources=resources,
    schedules=[
        ScheduleDefinition(job=everything_job, cron_schedule="@weekly"),
    ],
)
