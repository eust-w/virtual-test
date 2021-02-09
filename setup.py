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
      ],
      entry_points={
          'console_scripts': [
              'zguest = ztest.guest.main:main',
              'ztest = ztest.host.main:main'
          ]
      }
)
