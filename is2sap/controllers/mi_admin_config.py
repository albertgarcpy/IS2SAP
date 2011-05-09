# -*- coding: utf-8 -*-
"""Main Controller"""

from tg import expose, flash, require, url, request, redirect
from pylons.i18n import ugettext as _, lazy_ugettext as l_
from tgext.admin.tgadminconfig import TGAdminConfig
from tgext.admin.controller import AdminController, AdminConfig
from repoze.what import predicates

from is2sap.lib.base import BaseController
from is2sap.model import DBSession, metadata, Usuario
from is2sap import model
from is2sap.controllers.secure import SecureController
from is2sap.controllers.error import ErrorController

from tg import tmpl_context, validate
from is2sap.widgets.usuario_form import crear_usuario_form
from webhelpers import paginate
from repoze.what.predicates import has_permission
from tg import config

from is2sap.controllers.usuario_controller import *


__all__ = ['MiAdminConfig']

class MiAdminConfig(AdminConfig):

    allow_only = has_permission('administracion',
                                msg=l_('Only for people with the "administrador" permission'))
    default_index_template = "genshi:is2sap.templates.admin_principal"
