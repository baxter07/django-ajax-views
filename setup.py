from setuptools import setup, find_packages
from ajaxviews import __version__
from codecs import open
from os import path


root_path = path.abspath(path.dirname(__file__))

with open(path.join(root_path, 'README.rst'), encoding='utf-8') as f:
    long_description = f.read()

version_str = '.'.join(str(n) for n in __version__)


setup(
    name='django-ajax-views',
    version=version_str,
    description='Django class-based views extension working together with JS library require-ajax-views.',
    long_description=long_description,
    url='https://github.com/Pyco7/django-ajax-views',
    author='Emanuel Hafner',
    author_email='dev@hafner.me',
    license='MIT',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Web Environment',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        # 'Programming Language :: Python :: 2',
        # 'Programming Language :: Python :: 2.6',
        # 'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        # 'Programming Language :: Python :: 3.3',
        # 'Programming Language :: Python :: 3.4',
        # 'Programming Language :: Python :: 3.5',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
    keywords='django class-based views javascript coffeescript typescript ajax requirejs',
    packages=find_packages(),
    package_data={
        'ajaxviews': [
            'templates/ajaxviews/*.html',
            'static/require-ajax-views/dist/ajaxviews.js',
        ],
    },
    install_requires=[
        'Django>=1.9',
        'django-require',
        'django-guardian',
        'django-crispy-forms',
        'django-extra-views',
        'django-js-reverse',
        'django-jsonify',
        'django-autocomplete-light==2.3.3',
    ],
    # extras_require={
    #     'dev': ['django-require'],
    #     'test': ['coverage'],
    # },
)
