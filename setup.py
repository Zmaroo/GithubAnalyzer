from setuptools import setup, find_packages

setup(
    name="GithubAnalyzer",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        'psycopg2-binary',
        'neo4j',
        'python-dotenv',
        'sentence-transformers>=3.3.1',
        'tree-sitter',
        'rich',
        'click',
        'networkx>=3.4.2',
        'matplotlib',
        'numpy>=2.2.0',
        'PyYAML>=6.0.1',
        'jenkinsapi>=0.3.13',
        'jproperties>=2.1.1',
        'javaproperties>=0.8.0',
        'torch>=2.5.1',
        'transformers>=4.47.1',
        'scikit-learn>=1.6.0'
    ]
) 