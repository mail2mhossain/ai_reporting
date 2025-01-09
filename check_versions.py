import sys
from importlib.metadata import version, PackageNotFoundError

# List of package names you want to check
package_names = [
    "python-decouple",
    "numpy",
    "pandas",
    "matplotlib",
    "plotly",
    "seaborn",
    "langchain",
    "langgraph",
    "langchain_openai",
    "langchain_community",
    "langchain-experimental",
    "streamlit",
    "sqlalchemy",
    "tabulate",
    "duckdb",
    "psycopg2",
]

# Print the Python version
print("Python Version:", sys.version)

# Print the version of each package in the list
for package_name in package_names:
    try:
        package_version = version(package_name)
        print(f"{package_name} Version: {package_version}")
    except PackageNotFoundError:
        print(f"{package_name} is not installed")
