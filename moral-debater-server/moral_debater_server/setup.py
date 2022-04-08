from setuptools import setup

setup(
    name='Moral Debater API',
    version='1.0',
    packages=['moral_debater_api'],
    include_package_data=True,
    zip_safe=False,
    install_requires=['Flask', 'waitress', 'importlib_resources', 'Flask-Caching', 'typing_extensions', 'configparser'],
    package_data={'': ['static/*', 'templates/*']}
)