from setuptools import setup, find_packages

version = '0.1'

setup(name='ztest',
      version=version,
      description="ztest tool",
      classifiers=[],
      keywords='ztest',
      author='zstacker',
      author_email='support@zstack.io',
      url='http://zstack.io',
      license='private',
      packages=find_packages('src'),
      package_dir={'': 'src'},
      include_package_data=True,
      zip_safe=True,
      install_requires=[
          "simplejson==3.17.2",
          "typing==3.7.4.3",
          "docker==4.4.1",
          "mock==3.0.5",
          "setuptools==44.1.1",
          "Jinja2==2.11.3",
      ],
      entry_points={
          'console_scripts': [
              'zguest = ztest.guest.main:main',
              'ztest = ztest.host.main:main'
          ]
      }
      )
