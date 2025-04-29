from setuptools import setup, find_packages

setup(
    name="bet365-ml",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "fastapi>=0.109.2",
        "pydantic>=2.6.1",
        "pydantic-settings>=2.2.1",
        "httpx>=0.26.0",
        "python-dotenv>=1.0.1",
        "kafka-python>=2.0.2",
        "aiokafka>=0.10.0",
        "sqlalchemy>=2.0.27",
    ],
    extras_require={
        "dev": [
            "pytest>=8.0.0",
            "pytest-asyncio>=0.23.5",
            "pytest-cov>=4.1.0",
        ],
    },
) 