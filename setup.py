from setuptools import setup, find_packages

setup(
    name="gpt_oss_mcp_server",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "fastmcp",
        "selenium",
        "webdriver-manager",
        "fastapi",
        "uvicorn",
        "pydantic",
        "httpx",
        "aiofiles",
        "python-multipart"
    ],
)