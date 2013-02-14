<%inherit file="layout.py"/>
from weboob.tools.backend import BaseBackend

from .browser import ${r.classname}Browser


__all__ = ['${r.classname}Backend']


class ${r.classname}Backend(BaseBackend):
    NAME = '${r.name}'
    DESCRIPTION = u'${r.name} website'
    MAINTAINER = u'${r.author}'
    EMAIL = '${r.email}'
    VERSION = '${r.version}'

    BROWSER = ${r.classname}Browser
