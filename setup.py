from setuptools import setup, find_packages

setup(
    name="hrdk-law-core",
    version="1.0.0",
    description="HRDK 법령 모니터링 공유 코어 라이브러리",
    packages=find_packages(),
    python_requires=">=3.11",
    install_requires=[
        "requests>=2.31.0",
        "urllib3>=2.0.0",
        "gspread>=5.12.0",
        "oauth2client>=4.1.3",
        "openpyxl>=3.1.2",
        "pandas>=2.0.0",
    ],
)
