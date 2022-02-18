from setuptools import setup

setup(
    name='meraki-apiv0-audit',
    version='0.1.0',
    py_modules=['meraki-apiv0-audit'],
    install_requires=[
          'meraki',
          'click',
          'tqdm'
      ],
    entry_points='''
        [console_scripts]
        v0audit=v0audit:audit
    ''',
)
